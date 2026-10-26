# Simli + OpenAI Realtime on LiveKit Agents

A real-time voice agent with a face. It runs on [LiveKit Agents](https://docs.livekit.io/agents/), talks through OpenAI's Realtime API, and [Simli](https://www.simli.com) gives it a lip-synced Trinity-2 avatar that joins the LiveKit room with it.

It's one Python file, plus a small web page to talk to it. You need three keys: Simli, LiveKit and OpenAI. Speech-to-speech means no separate speech-to-text or text-to-speech provider.

Looking for Pipecat instead? See the sibling starter, [create-simli-app-pipecat](https://github.com/simliai/create-simli-app-pipecat).

## What's in here

- **[`agent.py`](agent.py)**: the agent. It hears you through OpenAI's Realtime API (`gpt-realtime`), answers in voice, and sends that voice to a Simli avatar in the same LiveKit room. The avatar publishes lip-synced video and voice for the agent.
- **[`frontend/`](frontend)**: a Next.js page to talk to the avatar in your browser. [`app/api/token/route.ts`](frontend/app/api/token/route.ts) mints a LiveKit token that dispatches the agent, and [`app/components/AvatarCall.tsx`](frontend/app/components/AvatarCall.tsx) joins the room, publishes your mic and shows the avatar.

## Setup

You need [uv](https://docs.astral.sh/uv/) for Python, [Node.js](https://nodejs.org) 20.9 or later for the page, and these keys:

- [Simli](https://app.simli.com) (free plan included)
- [LiveKit Cloud](https://cloud.livekit.io): a project's URL, API key and API secret, from its settings.
- [OpenAI](https://platform.openai.com/api-keys)

`LIVEKIT_URL` must be a LiveKit server reachable from the internet: LiveKit Cloud, or a self-hosted server with a public address. Simli's servers join the room, so a LiveKit server running locally on your machine won't work.

```bash
git clone https://github.com/simliai/create-simli-app-livekit-agents
cd create-simli-app-livekit-agents
uv sync
cp .env.example .env                          # then paste in your keys
cp frontend/.env.example frontend/.env.local  # then copy in the same three LIVEKIT_ values
```

The page's API route reads the LiveKit key and secret on the server; they never reach the browser.

Prefer pip? With Python 3.10 to 3.14:

```bash
python -m venv .venv && source .venv/bin/activate
pip install livekit-agents==1.8.9 livekit-plugins-openai==1.8.9 livekit-plugins-simli==1.8.9 python-dotenv==1.2.4
```

Then use `python agent.py ...` wherever this README says `uv run agent.py ...`.

## Run it

1. Start the agent: `uv run agent.py dev` (or `python agent.py dev` with pip).
2. In a second terminal, start the page: `cd frontend && npm install && npm run dev`
3. Open http://localhost:3000, click **Start** and allow the microphone. The avatar greets you once it's ready. **End** leaves the room.

The agent registers as `simli-agent` and only joins rooms whose token dispatches it by that name, as the page's token does. That explicit dispatch matters because a LiveKit project can have other agents deployed that would otherwise join every room. To rename it, set `LIVEKIT_AGENT_NAME` in both `.env` and `frontend/.env.local`.

Alternatively, talk to it from LiveKit's [Agents Playground](https://agents-playground.livekit.io): connect it to your project and set **Agent name** to `simli-agent`.

`uv run agent.py console` talks to the agent in your terminal instead. It is voice only: console mode has no LiveKit room, so there is no avatar. It needs a microphone (and PortAudio on Linux).

`uv run agent.py dev` shows debug logs; restart it after code changes. livekit-agents 1.8.9 marks the `dev` and `console` subcommands as deprecated, and `dev` no longer reloads on changes. The [LiveKit CLI](https://docs.livekit.io/agents/server/startup-modes/) (2.18.8 or later) runs the same `agent.py` with `lk agent dev` and `lk agent console`.

## Make it yours

Everything for the agent is near the top of [`agent.py`](agent.py):

- **Face:** any Trinity-2 face ID. Pick a [preset](https://docs.simli.com/api-reference/preset-faces) or [make your own from a photo](https://app.simli.com). Or set `SIMLI_FACE_ID`.
- **Framing:** the video is 16:9 at 1366x768, Trinity-2's full frame, with the avatar at the bottom centre. In `Trinity2Config` you can change the size (1:1 and 9:16 work too), move the avatar, start the [camera](https://docs.simli.com/api-reference/trinity-2/camera) elsewhere, or add your own [background or foreground](https://docs.simli.com/api-reference/trinity-2/backgrounds). See [Framing the video](https://docs.simli.com/api-reference/trinity-2#framing-the-video).
- **Model and voice:** `openai.realtime.RealtimeModel(model="gpt-realtime", voice="marin")`.
- **Prompt and greeting:** `INSTRUCTIONS` and the `generate_reply` call.
- **Session limits:** the avatar leaves after 10 minutes (`max_session_length`) or 5 minutes without speaking (`max_idle_time`), and the session ends with it.
- **Tools and more:** it's a regular LiveKit agent, so everything in the [LiveKit Agents docs](https://docs.livekit.io/agents/) applies.

The page is [`frontend/app/page.tsx`](frontend/app/page.tsx) (layout and text) and [`frontend/app/components/AvatarCall.tsx`](frontend/app/components/AvatarCall.tsx) (the call). It uses [livekit-client](https://docs.livekit.io/reference/client-sdk-js/) directly; for transcripts, agent state and more, see LiveKit's [agent-starter-react](https://github.com/livekit-examples/agent-starter-react).

## How it works

1. You click **Start**. The page's API route makes up a room name and signs a token that lets you join that room and dispatches `simli-agent` to it. Joining creates the room, and LiveKit sends the agent there.
2. The agent connects and starts the avatar. The [Simli plugin](https://docs.livekit.io/agents/models/avatar/plugins/simli/) sends the face and framing to Simli, and Simli's avatar joins the room.
3. The agent waits until the avatar is publishing video. Only then does it start listening and greet you, so its first words aren't lost.
4. OpenAI hears your mic and answers in voice. The agent streams that voice to the avatar over LiveKit. The avatar publishes lip-synced video and voice on the agent's behalf, under its own identity; the page plays whichever remote video and audio tracks arrive.
5. The avatar's session ends with the agent's. When you leave, or the avatar reaches its time limits, the agent deletes the room to tidy up, so everyone leaves at once. If the agent itself stops mid-call, its avatar leaves with it. Either way the page returns to its start screen.

`Trinity2Config` exists because the plugin's `SimliConfig` (livekit-plugins-simli 1.8.9) only sends the face (with a legacy style suffix) and the time limits. Its `create_json()` builds the request to Simli, so the subclass adds the Trinity-2 fields there and sends the plain face ID.

## Troubleshooting

- **`the Simli avatar didn't start`:** the Simli error logged just before it says why. `401` means `SIMLI_API_KEY` is wrong. `400` means the face ID wasn't found. `429` means your Simli account is already running as many sessions as it can.
- **`the Simli avatar didn't join the room`:** usually Simli couldn't reach your LiveKit server. `LIVEKIT_URL` must be reachable from the internet (see [Setup](#setup)).
- **The page says the avatar didn't join:** check that `uv run agent.py dev` is running, that both `.env` files hold the same `LIVEKIT_*` values, and that `LIVEKIT_AGENT_NAME` matches if you set it.

## Before you go to production

Anyone who can join a room in your LiveKit project starts a conversation, which uses your Simli minutes and OpenAI credit. The page's `/api/token` route hands a token to anyone who opens the page, so put it behind your own login before you deploy it. To deploy the agent, run `uv run agent.py start` on any server, or see [LiveKit's deployment guide](https://docs.livekit.io/deploy/agents/). The page builds with `npm run build` and runs with `npm start`, or deploys to any Next.js host.

## More

- [Simli docs](https://docs.simli.com) and [all starters](https://docs.simli.com/api-reference/samples/all-samples)
- Source: https://github.com/simliai/create-simli-app-livekit-agents
- Sibling starter: https://github.com/simliai/create-simli-app-pipecat
- Questions? Ask on [Discord](https://discord.gg/yQx49zNF4d).
