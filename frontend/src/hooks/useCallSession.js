// src/hooks/useCallSession.js
// VAD: @ricky0123/vad-web (Silero neural VAD — replaces RMS amplitude loop)

import { useState, useRef, useCallback, useEffect } from "react";
import { MicVAD } from "@ricky0123/vad-web";
import * as ort from "onnxruntime-web";

const API_WS_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace("https://", "wss://")
  .replace("http://", "ws://");

// ── Silero VAD configuration ──────────────────────────────────────────────────
//
// positiveSpeechThreshold (0–1):
//   Silero confidence above which a frame is "speech".
//   0.5 = default. Lower = more sensitive (picks up soft voices).
//   For clinic/home noise environments, 0.5 is the right balance.
//
// negativeSpeechThreshold (0–1):
//   Confidence below which a frame is "silence".
//   Must be lower than positive threshold (hysteresis gap prevents flutter).
//
// minSpeechFrames:
//   Minimum consecutive speech frames before onSpeechStart fires.
//   At 16kHz, each frame is ~32ms. 5 frames = ~160ms minimum speech.
//   Prevents door slams, coughs, single syllable noise from triggering.
//
// redemptionFrames:
//   How many silence frames before onSpeechEnd fires.
//   This is Silero's end-of-utterance detector.
//   15 frames × 32ms = ~480ms of silence before it considers speech done.
//   Good for Hindi/Gujarati which have natural mid-sentence pauses.
//   Increase to 20-25 if Sheetal is cutting off patients mid-sentence.
//
// preSpeechPadFrames:
//   How many frames BEFORE speech detection to include in the audio segment.
//   5 frames = ~160ms of audio before the detected speech start.
//   Prevents clipping the first syllable of "नमस्ते" or "CBC".
// ─────────────────────────────────────────────────────────────────────────────
const VAD_CONFIG = {
  positiveSpeechThreshold: 0.5,
  negativeSpeechThreshold: 0.35,
  minSpeechFrames:         5,
  redemptionFrames:        10,
  preSpeechPadFrames:      3,
};

// Interruption sensitivity — separate from VAD.
// When Sheetal is speaking, we still run a lightweight RMS check
// to detect if the user started talking over her.
// We keep ONE RMS check specifically for interruption (not for utterance detection).
const INTERRUPT_RMS_THRESHOLD = 25;   // higher than before — only very clear speech
const INTERRUPT_INTERVAL_MS   = 100;  // check every 100ms during Sheetal's speech


