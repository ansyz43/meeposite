import { MeshGradient } from "@paper-design/shaders-react";

/**
 * Animated WebGL mesh gradient background (paper-design shader).
 * fixed=true → covers viewport with position:fixed, content scrolls over it.
 */
export function HeroMeshGradient({ className = "", fixed = false }) {
  return (
    <div
      className={`pointer-events-none ${fixed ? 'fixed inset-0 z-0' : 'absolute inset-0'} ${className}`}
      aria-hidden="true"
      style={{ opacity: 0.45 }}
    >
      <MeshGradient
        colors={["#060B11", "#1e1b4b", "#0f172a", "#1a0a2e", "#0c1631"]}
        speed={0.12}
        distortion={0.5}
        swirl={0.25}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
