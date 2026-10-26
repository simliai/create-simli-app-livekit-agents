import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";

// The name agent.py registers under. Change both together (LIVEKIT_AGENT_NAME).
const AGENT_NAME = process.env.LIVEKIT_AGENT_NAME || "simli-agent";

// Mints a token for a new room. The API secret signs it here, on the server, and never
// reaches the browser.
export async function POST() {
  const { LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET } = process.env;
  if (!LIVEKIT_URL || !LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
    return Response.json(
      { error: "Set LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET in frontend/.env.local" },
      { status: 500 },
    );
  }

  const roomName = `simli-${crypto.randomUUID()}`;
  const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
    identity: `user-${crypto.randomUUID().slice(0, 8)}`,
    ttl: "10m", // only needs to last until the user joins
  });
  token.addGrant({ room: roomName, roomJoin: true, canPublish: true, canSubscribe: true });
  // The room is created when this user joins it, and LiveKit then dispatches the agent named
  // here. A room that names its agents gets only those, not every agent in the project.
  token.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: AGENT_NAME })],
  });

  return Response.json({ serverUrl: LIVEKIT_URL, participantToken: await token.toJwt() });
}
