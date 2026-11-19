"use client";

import { useEffect, useRef } from "react";

// Each word turns from muted to full ink as it crosses a line two thirds down the viewport.
export function TaglineReveal({ lines }: { lines: string[] }) {
  const ref = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const words = Array.from(root.querySelectorAll<HTMLSpanElement>("[data-word]"));
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          (e.target as HTMLElement).dataset.lit = String(e.isIntersecting || e.boundingClientRect.top < 0);
        }
      },
      { rootMargin: "0px 0px -35% 0px", threshold: 1 },
    );
    words.forEach((w) => io.observe(w));
    return () => io.disconnect();
  }, []);

  return (
    <p ref={ref} className="max-w-[680px] text-3xl font-semibold tracking-tight sm:text-4xl">
      {lines.map((line, li) => (
        <span key={li} className="block">
          {line.split(" ").map((w, wi) => (
            <span
              key={wi}
              data-word
              className="text-ink/30 transition-colors duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] data-[lit=true]:text-ink"
            >
              {w}{" "}
            </span>
          ))}
        </span>
      ))}
    </p>
  );
}
