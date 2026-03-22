import { cn } from "@/lib/utils";

export function RainbowButton({ children, className, ...props }) {
  return (
    <button
      className={cn(
        "group relative inline-flex h-12 animate-rainbow cursor-pointer items-center justify-center rounded-xl border-0 bg-[length:200%] px-8 py-2 font-semibold text-white transition-all duration-300 [background-clip:padding-box,border-box,border-box] [background-origin:border-box] [border:calc(0.08*1rem)_solid_transparent]",
        // before styles (glow)
        "before:absolute before:bottom-[-20%] before:left-1/2 before:z-0 before:h-[20%] before:w-[60%] before:-translate-x-1/2 before:animate-rainbow before:bg-[linear-gradient(90deg,var(--color-1),var(--color-2),var(--color-3),var(--color-4),var(--color-5))] before:bg-[length:200%] before:[filter:blur(calc(0.8*1rem))]",
        // light mode (we're dark-only but keeping compat)
        "bg-[linear-gradient(#0C1219,#0C1219),linear-gradient(#0C1219_50%,rgba(12,18,25,0.6)_80%,rgba(12,18,25,0)),linear-gradient(90deg,var(--color-1),var(--color-2),var(--color-3),var(--color-4),var(--color-5))]",
        // dark mode override
        "dark:bg-[linear-gradient(#0C1219,#0C1219),linear-gradient(#0C1219_50%,rgba(12,18,25,0.6)_80%,rgba(12,18,25,0)),linear-gradient(90deg,var(--color-1),var(--color-2),var(--color-3),var(--color-4),var(--color-5))]",
        "hover:scale-105 active:scale-100",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
