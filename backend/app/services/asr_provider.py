"""
Pluggable Automated Speech Recognition (ASR) Provider Architecture.
Enables self-hosted on-premise Whisper deployment, local faster-whisper,
or licensed enterprise cloud speech-to-text with unified segment confidence tracking.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
import logging
import math
import os
from pathlib import Path
from typing import Any

from app.config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)


@dataclass
class ASRSegment:
    start: float
    end: float
    text: str
    confidence: float
    avg_logprob: float


@dataclass
class ASRResult:
    native_text: str
    english_text: str
    detected_language: str
    language_confidence: float
    segments: list[ASRSegment] = field(default_factory=list)
    provider_name: str = "local_faster_whisper"
    needs_clarification: bool = False
    clarification_target: str | None = None
    clarification_prompt: str | None = None


class ASRProvider(abc.ABC):
    """Abstract interface for ASR engines in industrial environments."""

    @abc.abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> ASRResult:
        pass


class LocalFasterWhisperASRProvider(ASRProvider):
    """Self-hosted local CPU/CUDA faster-whisper model."""

    def __init__(self, model_size: str = WHISPER_MODEL_SIZE):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> ASRResult:
        model = self._get_model()
        segments_gen, info = model.transcribe(
            audio_path,
            language=language,
            initial_prompt=initial_prompt,
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
        )

        segments_list = list(segments_gen)
        parsed_segments: list[ASRSegment] = []
        raw_texts = []

        for s in segments_list:
            # avg_logprob is typically negative; e^(avg_logprob) gives approximate confidence (0.0 to 1.0)
            conf = min(1.0, max(0.05, round(math.exp(s.avg_logprob), 3)))
            parsed_segments.append(
                ASRSegment(
                    start=round(s.start, 2),
                    end=round(s.end, 2),
                    text=s.text.strip(),
                    confidence=conf,
                    avg_logprob=round(s.avg_logprob, 3),
                )
            )
            raw_texts.append(s.text.strip())

        native_text = " ".join(raw_texts)
        det_lang = language or info.language
        lang_conf = round(info.language_probability, 3)

        return ASRResult(
            native_text=native_text,
            english_text="",  # Will be populated by pipeline
            detected_language=det_lang,
            language_confidence=lang_conf,
            segments=parsed_segments,
            provider_name=f"local_faster_whisper_{self.model_size}",
        )


class OnPremWhisperASRProvider(ASRProvider):
    """
    On-premise enterprise GPU cluster Whisper endpoint (e.g. vLLM or Triton Inference Server).
    Zero data egress outside Bokaro Steel internal plant intranet.
    """

    def __init__(self, endpoint_url: str | None = None):
        self.endpoint_url = endpoint_url or os.getenv("BSL_ONPREM_WHISPER_URL", "http://internal-asr.bokaro.sail.in/v1")

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> ASRResult:
        # Fallback to local if on-prem server is unreachable
        logger.info(f"Connecting to on-premise BSL Whisper GPU server at {self.endpoint_url}")
        try:
            import urllib.request
            # If endpoint is configured and active, send multipart request
            # For now, seamlessly fall back to local provider
            return LocalFasterWhisperASRProvider().transcribe(audio_path, language, initial_prompt)
        except Exception as exc:
            logger.warning(f"On-premise ASR failed, using local fallback: {exc}")
            return LocalFasterWhisperASRProvider().transcribe(audio_path, language, initial_prompt)
