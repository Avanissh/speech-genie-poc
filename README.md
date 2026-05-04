
---

# 🧠🔊 Speech Genie

### Adaptive Multi-Backend Conversational Speech System with Persona-Aware Dialogue & Dynamic Prosody

---

## 🚀 Overview

**Speech Genie** is a real-time conversational speech system designed to overcome the limitations of traditional TTS pipelines by combining:

* 🧠 Intent-aware response generation
* 🎭 Persona-based conversational behavior
* 🎛 Dynamic prosody control
* ⚙️ Multi-backend speech synthesis

---

## 🎯 Core Objective

To build a system that can:

* Generate **natural, human-like speech**
* Adapt **tone dynamically based on context and emotion**
* Support **voice cloning + preset voices**
* Maintain **low latency for real-time interaction**
* Provide **domain-specific conversational intelligence**

---

# 🧠 Core Philosophy

```text
WHAT to say     → Intent + Agent
HOW to behave   → Persona Engine
HOW to sound    → Prosody Engine
HOW to generate → Multi-Backend TTS
```

---

# 🧭 FULL DEVELOPMENT JOURNEY (DAY 1 → v6 PRO)

---

## 🔹 Stage 1 — Initial TTS Exploration

### Models Tested:

* XTTS v2

### Observations:

* Excellent voice cloning quality
* Extremely high latency
* Not usable for real-time systems

### Insight:

> High-quality TTS ≠ real-time usability

---

## 🔹 Stage 2 — First Working System

### Built:

* Basic pipeline: input → TTS → playback
* Single backend system

### Limitations:

* No modularity
* No flexibility
* No intelligence

---

## 🔹 Stage 3 — Modular Speech Generator

### Introduced:

* `SpeechGenerator` abstraction
* Backend switching

### Goal:

Decouple:

* generation logic
* model implementation

---

## 🔹 Stage 4 — Multi-Backend Integration

### Models Integrated:

| Model     | Purpose               |
| --------- | --------------------- |
| XTTS      | high-quality cloning  |
| Piper     | fast real-time speech |
| OpenVoice | cloning experiments   |
| StyleTTS2 | expressive speech     |
| Kokoro    | lightweight testing   |

---

### Benchmark Metrics Collected:

* ⏱ Latency
* ⚡ Real-Time Factor (RTF)
* 🎧 Output duration
* 🧠 Voice similarity

---

### Key Discovery:

> ❌ No single model satisfies:
>
> * low latency
> * high quality
> * cloning capability

---

## 🔹 Stage 5 — Hybrid Routing Architecture

### Solution:

```text
Short text → Piper
Long text  → Sopro
Fallback   → XTTS
```

### Outcome:

* Real-time performance achieved
* Quality maintained selectively

---

## 🔹 Stage 6 — Conversational Layer

### Added:

* Rule-based agent
* Interaction loop

### Problem:

* Responses felt robotic

---

## 🔹 Stage 7 — Persona Engine

### Implemented:

* 11 industry personas
* Role-based responses
* Vocabulary transformation

### Examples:

* Insurance → formal
* Hospital → empathetic
* Sales → persuasive

---

## 🔹 Stage 8 — Voice Modes

### Modes Introduced:

* Clone Mode → Sopro
* Preset Mode → Piper
* Auto Mode → dynamic routing

---

## 🔹 Stage 9 — Prosody Engine (CORE INNOVATION)

### Problem:

Speech sounded flat even with good models

---

### Solution:

Dynamic prosody system based on:

#### 🧠 Three Signals:

1. User emotion
2. Response content
3. Base tone

---

### Backend-Aware Control:

| Parameter            | Backend |
| -------------------- | ------- |
| speed / length_scale | Piper   |
| style_strength       | Sopro   |
| energy (volume)      | All     |

---

### Example:

User:

```text
"I'm frustrated"
```

System:

