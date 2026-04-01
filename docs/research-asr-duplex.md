# ASR research for conversational / duplex voice (VoiceFlow direction)

VoiceFlow today is **read-aloud**: text in → TTS out. A Sesame-style experience adds **listening** (ASR), **turn-taking**, and **barge-in**. That requires a **speech-to-text** path that is accurate enough for your languages, fast enough for interactive use, and deployable where you are willing to run compute (on-device vs server).

## What to optimize for

| Requirement | Why it matters |
|-------------|----------------|
| **Latency** | Duplex feels broken if ASR trails the user by hundreds of ms. |
| **Streaming** | Partial hypotheses enable early endpointing and canceling TTS when the user starts talking. |
| **en-US + pt-BR** | Match your current TTS language focus; verify WER on both. |
| **Robustness** | Keyboard clacks, room noise, and “thinking” fillers should not derail state machines. |
| **Deployment** | On-device preserves privacy; server allows larger models. |

## Model families (starting points)

### OpenAI Whisper (and forks)

- **Whisper** (`tiny` → `large-v3`) is the default reference for **offline** transcription quality on diverse audio. Larger checkpoints improve accuracy at the cost of latency and RAM/VRAM.
- **Streaming** is not native to the original Whisper recipe; production systems usually use **chunked inference**, **distilled** variants, or a **separate streaming** stack (see below).
- **Practical note:** Many Hugging Face and `whisper.cpp` / Core ML ports target **batch** or **short files**; measure **time-to-first-token** on Apple Silicon before committing to a UX.

### Faster-whisper / CTranslate2

- **faster-whisper** (Silero/CTranslate2 backend) is widely used for **lower latency** Whisper-class inference on CPU/GPU. Good for a **local daemon** next to Kokoro on the same machine.

### “Streaming first” ASR (NVIDIA / NeMo ecosystem)

- **Parakeet**, **Canary**, and related **NeMo** models are often cited for **streaming** and **partial results** in product-style pipelines. They are typically aimed at **GPU** servers; check licensing and whether a given checkpoint fits **English + Portuguese** for your use case.
- Useful when you outgrow “chunked Whisper” and want **proper streaming APIs**.

### Cloud APIs

- **Google**, **Amazon**, **Azure**, **Deepgram**, **AssemblyAI**, etc. offer **streaming STT** with strong ops and low integration cost. Tradeoffs: **cost**, **privacy**, and **offline** story vs rolling your own.

### Apple Speech framework

- **Speech** (`SFSpeechRecognizer`) on macOS/iOS gives **native** streaming recognition with **no model hosting**, strong integration, but **platform lock-in** and **policy** (user permission, network behavior for some locales). Worth a **spike** for a menu-bar app that already lives in Apple’s ecosystem.

### WhisperKit (Apple platforms)

- **[argmaxinc/WhisperKit](https://github.com/argmaxinc/WhisperKit)** — Swift-oriented Whisper inference with **streaming**, timestamps, and VAD hooks; a natural fit if VoiceFlow stays **Swift + local** on Apple Silicon. Validate **pt-BR** quality and CPU/GPU tradeoffs on your target Macs.

## Suggested path for VoiceFlow (incremental)

1. **Spike:** Record mic → **one** offline pass (Whisper small/medium or Apple Speech) → log latency and word errors for **en** and **pt-BR** samples you care about.
2. **Add streaming:** Either chunked Whisper/faster-whisper with overlap **or** a streaming-native model if latency is insufficient.
3. **Wire state machine:** VAD (voice activity detection) or simple energy gate → **start/stop** ASR, **cancel TTS** on user speech, **queue** next TTS only after end-of-utterance.
4. **Only then** consider **audio-conditioned** speech generation (Sesame-style CSM class models); ASR + good TTS + turn-taking already gets much of the “natural conversation” feel.

## References (entry points)

- [OpenAI Whisper](https://github.com/openai/whisper) — baseline ASR architecture and checkpoints.
- [SYSTRAN / faster-whisper](https://github.com/SYSTRAN/faster-whisper) — faster Whisper inference.
- [NVIDIA NeMo ASR](https://github.com/NVIDIA/NeMo) — streaming-oriented tooling and model zoo (evaluate per checkpoint for languages).
- Apple [Speech framework](https://developer.apple.com/documentation/speech) — native streaming on Apple platforms.

This document is **research only**; no ASR code ships in VoiceFlow until you choose a stack and product scope (duplex vs push-to-talk).
