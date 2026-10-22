"use client";
import { useEffect, useState } from "react";

export function AmbientMotion() {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    document.documentElement.dataset.motion = paused ? "paused" : "running";
  }, [paused]);
  return (
    <>
      <div className="ambient-particles" aria-hidden="true">
        {Array.from({ length: 36 }, (_, i) => (
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
