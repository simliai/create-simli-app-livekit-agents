"""A LiveKit Agents voice agent with a Simli Trinity-2 avatar.

Run `uv run agent.py dev`, then talk to it from LiveKit's Agent Console or the Agents
Playground. See README.md.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
from livekit.plugins import openai, simli

load_dotenv()

logger = logging.getLogger("simli-agent")

# A Trinity-2 preset face. Set SIMLI_FACE_ID in .env to use another one.
DEFAULT_FACE_ID = "bf13113a-355a-4d97-8b90-4edccd1da7b2"

INSTRUCTIONS = (
    "You are a friendly voice assistant, seen by the user as a video avatar. "
    "Speak English unless the user speaks another language. "
    "Keep your replies short and conversational. Don't use emojis, lists or markdown."
)


@dataclass
class Trinity2Config(simli.SimliConfig):
    """SimliConfig plus Trinity-2's framing options.

    The released plugin's SimliConfig only sends the face, with a legacy style suffix, and the
    timeouts to Simli's POST /compose/token. Its create_json() builds that request body, so this
    subclass adds the Trinity-2 fields (https://docs.simli.com/api-reference/trinity-2) and
    sends the plain face ID. Faces older than Trinity-2 ignore these fields.
    """

    # Video size: 1:1, 16:9 or 9:16, each side at least 512 px.
    # 1366x768 is Trinity-2's full 16:9 frame; the API default is 768x768.
    streaming_width: int = 1366
    streaming_height: int = 768
    # Where the avatar sits on the canvas, each 0 to 1 (0.5, 1.0 is bottom centre).
    avatar_position_x: float = 0.5
    avatar_position_y: float = 1.0
    # Starting camera, e.g. {"zoom": 1.2, "orbit_y_off": 15}. None keeps the avatar's own.
    camera: dict[str, float] | None = None
    # Ids of your own uploads (POST /assets/backgrounds, /assets/foregrounds).
    background_id: str | None = None
    foreground_id: str | None = None

    def create_json(self) -> dict[str, Any]:
        body = super().create_json()
        body["faceId"] = self.face_id  # the plain face ID, without the legacy suffix
        for name in (
            "streaming_width",
            "streaming_height",
            "avatar_position_x",
            "avatar_position_y",
            "camera",
            "background_id",
            "foreground_id",
        ):
            if (value := getattr(self, name)) is not None:
                body[name] = value
        return body


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession(
        # A speech-to-speech model: no separate STT or TTS provider, and one OpenAI key.
        llm=openai.realtime.RealtimeModel(model="gpt-realtime", voice="marin"),
        # The avatar can't pause its speech, so there is nothing to resume after a false
        # interruption.
        turn_handling={"interruption": {"resume_false_interruption": False}},
    )

    # `console` runs the agent in your terminal with no LiveKit room, so there is
    # nowhere to show the avatar: it is voice only there.
    if not ctx.is_fake_job():
        # Connect first: wait_for_join() below only waits once the room is connected.
        await ctx.connect()

        avatar = simli.AvatarSession(
            simli_config=Trinity2Config(
                api_key=os.environ["SIMLI_API_KEY"],
                face_id=os.getenv("SIMLI_FACE_ID") or DEFAULT_FACE_ID,
                max_session_length=600,  # seconds; the avatar leaves after this
                max_idle_time=300,  # seconds without speaking before the avatar leaves
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

        # The room holds one user, this agent and its avatar. When the session ends (the
        # user left) or the avatar leaves (after max_session_length or max_idle_time),
        # delete the room so everyone leaves at once; the avatar would otherwise stay on,
        # still billed, for up to a minute.
        session.on("close", lambda _: ctx.delete_room())

        @ctx.room.on("participant_disconnected")
        def _on_participant_disconnected(participant: rtc.RemoteParticipant) -> None:
            if participant.identity == avatar.avatar_identity:
                ctx.delete_room()

    await session.start(agent=Agent(instructions=INSTRUCTIONS), room=ctx.room)
    session.generate_reply(instructions="Greet the user in one short sentence.")


if __name__ == "__main__":
    cli.run_app(server)
