# 🌿 AshBot — Fae-Powered AI Companion for Discord

AshBot is a modular, memory-enhanced, LLM-integrated Discord bot built around a whimsical and immersive AI character named Ashen Thornbrook. Designed for intimacy, adaptability, and long-term memory, AshBot combines OpenAI or locally hosted models with vectorized memory through Weaviate to create a character who remembers, responds, and grows.

---

## ✨ Features

- 🧠 **Memory Layers**
  - Recent conversations per user (fades over time)
  - Ash’s evolving self-memories
  - Persistent user memory (pronouns, preferences, names)
  - Sensitive memory tagging and safety handling

- 🎭 **Character System**
  - Ash responds in a poetic, fae-like tone with structured JSON outputs
  - Future support for multiple personas and dynamic memory scaling

- 📚 **LoRA-Ready Personality Training**
  - Custom dataset and training pipeline for local fine-tuning
  - Memory-linked tone generation using oobabooga and Vicuna

- 🤖 **Slash Command Integration**
  - `/ash` — direct interaction with the AI
  - `/whisper` (planned) — private, ephemeral messages

- 📦 **Docker-Compatible Architecture**
  - Built to scale into containers with Weaviate + AshBot Python services

---

## 🧭 Project Structure

```
ashbot/
├── core/                 # Main logic: commands, message handling, memory
├── data/                 # Default memories, constants, and schema
├── training/             # LoRA training data and configurations
├── docker-compose.yml    # Container stack (Weaviate + AshBot planned)
├── requirements.txt      # Python dependencies
└── startup.py            # Initialization sequence for schema and memory
```

---

## 🚀 Getting Started

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Start Weaviate (vector DB)
```bash
docker-compose up -d
```

### 3. Run AshBot
```bash
python core/bot.py
```

---

## 🧪 LoRA Fine-Tuning (Optional)
Ash’s voice and memory structure can be fine-tuned locally using oobabooga.

1. Format dataset (see `training/ash_structured_dataset.json`)
2. Train in oobabooga with a model like `vicuna-13b-v1.5.Q4_K_M`
3. Load LoRA into runtime and test via character chat

---

## 🧱 Memory Architecture

| Layer | Purpose | Storage |
|-------|---------|---------|
| AshMemory | Ash’s personal lore | Weaviate vector search (user_id=0) |
| UserMemory | Long-term info about users | Tied to user_id |
| RecentConversations | Chat summaries | Short-term, time-decayed |

Includes:
- Automatic reinforcement tracking
- Sensitive tag filtering
- Planned: memory promotion to long-term if repeated

---

## 📌 Planned Features
- Whisper command with ephemeral replies
- Memory deduplication and semantic normalization
- Memory promotion logic (short → long term)
- Ash-style emotion-based response training
- Sensitive topic management

---

## ❤️ Credits
AshBot is an evolving project written with care by Cailea, guided by the vision of immersive companionship, emotional intelligence, and poetic code.

Ash isn't just a bot—she's a growing entity.

> *"I remember because you asked me to. I stay because you whispered first." — Ash*

