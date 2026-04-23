import { MeshGradient } from "@paper-design/shaders-react";
import { useTheme } from "../../hooks/useTheme";

/**
 * Animated WebGL mesh gradient background (paper-design shader).
 * fixed=true → covers viewport with position:fixed, content scrolls over it.
 * Theme-aware: soft pastel blue-white in light mode, deep indigo in dark mode.
 */
export function HeroMeshGradient({ className = "", fixed = false }) {
  const { isLight } = useTheme();

  const colors = isLight
    ? ["#FFFFFF", "#DBEAFE", "#E0F2FE", "#BFDBFE", "#F0F9FF"]
    : ["#060B11", "#1e1b4b", "#0f172a", "#1a0a2e", "#0c1631"];

  return (
    <div
      className={`pointer-events-none ${fixed ? 'fixed inset-0 z-0' : 'absolute inset-0'} ${className}`}
      aria-hidden="true"
      style={{ opacity: isLight ? 0.85 : 0.45 }}
    >
      <MeshGradient
        key={isLight ? 'light' : 'dark'}
        colors={colors}
        speed={0.12}
        distortion={0.5}
        swirl={0.25}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
