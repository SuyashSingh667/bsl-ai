"""
Production-Safe Pluggable Text-to-Speech (TTS) Provider Interface.
Replaces unofficial endpoints with enterprise-grade providers:
  1. PreCachedSOPAudioProvider: Instant, offline-capable static audio for standard SOP prompts.
  2. LocalOfflineTTSProvider: System-level offline synthesis (macOS say / eSpeak).
  3. LicensedCloudTTSProvider: Production enterprise cloud TTS (Azure Speech / Google Cloud TTS / AWS Polly).
"""

from __future__ import annotations

import abc
import hashlib
import logging
import os
from pathlib import Path
import subprocess
from typing import Any

from app.config import BACKEND_DIR

logger = logging.getLogger(__name__)

PRECACHED_SOP_DIR = BACKEND_DIR / "data" / "cached_sop_audio"
PRECACHED_SOP_DIR.mkdir(parents=True, exist_ok=True)


class TTSProvider(abc.ABC):
    """Abstract interface for enterprise text-to-speech providers."""

    @abc.abstractmethod
    def synthesize(self, text: str, language: str, out_path: Path) -> bool:
        """Synthesizes text into audio file at out_path. Returns True on success."""
        pass


class PreCachedSOPAudioProvider(TTSProvider):
    """
    Serves verified pre-generated audio for standard plant safety SOP guidance.
    Guarantees zero-latency, high-fidelity offline playback for life-critical instructions.
    """

    def __init__(self, cache_dir: Path = PRECACHED_SOP_DIR):
        self.cache_dir = cache_dir

    def get_cache_key(self, text: str, language: str) -> str:
        clean = " ".join(text.strip().lower().split())
        return hashlib.sha256(f"{language}:{clean}".encode("utf-8")).hexdigest()[:20]

    def synthesize(self, text: str, language: str, out_path: Path) -> bool:
        key = self.get_cache_key(text, language)
        # Check if pre-cached file exists in repository
        for ext in [".mp3", ".wav", ".m4a"]:
            cached_file = self.cache_dir / f"sop_{key}{ext}"
            if cached_file.exists() and cached_file.stat().st_size > 0:
                try:
                    import shutil
                    shutil.copyfile(cached_file, out_path)
                    logger.info(f"Served pre-cached SOP audio for key {key} ({language})")
                    return True
                except Exception as exc:
                    logger.warning(f"Failed to copy pre-cached SOP audio: {exc}")
        return False

    def store_cache(self, text: str, language: str, audio_source: Path) -> Path | None:
        if not audio_source.exists():
            return None
        key = self.get_cache_key(text, language)
        target = self.cache_dir / f"sop_{key}{audio_source.suffix}"
        import shutil
        shutil.copyfile(audio_source, target)
        return target


class LocalOfflineTTSProvider(TTSProvider):
    """
    System-level offline TTS provider with zero external network dependencies.
    Uses macOS 'say' with afconvert or Linux 'espeak-ng'.
    """

    def synthesize(self, text: str, language: str, out_path: Path) -> bool:
        clean_text = text.strip()
        # Try macOS say first
        try:
            aiff_tmp = out_path.with_suffix(".aiff")
            voice = "Samantha" if language == "en" else "Lekha"
            res = subprocess.run(["say", "-v", voice, "-o", str(aiff_tmp), clean_text], capture_output=True)
            if res.returncode != 0:
                subprocess.run(["say", "-o", str(aiff_tmp), clean_text], capture_output=True)

            if aiff_tmp.exists() and aiff_tmp.stat().st_size > 0:
                wav_target = out_path.with_suffix(".wav")
                conv = subprocess.run(
                    ["afconvert", "-f", "WAVE", "-d", "LEI16@22050", str(aiff_tmp), str(wav_target)],
                    capture_output=True,
                )
                if aiff_tmp.exists():
                    aiff_tmp.unlink()
                if conv.returncode == 0 and wav_target.exists() and wav_target.stat().st_size > 0:
                    if out_path.suffix != ".wav":
                        # If destination was mp3, copy or leave as wav
                        import shutil
                        shutil.copyfile(wav_target, out_path)
                    return True
        except Exception:
            pass

        # Try espeak-ng on Linux
        try:
            espeak_lang = "hi" if language == "hi" else "en"
            wav_target = out_path.with_suffix(".wav")
            res = subprocess.run(["espeak-ng", "-v", espeak_lang, "-w", str(wav_target), clean_text], capture_output=True)
            if res.returncode == 0 and wav_target.exists() and wav_target.stat().st_size > 0:
                if out_path.suffix != ".wav":
                    import shutil
                    shutil.copyfile(wav_target, out_path)
                return True
        except Exception:
            pass

        return False


class LicensedCloudTTSProvider(TTSProvider):
    """
    Enterprise licensed Cloud TTS provider (Azure Speech Services / AWS Polly / Google Cloud TTS).
    Requires explicit plant enterprise API credentials in environment variables.
    """

    def __init__(self):
        self.azure_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_region = os.getenv("AZURE_SPEECH_REGION", "centralindia")

    def synthesize(self, text: str, language: str, out_path: Path) -> bool:
        if not self.azure_key:
            return False

        try:
            import azure.cognitiveservices.speech as speechsdk
            speech_config = speechsdk.SpeechConfig(subscription=self.azure_key, region=self.azure_region)
            voice_name = "hi-IN-SwaraNeural" if language == "hi" else "en-IN-NeerjaExpressiveNeural"
            speech_config.speech_synthesis_voice_name = voice_name

            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_path))
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Successfully synthesized speech via Licensed Azure Cloud TTS ({voice_name})")
                return True
        except Exception as exc:
            logger.warning(f"Licensed Cloud TTS synthesis failed: {exc}")

        return False


class CompositeTTSManager:
    """
    Production-safe TTS pipeline:
      1. Pre-cached offline SOP audio (guaranteed zero latency)
      2. Licensed Cloud TTS (if enterprise keys configured)
      3. Local offline TTS (macOS / Linux native)
    """

    def __init__(self):
        self.precached_provider = PreCachedSOPAudioProvider()
        self.cloud_provider = LicensedCloudTTSProvider()
        self.offline_provider = LocalOfflineTTSProvider()

    def synthesize(self, text: str, language: str = "hi", out_path: Path | None = None) -> bool:
        if not text or not text.strip():
            return False

        if out_path is None:
            clean = text.strip()
            hash_key = hashlib.md5(f"{language}:{clean}".encode("utf-8")).hexdigest()[:16]
            out_path = PRECACHED_SOP_DIR / f"tts_{hash_key}.wav"

        # Tier 1: Check Pre-Cached Standard SOP audio
        if self.precached_provider.synthesize(text, language, out_path):
            return True

        # Tier 2: Licensed Cloud TTS
        if self.cloud_provider.synthesize(text, language, out_path):
            return True

        # Tier 3: Local Offline TTS
        if self.offline_provider.synthesize(text, language, out_path):
            return True

        return False


_TTS_MANAGER: CompositeTTSManager | None = None


def get_tts_manager() -> CompositeTTSManager:
    global _TTS_MANAGER
    if _TTS_MANAGER is None:
        _TTS_MANAGER = CompositeTTSManager()
    return _TTS_MANAGER
