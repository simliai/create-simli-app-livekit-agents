# Simli + OpenAI Realtime on LiveKit Agents

A real-time voice agent with a face. It runs on [LiveKit Agents](https://docs.livekit.io/agents/), talks through OpenAI's Realtime API, and [Simli](https://www.simli.com) gives it a lip-synced Trinity-2 avatar that joins the LiveKit room with it.

It's one Python file. You need three keys: Simli, LiveKit and OpenAI. Speech-to-speech means no separate speech-to-text or text-to-speech provider.

Looking for Pipecat instead? See the sibling starter, [create-simli-app-pipecat](https://github.com/simliai/create-simli-app-pipecat).

## What's in here

- **[`agent.py`](agent.py)**: the agent. It hears you through OpenAI's Realtime API (`gpt-realtime`), answers in voice, and sends that voice to a Simli avatar in the same LiveKit room. The avatar publishes lip-synced video and voice for the agent.
- **No frontend.** Talk to it from LiveKit's Agent Console, the Agents Playground, or any LiveKit agent frontend (see [Talk to it](#talk-to-it)).

## Setup

You need [uv](https://docs.astral.sh/uv/) for Python, and these keys:

- [Simli](https://app.simli.com) (free plan included)
- [LiveKit Cloud](https://cloud.livekit.io): a project's URL, API key and API secret, from its settings. A self-hosted LiveKit server works too, if Simli's servers can reach it over the internet.
- [OpenAI](https://platform.openai.com/api-keys)

```bash
git clone https://github.com/simliai/create-simli-app-livekit
cd create-simli-app-livekit
uv sync
cp .env.example .env   # then paste in your keys
```

Prefer pip? With Python 3.10 to 3.14:

```bash
python -m venv .venv && source .venv/bin/activate
pip install livekit-agents==1.8.9 livekit-plugins-openai==1.8.9 livekit-plugins-simli==1.8.9 python-dotenv==1.2.4
```

Then use `python agent.py ...` wherever this README says `uv run agent.py ...`.

## Run it

```bash
uv run agent.py dev     # while developing: debug logs; restart it after code changes
uv run agent.py start   # in production
```

Both connect to your LiveKit project and wait. By default the agent joins every new room in the project, and each one starts a Simli session. If you share the project with other apps, set `LIVEKIT_AGENT_NAME` in `.env`. The agent then only joins rooms that [dispatch it by that name](https://docs.livekit.io/agents/server/agent-dispatch/).

`uv run agent.py console` talks to the agent in your terminal instead. It is voice only: console mode has no LiveKit room, so there is no avatar. It needs a microphone (and PortAudio on Linux).

livekit-agents 1.8.9 marks the `dev` and `console` subcommands as deprecated, and `dev` no longer reloads on changes. The [LiveKit CLI](https://docs.livekit.io/agents/server/startup-modes/) (2.18.8 or later) runs the same `agent.py` with `lk agent dev` and `lk agent console`.

### Talk to it

With the agent running:

- **Agent Console:** in LiveKit Cloud, open your project's [Agents](https://cloud.livekit.io/projects/p_/agents/console) page and click **Launch Console**.
- **Agents Playground:** open https://agents-playground.livekit.io and connect it to your project.
- **Your own app:** any LiveKit agent frontend, such as [agent-starter-react](https://github.com/livekit-examples/agent-starter-react). The avatar's video arrives as the agent's video.

Allow the microphone. The avatar greets you once it's ready.

## Make it yours

Everything is near the top of [`agent.py`](agent.py):

- **Face:** any Trinity-2 face ID. Pick a [preset](https://docs.simli.com/api-reference/preset-faces) or [make your own from a photo](https://app.simli.com). Or set `SIMLI_FACE_ID`.
- **Framing:** the video is 16:9 at 1366x768, Trinity-2's full frame, with the avatar at the bottom centre. In `Trinity2Config` you can change the size (1:1 and 9:16 work too), move the avatar, start the [camera](https://docs.simli.com/api-reference/trinity-2/camera) elsewhere, or add your own [background or foreground](https://docs.simli.com/api-reference/trinity-2/backgrounds). See [Framing the video](https://docs.simli.com/api-reference/trinity-2#framing-the-video).
- **Model and voice:** `openai.realtime.RealtimeModel(model="gpt-realtime", voice="marin")`.
- **Prompt and greeting:** `INSTRUCTIONS` and the `generate_reply` call.
- **Session limits:** the avatar leaves after 10 minutes (`max_session_length`) or 5 minutes without speaking (`max_idle_time`), and the session ends with it.
- **Tools and more:** it's a regular LiveKit agent, so everything in the [LiveKit Agents docs](https://docs.livekit.io/agents/) applies.

## How it works

1. LiveKit dispatches the agent to a room. The agent connects and starts the avatar. The [Simli plugin](https://docs.livekit.io/agents/models/avatar/plugins/simli/) sends the face and framing to Simli, and Simli's avatar joins the room.
2. The agent waits until the avatar is publishing video. Only then does it start listening and greet you, so its first words aren't lost.
3. OpenAI hears you and answers in voice. The agent streams that voice to the avatar over LiveKit. The avatar publishes lip-synced video and voice on the agent's behalf, so frontends show them as the agent's.
4. When you leave, or the avatar times out, the agent deletes the room, so the avatar's session ends at once.

`Trinity2Config` exists because the plugin's `SimliConfig` (livekit-plugins-simli 1.8.9) only sends the face (with a legacy style suffix) and the time limits. Its `create_json()` builds the request to Simli, so the subclass adds the Trinity-2 fields there and sends the plain face ID.

## Troubleshooting

- **`the Simli avatar didn't start`:** the Simli error logged just before it says why. `401` means `SIMLI_API_KEY` is wrong. `400` means the face ID wasn't found. `429` means your Simli account is already running as many sessions as it can.
- **The agent never joins:** check the `LIVEKIT_*` values, and if you set `LIVEKIT_AGENT_NAME`, make sure your frontend dispatches that name.

## Before you go to production

Anyone who can join a room in your LiveKit project starts a conversation, which uses your Simli minutes and OpenAI credit. Only hand out LiveKit tokens to people you trust. To deploy, run `uv run agent.py start` on any server, or see [LiveKit's deployment guide](https://docs.livekit.io/deploy/agents/).

## More

- [Simli docs](https://docs.simli.com) and [all starters](https://docs.simli.com/api-reference/samples/all-samples)
- Source: https://github.com/simliai/create-simli-app-livekit
- Sibling starter: https://github.com/simliai/create-simli-app-pipecat
- Questions? Ask on [Discord](https://discord.gg/yQx49zNF4d).