```text
→ Mood detected: angry  
→ Mapped to: calm/empathetic  
→ Speech: slower + softer
```

---

## 🔹 Stage 10 — STT Integration

### Implemented:

* Faster-Whisper
* Streaming audio
* Silence detection

---

### Issues:

* Latency
* Accuracy drop in noise

---

## 🔹 Stage 11 — Audio Engineering Fixes

### Problems:

* Repeated audio
* Trailing noise
* File read crashes

---

### Solutions:

* Silence trimming
* Volume normalization
* File-write stabilization
* Playback synchronization

---

## 🔹 Stage 12 — Intent System Upgrade

### Added:

* Keyword-based detection
* Weighted scoring
* Multi-response variation

---

### Fix:

Short responses like:

```text
"go on"
```

Converted to:

```text
"I'm here to help, could you tell me more?"
```

---

## 🔹 Stage 13 — Stability + Debug Phase

### Fixed:

* OpenMP crashes
* Dependency conflicts
* Sopro instability
* Prosody misclassification (urgent vs cheerful)

---

## 🔹 Stage 14 — Demo System

### Created:

* `text_demo.py`

### Purpose:

* Reliable presentation
* Controlled testing

---

# 🧱 FINAL ARCHITECTURE

```text
User Input
   ↓
Intent Detection
   ↓
Persona Engine
   ↓
Response Enhancement
   ↓
Prosody Engine
   ↓
Speech Generator (Routing)
   ↓
Backend (Piper / Sopro / XTTS)
   ↓
Audio Output
```

---

# ⚙️ CODEBASE GUIDE

---

## 📁 Structure

```text
speech_poc/
├── app/
├── core/
├── stt/
├── servers/
├── assets/
├── models/
├── sopro_env/
```

---

## 🔹 Core Modules

### `speech_pipeline.py`

Main orchestrator

---

### `speech_generator.py`

Routing + backend control

---

### `prosody_engine.py`

Emotion → speech modulation

---

### `persona_config.py`

Role definitions

---

# 🔁 PIPELINE FLOW

```text
Audio → STT → Intent → Persona → Prosody → TTS → Output
```

---

# 🧪 SETUP

---

## Main Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Sopro Environment

```bash
python -m venv sopro_env
sopro_env\Scripts\activate
pip install -r sopro_requirements.txt
```

---

## Fix OpenMP (if needed)

```bash
set KMP_DUPLICATE_LIB_OK=TRUE
```

---

# ▶️ RUN

---

### Demo (recommended)

```bash
python -m app.text_demo
```

---

### Full system

```bash
python -m app.voice_pipeline
```

---

### Clone server

```bash
python servers/sopro_server.py
```

---

# 📊 MODEL INSIGHTS

| Model | Strength     | Weakness            |
| ----- | ------------ | ------------------- |
| XTTS  | Best quality | very slow           |
| Piper | Real-time    | no cloning          |
| Sopro | CPU cloning  | unstable short text |

---

# 🔥 KEY INNOVATIONS

* Adaptive backend routing
* Dynamic prosody system
* Persona-aware dialogue
* Performance-aware architecture

---

# ⚠️ LIMITATIONS

* No LLM integration
* Limited acoustic expressiveness
* No interrupt system
* STT variability

---

# 🚀 FUTURE WORK

* Hard interrupt
* LLM integration
* Memory
* Web UI

---

# 🏁 FINAL CONCLUSION

---

## ❌ This is NOT:

* basic TTS
* simple chatbot

---

## ✅ This IS:

> A performance-aware conversational speech framework that dynamically adapts voice, tone, and backend selection.

---

# 💡 STATUS

```text
Prototype        ❌
Basic System     ❌
POC              ❌
Research System  ✅
Pre-Product      ⚡
```

---

# 🧠 FINAL NOTE

This project demonstrates:

* real-time system design
* multi-model orchestration
* human-like interaction modeling
* research-level engineering depth

---