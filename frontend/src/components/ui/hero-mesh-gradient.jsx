import { useEffect, useRef } from "react";

/**
 * Animated mesh gradient background using Canvas.
 * When fixed=true, covers the full viewport with position:fixed so content scrolls over it.
 */
export function HeroMeshGradient({ className = "", fixed = false }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w, h;
    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (fixed) {
        w = window.innerWidth;
        h = window.innerHeight;
      } else {
        const rect = canvas.parentElement.getBoundingClientRect();
        w = rect.width;
        h = rect.height;
      }
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    const blobs = [
      { x: 0.2, y: 0.3, r: 0.45, color: [16, 185, 129], speed: 0.0003, phase: 0 },
      { x: 0.7, y: 0.2, r: 0.4, color: [20, 184, 166], speed: 0.0004, phase: 2 },
      { x: 0.5, y: 0.7, r: 0.5, color: [6, 182, 212], speed: 0.00025, phase: 4 },
      { x: 0.8, y: 0.6, r: 0.35, color: [52, 211, 153], speed: 0.00035, phase: 1 },
    ];

    function draw(t) {
      ctx.clearRect(0, 0, w, h);
      for (const b of blobs) {
        const cx = (b.x + Math.sin(t * b.speed + b.phase) * 0.08) * w;
        const cy = (b.y + Math.cos(t * b.speed * 0.7 + b.phase) * 0.06) * h;
        const radius = b.r * Math.min(w, h);
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        grad.addColorStop(0, `rgba(${b.color.join(",")}, 0.12)`);
        grad.addColorStop(0.5, `rgba(${b.color.join(",")}, 0.05)`);
        grad.addColorStop(1, `rgba(${b.color.join(",")}, 0)`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }
      animRef.current = requestAnimationFrame(draw);
    }
    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [fixed]);

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none ${fixed ? 'fixed inset-0 z-0' : 'absolute inset-0'} ${className}`}
      aria-hidden="true"
    />
  );
}