export function useCallSession({ sessionId }) {
  // ── State (identical to original) ────────────────────────────────────────
  const [callState, setCallState]       = useState("idle");
  const [transcript, setTranscript]     = useState("");
  const [sheetalText, setSheetalText]   = useState("");
  const [language, setLanguage]         = useState("");
  const [callDuration, setCallDuration] = useState(0);
  const [error, setError]               = useState("");
  const [messages, setMessages]         = useState([]);

  // ── Refs ──────────────────────────────────────────────────────────────────
  // KEPT from original:
  const wsRef            = useRef(null);
  const streamRef        = useRef(null);
  const audioContextRef  = useRef(null);   // kept — used in _cleanup and interruption check
  const currentAudioRef  = useRef(null);
  const audioQueueRef    = useRef([]);
  const isPlayingRef     = useRef(false);
  const isSpeakingRef    = useRef(false);
  const durationTimerRef = useRef(null);
  const languageRef      = useRef("");

  // CHANGED: mediaRecorderRef and chunksRef removed —
  // Silero VAD delivers a clean Float32Array directly in onSpeechEnd.
  // No MediaRecorder or manual chunk accumulation needed.

  // NEW: vadRef holds the MicVAD instance for this call
  const vadRef = useRef(null);

  // NEW: interruption detector — lightweight RMS check ONLY during Sheetal's speech
  const interruptIntervalRef  = useRef(null);
  const interruptAnalyserRef  = useRef(null);   // separate analyser just for interruption

  // Indirection refs (identical to original):
  const _startListeningRef        = useRef(null);
  const _playSheetalRef           = useRef(null);
  const _stopListeningRef         = useRef(null);  // renamed from _stopRecordingRef
  const _handleServerMessageRef   = useRef(null);
  const _cleanupRef               = useRef(null);
  const _interruptRef             = useRef(null);

  // ── Sync state → refs (identical to original) ────────────────────────────
  // ── Reset state when sessionId changes ──────────────────────────────
  useEffect(() => {
    setMessages([]);
    setTranscript("");
    setSheetalText("");
    setCallDuration(0);
    setCallState("idle");
    setError("");
  }, [sessionId]);

  useEffect(() => { isSpeakingRef.current = callState === "speaking"; }, [callState]);
  useEffect(() => { languageRef.current = language; },                  [language]);

  // ── Start call ────────────────────────────────────────────────────────────
  // CHANGED: Step 2 is completely different. Everything else identical.

  const startCall = useCallback(async () => {
    setError("");
    setTranscript("");
    setSheetalText("");
    setCallDuration(0);
    setCallState("ringing");

    // Step 1: Open microphone — IDENTICAL to original
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: true,
          echoCancellation: true,
          sampleRate:       16000,
          channelCount:     1,
        },
      });
      streamRef.current = stream;
    } catch {
      setError("Microphone access denied. Please allow microphone access.");
      setCallState("error");
      return;
    }

    // Step 2: Set up Silero VAD — REPLACES the AudioContext/analyser block
    // Step 2: Open WebSocket IMMEDIATELY to trigger the backend greeting logic
    // This allows the server to synthesize TTS *in parallel* while the neural VAD builds.
    const ws = new WebSocket(`${API_WS_BASE}/api/call/ws/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setCallState("connected");
      durationTimerRef.current = setInterval(() => {
        setCallDuration(d => d + 1);
      }, 1000);
      
      // If VAD finished setting up before the websocket opened, start it now.
      if (vadRef.current) {
        _startListeningRef.current?.();
      }
    };

    ws.onmessage = (event) => {
      _handleServerMessageRef.current?.(JSON.parse(event.data));
    };

    ws.onerror = () => {
      setError("Connection lost. Please try again.");
      setCallState("error");
      _cleanupRef.current?.();
    };

    ws.onclose = () => {
      setCallState(prev => prev !== "ended" ? "ended" : prev);
      _cleanupRef.current?.();
    };

    // Step 3: Set up a SEPARATE AudioContext for interruption detection only.
    const interruptCtx      = new AudioContext();
    audioContextRef.current = interruptCtx;
    const interruptSource   = interruptCtx.createMediaStreamSource(stream);
    const interruptAnalyser = interruptCtx.createAnalyser();
    interruptAnalyser.fftSize = 512;
    interruptSource.connect(interruptAnalyser);
    interruptAnalyserRef.current = interruptAnalyser;

    // Step 4: Set up Silero VAD
    // MicVAD.new() takes 1-2 seconds the first time it loads.
    try {
      const vad = await MicVAD.new({
        stream:           stream,
        baseAssetPath:    "/",
        onnxWASMBasePath: "/",
        ort,
        ...VAD_CONFIG,

        onSpeechStart: () => {
          if (!isSpeakingRef.current) {
            setCallState("listening");
          }
        },

        onSpeechEnd: async (audioFloat32) => {
          if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

          const wavBytes = _float32ToWav(audioFloat32, 16000);
          const base64   = _bytesToBase64(wavBytes);

          wsRef.current.send(JSON.stringify({
            type:     "audio",
            data:     base64,
            language: languageRef.current || "hi",
            mime:     "audio/wav",
          }));
          setCallState("thinking");
        },

        onVADMisfire: () => {
          setCallState("listening");
        },
      });

      vadRef.current = vad;
      // If WebSocket already connected while the 1-2s VAD build was happening, start listening!
      if (ws.readyState === WebSocket.OPEN) {
        _startListeningRef.current?.();
      }
    } catch (e) {
      console.error("VAD init error:", e);
      setError("Voice detection failed to load. Please refresh and try again.");
      setCallState("error");
      stream.getTracks().forEach(t => t.stop());
      return;
    }
  }, [sessionId]);

  // ── Handle server messages — IDENTICAL to original ───────────────────────

  const _handleServerMessage = useCallback((msg) => {
    switch (msg.type) {
      case "call_connected":
        setCallState("connected");
        break;

      case "transcript":
        setTranscript(msg.text);
        setLanguage(msg.language || "");
        setCallState("thinking");
        setSheetalText(""); // Clear previous sheetal text for the new response
        setMessages(prev => [...prev, { role: "user", text: msg.text, time: new Date() }]);
        break;

      case "tts_audio":
        setSheetalText(prev => prev ? prev + " " + (msg.reply_text || "") : (msg.reply_text || ""));
        setLanguage(msg.language || "");
        if (msg.reply_text) {
          setMessages(prev => {
            const newArr = [...prev];
            const lastIndex = newArr.length - 1;
            const last = newArr[lastIndex];
            if (last && last.role === "sheetal") {
              // Creating a new immutable object prevents React Strict Mode from applying
              // the text update twice on the same memory reference.
              newArr[lastIndex] = { ...last, text: last.text + " " + msg.reply_text };
            } else {
              newArr.push({ role: "sheetal", text: msg.reply_text, time: new Date() });
            }
            return newArr;
          });
        }
        _playSheetalRef.current?.(msg.audio_b64, msg.mime || "audio/wav");
        break;

      case "error":
        console.error("[Call] Server error:", msg.message);
        _startListeningRef.current?.();
        break;

      case "call_ended":
        setCallState("ended");
        _cleanupRef.current?.();
        break;
    }
  }, []);

  _handleServerMessageRef.current = _handleServerMessage;

  // ── Start / Stop Silero VAD ───────────────────────────────────────────────
  // REPLACES _startListening and _stopRecording from original.
  // Silero manages the recording internally — we just pause/resume it.

  const _startListening = useCallback(() => {
    if (!vadRef.current)                                        return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    vadRef.current.start();
    setCallState("listening");

    // Stop the interruption interval — we're listening now, not Sheetal
    clearInterval(interruptIntervalRef.current);
    interruptIntervalRef.current = null;
  }, []);

  _startListeningRef.current = _startListening;

  const _stopListening = useCallback(() => {
    vadRef.current?.pause();
    clearInterval(interruptIntervalRef.current);
    interruptIntervalRef.current = null;
  }, []);

  _stopListeningRef.current = _stopListening;

  // ── Play Sheetal's audio ──────────────────────────────────────────────────
  // CHANGED: one line — _stopRecordingRef.current?.() → _stopListeningRef.current?.()
  // Everything else identical.

  // ── Interruption detector (runs only while Sheetal is speaking) ───────────
  // CHANGED: this was embedded in the VAD interval loop in the original.
  // Now it's a separate concern — Silero is paused, so we use a simple
  // RMS check specifically for the "did the user start talking?" signal.

  const _startInterruptionWatch = useCallback(() => {
    clearInterval(interruptIntervalRef.current);

    const dataArray = new Uint8Array(
      interruptAnalyserRef.current?.fftSize || 512
    );

    interruptIntervalRef.current = setInterval(() => {
      if (!interruptAnalyserRef.current) return;
      if (!isSpeakingRef.current) {
        clearInterval(interruptIntervalRef.current);
        return;
      }

      interruptAnalyserRef.current.getByteTimeDomainData(dataArray);
      let sumSq = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const dev = dataArray[i] - 128;
        sumSq += dev * dev;
      }
      const rms = Math.sqrt(sumSq / dataArray.length);

      if (rms > INTERRUPT_RMS_THRESHOLD) {
        _interruptRef.current?.();
      }
    }, INTERRUPT_INTERVAL_MS);
  }, []);

  const _processAudioQueue = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      URL.revokeObjectURL(currentAudioRef.current?.src || "");
      currentAudioRef.current = null;
      clearInterval(interruptIntervalRef.current);
      interruptIntervalRef.current = null;
      setCallState("listening");
      _startListeningRef.current?.();
      return;
    }

    isPlayingRef.current = true;
    const { audio_b64, mime } = audioQueueRef.current.shift();

    const byteChars = atob(audio_b64);
    const bytes     = new Uint8Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) bytes[i] = byteChars.charCodeAt(i);
    const blob = new Blob([bytes], { type: mime });
    const url  = URL.createObjectURL(blob);
    const audio = new Audio(url);
    
    // Boost playback speed slightly for all languages to sound more natural
    audio.playbackRate = 1.15;
    
    currentAudioRef.current = audio;

    const onDone = () => {
      URL.revokeObjectURL(url);
      _processAudioQueue();
    };

    audio.onended = onDone;
    audio.onerror = onDone;
    audio.play().catch(onDone);
  }, []);

  const _playSheetal = useCallback((audio_b64, mime) => {
    if (!audio_b64) return;

    // Add to queue
    audioQueueRef.current.push({ audio_b64, mime });
    
    // Pause listening the very first time we queue something
    if (audioQueueRef.current.length === 1 && !isPlayingRef.current) {
      _stopListeningRef.current?.();
      setCallState("speaking");
      _startInterruptionWatch();
      _processAudioQueue();
    }
  }, [_startInterruptionWatch, _processAudioQueue]);

  _playSheetalRef.current = _playSheetal;


  // ── Interruption — IDENTICAL to original ─────────────────────────────────

  const _interrupt = useCallback(() => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    clearInterval(interruptIntervalRef.current);
    interruptIntervalRef.current = null;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "interrupt" }));
    }
    setCallState("listening");
    _startListening();
  }, [_startListening]);

  _interruptRef.current = _interrupt;

  // ── End call — IDENTICAL to original ─────────────────────────────────────

  const endCall = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_call" }));
      wsRef.current.close();
    }
    setCallState("ended");
    _cleanup();
  }, []);

  // ── Cleanup ───────────────────────────────────────────────────────────────
  // CHANGED: replaces VAD interval/timer cleanup with vadRef.destroy()

  const _cleanup = useCallback(() => {
    clearInterval(durationTimerRef.current);
    clearInterval(interruptIntervalRef.current);   // CHANGED: was vadIntervalRef + silenceTimerRef

    audioQueueRef.current = [];
    isPlayingRef.current = false;
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    // CHANGED: destroy Silero VAD instance instead of stopping MediaRecorder
    vadRef.current?.destroy();
    vadRef.current = null;

    streamRef.current?.getTracks().forEach(t => t.stop());
    audioContextRef.current?.close();

    streamRef.current           = null;
    audioContextRef.current     = null;
    interruptAnalyserRef.current = null;
  }, []);

  _cleanupRef.current = _cleanup;

  // ── Auto-start listening when connected — IDENTICAL to original ───────────

  useEffect(() => {
    if (callState === "connected") {
      _startListening();
    }
  }, [callState]);

  // ── Cleanup on unmount — IDENTICAL to original ───────────────────────────

  useEffect(() => {
    return () => _cleanup();
  }, []);

  // ── Return — IDENTICAL to original ───────────────────────────────────────

  return {
    callState,
    transcript,
    sheetalText,
    messages,
    language,
    callDuration,
    error,
    startCall,
    endCall,
  };
}


// ── Audio utility functions ────────────────────────────────────────────────
// These replace the recorder.onstop blob encoding from the original.
// Silero gives us Float32Array directly — we encode it to WAV ourselves.

/**
 * Convert a Float32Array (16kHz mono PCM) to WAV file bytes.
 * WAV is universally supported and Sarvam STT accepts it directly.
 */
function _float32ToWav(samples, sampleRate) {
  const numSamples  = samples.length;
  const buffer      = new ArrayBuffer(44 + numSamples * 2);
  const view        = new DataView(buffer);

  // WAV header
  const writeStr = (offset, str) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };

  writeStr(0,  "RIFF");
  view.setUint32(4,  36 + numSamples * 2, true);   // file size - 8
  writeStr(8,  "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16,         true);   // PCM chunk size
  view.setUint16(20, 1,          true);   // PCM format
  view.setUint16(22, 1,          true);   // mono
  view.setUint32(24, sampleRate, true);   // sample rate
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2,          true);   // block align
  view.setUint16(34, 16,         true);   // bits per sample
  writeStr(36, "data");
  view.setUint32(40, numSamples * 2, true);

  // PCM samples: Float32 (-1.0 to 1.0) → Int16 (-32768 to 32767)
  let offset = 44;
  for (let i = 0; i < numSamples; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped < 0 ? clamped * 32768 : clamped * 32767, true);
    offset += 2;
  }

  return new Uint8Array(buffer);
}

/**
 * Convert Uint8Array to base64 string safely (chunked to avoid stack overflow).
 */
function _bytesToBase64(bytes) {
  let binary = "";
  const CHUNK = 8192;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    binary += String.fromCharCode(...bytes.subarray(i, i + CHUNK));
  }
  return btoa(binary);
}