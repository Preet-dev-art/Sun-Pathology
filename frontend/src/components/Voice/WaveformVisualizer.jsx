// src/components/Voice/WaveformVisualizer.jsx

import { useEffect, useRef } from "react";

export default function WaveformVisualizer({ active }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let t = 0;

    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      if (!active) {
        // Flat line when idle
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.strokeStyle = "#93c5fd";
        ctx.lineWidth = 2;
        ctx.stroke();
        frameRef.current = requestAnimationFrame(draw);
        return;
      }

      // Animated wave when listening/speaking
      ctx.beginPath();
      for (let x = 0; x < width; x++) {
        const amplitude = 20 + Math.random() * 15;
        const y = height / 2 + Math.sin((x / width) * Math.PI * 6 + t) * amplitude;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "#2E86C1";
      ctx.lineWidth = 2.5;
      ctx.stroke();

      t += 0.15;
      frameRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(frameRef.current);
  }, [active]);

  return (
    <canvas
      ref={canvasRef}
      width={280}
      height={60}
      className="rounded-xl opacity-80"
    />
  );
}