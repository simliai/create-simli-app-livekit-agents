# Simli + LiveKit Agents, on LiveKit Inference

A real-time voice agent with a face. It runs on [LiveKit Agents](https://docs.livekit.io/agents/), hears and answers you through [LiveKit Inference](https://docs.livekit.io/agents/models/), and [Simli](https://www.simli.com) gives it a lip-synced Trinity-2 avatar that joins the LiveKit room with it.

It's one Python file, plus a small web page to talk to it. You need two free accounts: a [LiveKit Cloud](https://cloud.livekit.io) project on the Build plan (no card required), and [Simli](https://app.simli.com). The LiveKit project's credentials also pay for speech-to-text, the LLM and text-to-speech through LiveKit Inference, so there are no OpenAI, Deepgram or other model keys.

Looking for Pipecat instead? See the sibling starter, [create-simli-app-pipecat](https://github.com/simliai/create-simli-app-pipecat).

## What's in here

- **[`agent.py`](agent.py)**: the agent. Deepgram Nova-3 turns your speech into text, Gemma 4 31B answers, and Inworld TTS-2 speaks the answer, all through LiveKit Inference. The agent sends that voice to a Simli avatar in the same LiveKit room, and the avatar publishes lip-synced video and voice for the agent.
- **[`frontend/`](frontend)**: a Next.js page to talk to the avatar in your browser. [`app/api/token/route.ts`](frontend/app/api/token/route.ts) mints a LiveKit token that dispatches the agent, and [`app/components/AvatarCall.tsx`](frontend/app/components/AvatarCall.tsx) joins the room, publishes your mic and shows the avatar.

## Setup

You need [uv](https://docs.astral.sh/uv/) for Python, [Node.js](https://nodejs.org) 20.9 or later for the page, and four values:

| Variable | Where to find it |
| --- | --- |
| `SIMLI_API_KEY` | [app.simli.com](https://app.simli.com): your profile's API key. The free plan works. |
| `LIVEKIT_URL` | [cloud.livekit.io](https://cloud.livekit.io): create a project (Build plan, free, no card). The project URL, `wss://<your-project>.livekit.cloud`, is shown at the top of the project's dashboard and next to its API keys. |
| `LIVEKIT_API_KEY` | The same project: **Settings**, then **API keys**, then create a key. |
| `LIVEKIT_API_SECRET` | Shown with the key when you create it. Copy it then. |

The LiveKit values must come from a LiveKit Cloud project. LiveKit Inference runs on LiveKit Cloud and authenticates with those credentials. Simli's servers also join the room from the internet, so a LiveKit server running locally on your machine wouldn't work either.

```bash
git clone https://github.com/simliai/create-simli-app-livekit-agents
cd create-simli-app-livekit-agents
uv sync
cp .env.example .env                          # then paste in your four values
cp frontend/.env.example frontend/.env.local  # then copy in the same three LIVEKIT_ values
```

The page's API route reads the LiveKit key and secret on the server; they never reach the browser.

Prefer pip? With Python 3.10 to 3.14:

```bash
python -m venv .venv && source .venv/bin/activate
pip install livekit-agents==1.8.11 livekit-plugins-simli==1.8.11 python-dotenv==1.2.4
```

Then use `python agent.py ...` wherever this README says `uv run agent.py ...`.

## Run it

1. Start the agent: `uv run agent.py dev` (or `python agent.py dev` with pip). It tells you which values are missing from `.env`, if any.
2. In a second terminal, start the page: `cd frontend && npm install && npm run dev`
3. Open http://localhost:3000, click **Start** and allow the microphone. The avatar greets you once it's ready. **End** leaves the room.

`npm run dev` listens on 127.0.0.1 only, so other machines on your network can't open the page and start sessions on your keys. To try it from another device, expose it deliberately (for example `npx next dev -H 0.0.0.0`), and only on a network you trust.

The agent registers as `simli-agent` and only joins rooms whose token dispatches it by that name, as the page's token does. That explicit dispatch matters because a LiveKit project can have other agents deployed that would otherwise join every room. To rename it, set `LIVEKIT_AGENT_NAME` in both `.env` and `frontend/.env.local`.

Alternatively, talk to it from LiveKit's [Agents Playground](https://agents-playground.livekit.io): connect it to your project and set **Agent name** to `simli-agent`.

`uv run agent.py console` talks to the agent in your terminal instead. It is voice only: console mode has no LiveKit room, so there is no avatar. It still needs the `LIVEKIT_` values for Inference, and a microphone (and PortAudio on Linux).

`uv run agent.py dev` shows debug logs; restart it after code changes. livekit-agents 1.8 marks the `dev` and `console` subcommands as deprecated, and `dev` no longer reloads on changes. The [LiveKit CLI](https://docs.livekit.io/agents/server/startup-modes/) (2.18.8 or later) runs the same `agent.py` with `lk agent dev` and `lk agent console`.

## Free plan

Everything here runs on free plans. These are the limits you'll meet first, checked on 17 November 2026; plans change, so follow the links.

**LiveKit Cloud Build plan** ([quotas and limits](https://docs.livekit.io/deploy/admin/quotas-and-limits/), [pricing](https://livekit.com/pricing)):

- **$2.50 of LiveKit Inference credit a month**, for any mix of models. It doesn't roll over, and once it's used up Inference requests fail until the 1st of next month. LiveKit's pricing page calls it "~50 minutes", without saying for which models.
- 5 concurrent agent sessions, and 5 STT and 5 TTS connections, so up to 5 conversations at once.
- 5,000 WebRTC participant minutes and 50 GB of downstream data a month.
- 1,000 agent session minutes a month. LiveKit's [billing page](https://docs.livekit.io/deploy/admin/billing/) meters agent session time for agents *deployed to* LiveKit Cloud; an agent you run yourself, as here, shouldn't use them (not verified).
- Self-hosted agents (like this one, run with `uv run agent.py dev`) get 7,500 turn-detection requests a month. After that, the agent falls back to a smaller local turn detector rather than failing.
- Allowances are hard caps with no overage charges, and they're shared across all your free projects.

**What $2.50 buys at this starter's defaults** (prices from [LiveKit Inference pricing](https://livekit.com/pricing/inference), Build plan):

| Model | Price | Per minute of conversation |
| --- | --- | --- |
| STT: `deepgram/nova-3` | $0.0048 per minute connected | $0.0048 |
| LLM: `google/gemma-4-31b-it` | $0.40 in / $1.20 out per million tokens | about $0.003 |
| TTS: `inworld/inworld-tts-2` | $25 per million characters | about $0.010 to $0.015 |
| **Total** | | **about $0.018 to $0.023** |

That's roughly **110 to 140 minutes of conversation a month**, or 11 to 14 full ten-minute sessions. The LLM and TTS figures are estimates, not measurements: they assume about four replies a minute of about 120 to 150 characters each, and prompts of about 1,500 tokens. Long, talkative conversations cost more. Speech-to-speech instead (`openai/gpt-live-1` at $0.05 a minute) would last about 50 minutes.

**Simli free plan** ([pricing](https://www.simli.com/pricing)): 50 avatar minutes a month and 1 session at a time. That's usually the first limit you'll hit, before the Inference credit.

## Make it yours

Everything for the agent is in one block at the top of [`agent.py`](agent.py):

- **Face:** `FACE_ID`, any Trinity-2 face ID, or set `SIMLI_FACE_ID` in `.env`. The default is Simli's default Trinity-2 face (`14c60d62-6ebf-424d-b626-1f4f91c33b04`). Pick a [preset](https://docs.simli.com/api-reference/preset-faces) or [make your own from a photo](https://app.simli.com).
- **Name, prompt and greeting:** `NAME`, `INSTRUCTIONS` and `FIRST_MESSAGE`. The greeting is spoken word for word as soon as the avatar is in the room.
- **Voice:** `VOICE`. The default face is a woman, so the default is `FEMALE_VOICE` (Inworld's Ashley). Set `VOICE = MALE_VOICE` (Edward) for a male face. Other voices: [LiveKit's TTS models](https://docs.livekit.io/agents/models/tts/).
- **Models:** `STT_MODEL`, `LLM_MODEL` and `TTS_MODEL`, any [LiveKit Inference model ID](https://docs.livekit.io/agents/models/). The defaults are cheap and quick: Gemma 4 31B is LiveKit's recommended voice-agent LLM and is served on LiveKit's own infrastructure, Inworld TTS-2 is half the price of Cartesia Sonic 3 per character, and Nova-3 is a low-latency streaming STT. If you change `TTS_MODEL`, change the voices with it.
- **Session limits:** `MAX_SESSION_LENGTH` (600 seconds) and `MAX_IDLE_TIME` (300 seconds without speaking). The avatar leaves at either limit, and the session ends with it.
- **Framing:** the video is 16:9 at 1366x768, Trinity-2's full frame, with the avatar at the bottom centre. In the `SimliConfig` in `agent.py` you can change the size (1:1 and 9:16 work too), move the avatar, start the [camera](https://docs.simli.com/api-reference/trinity-2/camera) elsewhere, or add your own [background or foreground](https://docs.simli.com/api-reference/trinity-2/backgrounds). See [Framing the video](https://docs.simli.com/api-reference/trinity-2#framing-the-video).
- **Tools and more:** it's a regular LiveKit agent, so everything in the [LiveKit Agents docs](https://docs.livekit.io/agents/) applies.

The page is [`frontend/app/page.tsx`](frontend/app/page.tsx) (layout and text) and [`frontend/app/components/AvatarCall.tsx`](frontend/app/components/AvatarCall.tsx) (the call). It uses [livekit-client](https://docs.livekit.io/reference/client-sdk-js/) directly; for transcripts, agent state and more, see LiveKit's [agent-starter-react](https://github.com/livekit-examples/agent-starter-react).

## How it works

```
  Browser (frontend/)                LiveKit Cloud room                  agent.py (your machine)
  ───────────────────                ──────────────────                  ───────────────────────
  Start ─▶ /api/token (server):
           signs a token for a new
           room that dispatches
           "simli-agent"
  join room ───────────────────────▶ room created ──── dispatch ───────▶ job starts
                                                                         starts the Simli avatar
                                     Simli avatar joins ◀── Simli API ── (face, framing, limits)
  your mic ────────────────────────▶ ─────────────────────────────────▶ STT ▶ LLM ▶ TTS
                                                                         (LiveKit Inference)
                                     Simli avatar ◀──── agent's voice ──┘
  avatar video + voice ◀──────────── lip-synced video + voice
```

1. You click **Start**. The page's API route makes up a room name and signs a token that lets you join that room and dispatches `simli-agent` to it. Joining creates the room, and LiveKit sends the agent there.
2. The agent connects and starts the avatar. The [Simli plugin](https://docs.livekit.io/agents/models/avatar/plugins/simli/) sends the face, framing and session limits to Simli, and Simli's avatar joins the room.
3. The agent waits until the avatar is publishing video. Only then does it start listening and greet you, so its first words aren't lost.
4. Your mic goes to speech-to-text, the LLM answers, and text-to-speech voices the answer, all on LiveKit Inference. LiveKit's turn detector decides when you've finished speaking. The agent streams its voice to the avatar over LiveKit. The avatar publishes lip-synced video and voice on the agent's behalf, under its own identity; the page plays whichever remote video and audio tracks arrive.
5. The avatar's session ends with the agent's. When you leave, or the avatar reaches its time limits, the agent deletes the room to tidy up, so everyone leaves at once. If the agent itself stops mid-call, its avatar leaves with it. Either way the page returns to its start screen.

The Trinity-2 options (`streaming_width`, `streaming_height`, `avatar_position_x`, `avatar_position_y`, `camera`, `background_id`, `foreground_id`) are plain `SimliConfig` fields since livekit-plugins-simli 1.8.10. On older versions they need a subclass of `SimliConfig`; see [Trinity-2 in LiveKit Agents](https://docs.simli.com/api-reference/trinity-2/integration-workarounds).

## Using a coding agent?

This repo includes the [Simli agent skill](https://github.com/simliai/skills) in `.agents/skills/simli` (linked from `.claude/skills/simli`), so Claude Code, Codex, Cursor and other agents that support skills know how to change the face, framing, camera and prompt, and how to fix common errors. To add it to another project: `npx skills add simliai/skills`.

## Troubleshooting

- **`... is not set`:** the agent or the page is missing a value. The agent reads `.env`; the page reads `frontend/.env.local` (restart `npm run dev` after editing it).
- **`the Simli avatar didn't start`:** the Simli error logged just before it says why. `401` means `SIMLI_API_KEY` is wrong. `400` means the face ID wasn't found. `429` means your Simli account is already running as many sessions as it can (one, on the free plan).
- **`the Simli avatar didn't join the room`:** usually Simli couldn't reach your LiveKit server. `LIVEKIT_URL` must be your LiveKit Cloud project's `wss://` URL (see [Setup](#setup)).
- **The avatar appears but never answers, and the agent logs STT, LLM or TTS errors:** LiveKit Inference refused the request. Check that `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` belong to the project in `LIVEKIT_URL`, and whether this month's Inference credit is used up (your project's billing or usage page on [cloud.livekit.io](https://cloud.livekit.io)).
- **The page says the avatar didn't join:** check that `uv run agent.py dev` is running, that both `.env` files hold the same `LIVEKIT_*` values, and that `LIVEKIT_AGENT_NAME` matches if you set it.

## Before you go to production

Anyone who can join a room in your LiveKit project starts a conversation, which uses your Simli minutes and LiveKit Inference credit. The page's `/api/token` route has no login, so anyone who can reach the page could mint a token. That's why a production build (`npm run build` + `npm start`, or any deployed host) refuses with `403` until you change it. Add your own login and rate limiting where the `TODO` in [`app/api/token/route.ts`](frontend/app/api/token/route.ts) says.

For a demo or an internal network only, `ALLOW_UNAUTHENTICATED_SESSIONS=true` in `frontend/.env.local` (or your host's environment) turns the check off: anyone who can reach the page can then start sessions on your keys. Don't set it on a public deployment.

Each token is valid for 2 minutes, for one new room of at most 3 participants (you, the agent and its avatar), and only lets the user publish their microphone. To deploy the agent, run `uv run agent.py start` on any server, or see [LiveKit's deployment guide](https://docs.livekit.io/deploy/agents/). On the Build plan, an agent deployed to LiveKit Cloud may shut down when idle, and the next session can then wait 10 to 20 seconds for it to start. The page builds with `npm run build` and runs with `npm start`, or deploys to any Next.js host.

## More

- [Simli docs](https://docs.simli.com) and [all starters](https://docs.simli.com/api-reference/samples/all-samples)
- [LiveKit Inference models](https://docs.livekit.io/agents/models/) and [pricing](https://livekit.com/pricing/inference)
- Source: https://github.com/simliai/create-simli-app-livekit-agents
- Sibling starter: https://github.com/simliai/create-simli-app-pipecat
- Questions? Ask on [Discord](https://discord.gg/yQx49zNF4d).
