// src/hooks/useVoiceRecorder.js

import { useState, useRef, useCallback } from "react";

const SILENCE_THRESHOLD = 8;       // amplitude threshold (0–255 scale)
const SILENCE_DURATION_MS = 1200;  // stop after 1.2s of silence
const MIN_RECORDING_MS = 800;      // don't stop before 0.8s (avoids accidental cuts)

export function useVoiceRecorder({ onAudioReady }) {
  const [status, setStatus] = useState("idle"); // idle | listening | processing | speaking | error
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const recordingStartRef = useRef(null);
  const vadIntervalRef = useRef(null);

  const startListening = useCallback(async () => {
    setError("");
    setTranscript("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: true,
          echoCancellation: true,
          sampleRate: 16000,
        },
      });

      // Set up Web Audio API for VAD
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // MediaRecorder for capturing audio
      chunksRef.current = [];
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        audioContextRef.current?.close();
        clearInterval(vadIntervalRef.current);
        setStatus("processing");
        await onAudioReady(blob);
      };

      mediaRecorderRef.current.start(100); // collect chunks every 100ms
      recordingStartRef.current = Date.now();
      setStatus("listening");

      // VAD loop — check for silence every 200ms
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      vadIntervalRef.current = setInterval(() => {
        analyserRef.current?.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        const elapsed = Date.now() - recordingStartRef.current;

        if (avg < SILENCE_THRESHOLD && elapsed > MIN_RECORDING_MS) {
          // Start silence timer
          if (!silenceTimerRef.current) {
            silenceTimerRef.current = setTimeout(() => {
              stopListening();
            }, SILENCE_DURATION_MS);
          }
        } else {
          // Voice detected — reset silence timer
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        }
      }, 200);

    } catch (err) {
      console.error("Mic error:", err);
      setError("Microphone access denied. Please allow microphone in browser settings.");
      setStatus("error");
    }
  }, [onAudioReady]);

  const stopListening = useCallback(() => {
    clearInterval(vadIntervalRef.current);
    clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = null;
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const setReady = useCallback(() => setStatus("idle"), []);
  const setSpeaking = useCallback(() => setStatus("speaking"), []);

  return {
    status,           // "idle" | "listening" | "processing" | "speaking" | "error"
    transcript,
    setTranscript,
    error,
    startListening,
    stopListening,
    setReady,
    setSpeaking,
  };
}