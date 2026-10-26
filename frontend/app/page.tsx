import AvatarCall from "./components/AvatarCall";
import Navbar from "./components/Navbar";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-8 pt-28 font-abc-repro text-sm text-white">
      <div className="flex w-full flex-col items-center gap-6 rounded-xl p-6 pb-[40px]">
        <AvatarCall />
      </div>

      <div className="flex max-w-[350px] flex-col items-center font-thin">
        <span className="mb-[8px] font-bold leading-5">
          Talk to a LiveKit voice agent with a Simli avatar.
        </span>
        <ul className="ml-[6px] mt-2 max-w-[350px] list-inside list-decimal">
          <li className="mb-1">
            Start the agent with <code>uv run agent.py dev</code>.
          </li>
          <li className="mb-1">Click Start, allow the microphone, and say hello.</li>
          <li className="mb-1">
            Change the face, voice and prompt in <code>agent.py</code>.
          </li>
        </ul>
      </div>

      <Navbar />
    </main>
  );
}
