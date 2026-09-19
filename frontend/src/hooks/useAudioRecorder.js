import { useCallback, useRef, useState } from "react";

// Manual record -> speak -> Done flow, per the voice pipeline design: no
// voice-activity-detection auto-stop (unreliable on a noisy shop floor),
// just an explicit stop trigger from the worker.
const MAX_RECORDING_MS = 90_000;

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const timeoutRef = useRef(null);
  const stopResolveRef = useRef(null);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        if (stopResolveRef.current) {
          stopResolveRef.current(blob);
          stopResolveRef.current = null;
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);

      // Safety-net timeout, not a VAD substitute — just prevents an open
      // mic from recording indefinitely if the worker forgets to stop.
      timeoutRef.current = setTimeout(() => stop(), MAX_RECORDING_MS);
    } catch (err) {
      setError(err.message || "Microphone access denied");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === "inactive") {
        resolve(null);
        return;
      }
      clearTimeout(timeoutRef.current);
      stopResolveRef.current = resolve;
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    });
  }, []);

  return { isRecording, error, start, stop };
}
