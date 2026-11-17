"""A LiveKit Agents voice agent on LiveKit Inference, with a Simli Trinity-2 avatar.

Run `uv run agent.py dev`, then talk to it from the web page in frontend/. See README.md.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    CloseEvent,
    CloseReason,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
)
from livekit.plugins import simli

load_dotenv()

logger = logging.getLogger("simli-agent")

# --- Make it yours: everything you'd usually change is here. ------------------------------------

# Simli's default Trinity-2 face, a woman, so the default voice below is a female one. Use any
# Trinity-2 face ID (https://docs.simli.com/api-reference/preset-faces), or set SIMLI_FACE_ID in
# .env, and match the voice to it.
FACE_ID = os.getenv("SIMLI_FACE_ID") or "14c60d62-6ebf-424d-b626-1f4f91c33b04"

NAME = "Ava"

INSTRUCTIONS = (
    f"You are {NAME}, a friendly voice assistant whom the user sees as a video avatar. "
    "Speak English unless the user speaks another language. "
    "Keep your replies short and conversational: one to three sentences. "
    "Don't use emojis, lists, markdown or other formatting: everything you write is spoken."
)

# What the avatar says first, as soon as it's in the room. It's spoken word for word, so the
# user hears it without waiting for the LLM.
FIRST_MESSAGE = f"Hi, I'm {NAME}. What would you like to talk about?"

# Models, all through LiveKit Inference: your LiveKit project's credentials pay for them, so
# there are no OpenAI, Deepgram or Inworld keys. Other model IDs and prices:
# https://docs.livekit.io/agents/models/ and https://livekit.com/pricing/inference
STT_MODEL = "deepgram/nova-3"  # speech to text, streaming
STT_LANGUAGE = "en"
LLM_MODEL = "google/gemma-4-31b-it"  # LiveKit's recommended default, served by LiveKit
TTS_MODEL = "inworld/inworld-tts-2"  # text to speech

# Voices for TTS_MODEL (https://docs.livekit.io/agents/models/tts/). Match the voice to the face.
FEMALE_VOICE = "Ashley"  # warm, natural American female
MALE_VOICE = "Edward"  # fast-talking, emphatic American male
VOICE = FEMALE_VOICE

# Simli session limits, in seconds. The avatar leaves after MAX_SESSION_LENGTH, or after
# MAX_IDLE_TIME without speaking, and the conversation ends with it.
MAX_SESSION_LENGTH = 600
MAX_IDLE_TIME = 300  # the plugin's own default is only 30

# ------------------------------------------------------------------------------------------------

# The agent only joins rooms that dispatch it by this name, as the frontend's token does.
# Without a name, LiveKit would send it to every new room in the project.
AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME") or "simli-agent"


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession(
        stt=inference.STT(model=STT_MODEL, language=STT_LANGUAGE),
        llm=inference.LLM(model=LLM_MODEL),
        tts=inference.TTS(model=TTS_MODEL, voice=VOICE),
        turn_handling=TurnHandlingOptions(
            # LiveKit's turn detector decides when the user has finished speaking, from what
            # they said and how they said it. The session adds the voice activity detector it
            # needs. https://docs.livekit.io/agents/build/turns/
            turn_detection=inference.TurnDetector(),
            # The avatar can't pause its speech, so there is nothing to resume after a false
            # interruption.
            interruption={"resume_false_interruption": False},
        ),
    )

    # `console` runs the agent in your terminal with no LiveKit room, so there is
    # nowhere to show the avatar: it is voice only there.
    if not ctx.is_fake_job():
        # Connect first: wait_for_join() below only waits once the room is connected.
        await ctx.connect()

        avatar = simli.AvatarSession(
            simli_config=simli.SimliConfig(
                api_key=os.environ["SIMLI_API_KEY"],
                face_id=FACE_ID,
                max_session_length=MAX_SESSION_LENGTH,
                max_idle_time=MAX_IDLE_TIME,
                # Trinity-2 framing (https://docs.simli.com/api-reference/trinity-2).
                # Video size: 1:1, 16:9 or 9:16, each side at least 512 px. 1366x768 is
                # Trinity-2's full 16:9 frame; Simli's default is 768x768.
                streaming_width=1366,
                streaming_height=768,
                # Where the avatar sits on the canvas, each 0 to 1 (0.5, 1.0 is bottom centre).
                avatar_position_x=0.5,
                avatar_position_y=1.0,
                # Optional: a starting camera, e.g. {"zoom": 1.2, "orbit_y_off": 15}, and ids
                # of your own uploads (POST /assets/backgrounds, /assets/foregrounds).
                # camera={"zoom": 1.2},
                # background_id="...",
                # foreground_id="...",
            ),
        )
        await avatar.start(session, room=ctx.room)
        # On success the plugin sends the agent's voice to the avatar. On a Simli API error
        # (a bad key or face id, or no free session) it logs the error and returns instead.
        if session.output.audio is None:
            logger.error("the Simli avatar didn't start; see the Simli error above")
            ctx.delete_room()
            return

        # Don't start talking until the avatar is in the room and publishing video, so its
        # first words aren't lost.
        try:
            await avatar.wait_for_join(timeout=30)
        except asyncio.TimeoutError:
            logger.error("the Simli avatar didn't join the room")
            ctx.delete_room()
            return

        # The room holds one user, this agent and its avatar, whose session ends with this
        # agent's. When the conversation is over, delete the room to tidy up: everyone leaves
        # at once.
        @session.on("close")
        def _on_session_close(event: CloseEvent) -> None:
            # The session closes when the user leaves, or on an error. A job shutdown is this
            # agent leaving instead: its avatar leaves with it, and the page then leaves too.
            if event.reason != CloseReason.JOB_SHUTDOWN:
                ctx.delete_room()

        # The avatar leaves after MAX_SESSION_LENGTH or MAX_IDLE_TIME, and the conversation
        # ends with it.
        @ctx.room.on("participant_disconnected")
        def _on_participant_disconnected(participant: rtc.RemoteParticipant) -> None:
            if participant.identity == avatar.avatar_identity:
                ctx.delete_room()

    await session.start(agent=Agent(instructions=INSTRUCTIONS), room=ctx.room)
    session.say(FIRST_MESSAGE)


def _check_env() -> None:
    """Fail at startup, not on the first call, when a key is missing from .env."""
    if len(sys.argv) < 2 or sys.argv[1] not in ("dev", "start", "connect"):
        return  # --help, console, download-files, ...
    required = ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SIMLI_API_KEY")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        verb = "is" if len(missing) == 1 else "are"
        sys.exit(f"{', '.join(missing)} {verb} not set. Copy .env.example to .env and fill it in.")


if __name__ == "__main__":
    _check_env()
    cli.run_app(server)
