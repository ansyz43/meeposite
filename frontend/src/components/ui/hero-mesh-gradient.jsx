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
      style={{ opacity: 0.4 }}
    >
      <MeshGradient
        colors={["#060B11", "#10B981", "#0D9488", "#06B6D4", "#064E3B"]}
        speed={0.15}
        distortion={0.6}
        swirl={0.3}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
