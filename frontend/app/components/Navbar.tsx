import Image from "next/image";
import githubLogo from "@/media/github-mark-white.svg";
import simliLogo from "@/media/SimliLogoV2.svg";

const links = [
  { label: "Documentation", href: "https://docs.simli.com" },
  { label: "Billing", href: "https://simli.com" },
  { label: "Discord", href: "https://discord.gg/yQx49zNF4d" },
];

// The Simli logo, the GitHub link and the footer links, as in create-simli-app-openai.
export default function Navbar() {
  return (
    <>
      <a href="https://www.simli.com" className="absolute left-[32px] top-[32px]">
        <Image src={simliLogo} alt="Simli logo" />
      </a>
      <a
        href="https://github.com/simliai/create-simli-app-livekit-agents"
        className="absolute right-[32px] top-[32px] text-base font-bold leading-8 sm:text-xl"
      >
        <Image src={githubLogo} alt="" className="mr-2 inline w-[20px]" />
        <span className="hidden sm:inline">create-simli-app (LiveKit Agents)</span>
      </a>
      <nav className="mt-12 md:fixed md:bottom-[32px] md:left-[32px] md:mt-0">
        <ul className="flex gap-8 font-medium">
          {links.map(({ label, href }) => (
            <li key={label}>
              <a href={href} target="_blank" rel="noreferrer" className="hover:underline">
                {label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
