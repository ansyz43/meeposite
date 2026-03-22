import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect } from "react";

export function TextRoll({
  texts = [],
  className,
  duration = 3000,
}) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (texts.length <= 1) return;
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % texts.length);
    }, duration);
    return () => clearInterval(interval);
  }, [texts.length, duration]);

  return (
    <span className={cn("relative inline-grid overflow-hidden align-bottom", className)}>
      {/* Hidden sizer texts — all stacked in same grid cell to set width to longest */}
      {texts.map((text, i) => (
        <span
          key={`sizer-${i}`}
          className="invisible col-start-1 row-start-1 gradient-text"
          aria-hidden="true"
        >
          {text}
        </span>
      ))}
      {/* Animated visible text */}
      <AnimatePresence mode="wait">
        <motion.span
          key={index}
          initial={{ y: "100%", opacity: 0 }}
          animate={{ y: "0%", opacity: 1 }}
          exit={{ y: "-100%", opacity: 0 }}
          transition={{
            duration: 0.5,
            ease: [0.32, 0.72, 0, 1],
          }}
          className="col-start-1 row-start-1 gradient-text"
        >
          {texts[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
