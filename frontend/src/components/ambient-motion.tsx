"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

export function AmbientMotion() {
  const path = usePathname();
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    document.documentElement.dataset.motion = paused ? "paused" : "running";
  }, [paused]);
  const publicPage = path === "/" || path === "/events";
  if (!publicPage) return null;
  return (
    <>
      <div className="ambient-particles" aria-hidden="true">
        {Array.from({ length: 16 }, (_, i) => (
          <i
            key={i}
            style={{
              left: `${(i * 37 + 7) % 100}%`,
              top: `${(i * 23 + 11) % 100}%`,
              animationDelay: `-${i * 2.3}s`,
              animationDuration: `${22 + (i % 5) * 4}s`,
            }}
          />
        ))}
      </div>
      <button
        className="motion-toggle"
        type="button"
        aria-pressed={paused}
        onClick={() => setPaused(!paused)}
      >
        {paused ? "Resume motion" : "Pause motion"}
      </button>
    </>
  );
}
