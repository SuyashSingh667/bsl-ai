# Voice Interview Pipeline — Design Reference

Covers the worker-facing voice interaction: initial incident report through the adaptive verification interview. This consolidates decisions made across design discussion into one reference, matching the treatment given to the spatial impact engine and RAG document set.

## Interaction model: manual stop, not auto-stop

Every voice turn — the initial free-form report and each answer during verification — follows the same pattern:

```
TTS plays the question (skipped for the very first turn — worker taps "Report Incident" directly)
        ↓
Worker taps "Record" → mic starts capturing
        ↓
Worker speaks
        ↓
Worker taps "Done" → recording stops, audio segment finalized
        ↓
faster-whisper: transcript + detected language + confidence
        ↓
(see "After transcription" below)
```

**Why manual, not VAD-based auto-stop:** a shop floor has furnace/machinery noise that makes silence-detection unreliable — voice-activity-detection (VAD) models are tuned on relatively clean speech/silence contrast and would misfire in this environment, either cutting the worker off mid-sentence or never triggering. A manual tap removes that failure mode entirely and gives the worker explicit control, which is arguably better UX for a safety report regardless of noise.

**Safety net (not VAD):** a dumb max-recording-duration timeout (~90 seconds) auto-stops and submits if the worker forgets to tap Done — e.g., they got called away mid-recording. This is a timer, not a speech model, so it doesn't reintroduce the noise-reliability problem.

## Models

| Component | Model | Notes |
|---|---|---|
| Speech-to-text + language ID | **faster-whisper** (CTranslate2 build of Whisper) | Language identification is *built into* Whisper's decoding — the encoder produces audio features, then the decoder predicts a language-token probability distribution before transcribing. No separate language-ID model is needed; one call returns transcript + detected language + confidence. |
| Regional-language fallback | **AI4Bharat IndicWhisper** | Stock Whisper's Indian-language coverage is uneven — Hindi is reasonably covered, but regional languages (Santali, Odia, etc.) are much weaker. Use IndicWhisper when the detected/expected language is one Whisper handles poorly. |
| Text-to-speech | Meta MMS-TTS (primary) or AI4Bharat Vakyansh/IndicTTS (better naturalness) | Plays back both verification questions and final RAG guidance. |
| Translation (dynamic content) | AI4Bharat IndicTrans2 | Used only for the worker's free-text speech and for translating RAG-generated guidance back to native language — never for the fixed question bank (see below). |

### Model size tradeoff (faster-whisper)

| Size | Latency | Accuracy on Hindi/regional |
|---|---|---|
| tiny/base | Fastest | Weak — not recommended for a safety report |
| **small/medium** | **Good real-time balance** | **Practical default for live interaction** |
| large-v3 | Slow for live turns | Best, especially for Hindi-English code-switching — reserve for offline re-processing of stored audio if a ticket needs higher-confidence review |

## Language handling

- **Detected once, locked for the session.** Language is identified from the initial free-form report (the longest, clearest utterance) and then held fixed for every subsequent turn in that interview — re-running detection on every short answer risks flip-flopping between similar languages under noise or code-switching.
- **Low-confidence fallback:** if detection confidence on that first utterance is low, ask a quick clarifying TTS prompt ("Are you speaking in Hindi?") rather than silently guessing and proceeding on a possibly-wrong language.
- **Fixed content vs. dynamic content**, per the platform's core safety principle (don't let translation silently reword safety-critical fixed text):
  - **Verification questions** (finite, fixed per incident category — see `verification_questions.json`) use a **pre-approved, human-reviewed translation per language**, never live machine translation.
  - **The worker's free-text speech** and **RAG-generated guidance** are unavoidably live-translated (IndicTrans2), since they're open-ended content.

## After transcription

```
Store native-language transcript (audit record — never discarded, even after translation)
        ↓
Translate to English (IndicTrans2, or Whisper's built-in "translate" task as a fallback)
        ↓
English text → DistilBERT classifier + NER extraction (parallel)
        ↓
Verification orchestrator selects next question
        ↓
Pulls that question's pre-approved translation for the locked language
        ↓
TTS → played to worker (question also shown as on-screen text)
        ↓
Loop: worker taps Record → speaks → taps Done → next transcription, same locked language
```

## Data captured per turn

Each verification turn stores, per the ticket schema:

| Field | Purpose |
|---|---|
| `question_audio_ref` | TTS audio played for this question |
| `answer_audio_ref` | Worker's recorded answer |
| `answer_transcript_native` | Whisper transcript in the detected/locked language |
| `answer_transcript_en` | Translated English text used by the classifier/verification engine |

This gives the audit trail both the original voice and its translation, not just the final English interpretation — needed if a ticket is ever disputed or reviewed by a human safety officer who wants to hear what the worker actually said.

## Final guidance delivery

Same dual-channel principle as the interview: RAG-generated precautionary guidance is shown as on-screen text (with source citation) **and** passed through TTS in the worker's locked language, so neither channel diverges from the other.
