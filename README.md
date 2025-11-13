# Virtual Classroom with Indian Sign Language Support

End-to-end platform that converts classroom audio into Indian Sign Language (ISL) animations so Deaf and Hard-of-Hearing learners can follow lessons in real time. The workspace combines browser-based avatar playback, modern speech recognition, a trainable translation pipeline, and deployment tooling designed for research projects and production pilots.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Data Flow](#architecture--data-flow)
3. [Subsystem Deep Dive](#subsystem-deep-dive)
4. [Technology Stack](#technology-stack)
5. [Environment Setup](#environment-setup)
6. [Operating the Platform](#operating-the-platform)
7. [Failure Handling & Fallbacks](#failure-handling--fallbacks)
8. [Data, Models, and Assets](#data-models-and-assets)
9. [Scripts & Automation](#scripts--automation)
10. [Documentation Map](#documentation-map)
11. [Visual Guides & Examples](#visual-guides--examples)
12. [Testing & Monitoring](#testing--monitoring)
13. [Roadmap & Contributions](#roadmap--contributions)
14. [Support](#support)

---

## System Overview

- **Goal**: Deliver speech-to-sign translation for classrooms with a responsive 3D avatar and tooling to improve accuracy over time.
- **Primary Flow**: Audio → Whisper ASR → Translation (ML or rule-based) → ISL gloss sequence → SiGML playback → Avatar animation.
- **Audience**: Researchers, educators, and developers exploring ISL accessibility solutions.

Key capabilities:
- Runs locally, in Docker, or on Kubernetes clusters.
- Collects new dataset pairs and user feedback to continuously retrain translation models.
- Supports both automatic speech recognition (ASR) and text input modes.
- Provides dashboards, health checks, and logging for classroom operations.

---

## Architecture & Data Flow

```
Microphone / Uploaded Audio
          │
          ▼
   `services/asr_service.py`
    Whisper ASR (PyTorch)
          │ text + segments
          ▼
   `server.py` translation router
    ├─ `services/translation_service.py` (LSTM Seq2Seq, optional)
    ├─ Stanford Parser (rule-based fallback)
    └─ Token heuristics (last fallback)
          │ ISL tokens
          ▼
   `services/isl_mapper.py`
    Gloss mapping via `js/sigmlFiles.json`
          │ gloss list
          ▼
   Browser (`index.html`, `js/handler.js`)
    ├─ Fetch SiGML from `SignFiles/`
    ├─ Fetch cached HamNoSys JSON from `hamnosysData/`
    └─ Play `avatars/marc.jar` via CWASA
```

Data pipelines support:
- Continuous logging and health reporting via `monitoring/`.
- Dataset growth using `ml_pipeline/data_collector.py`.
- Offline training and evaluation through `ml_pipeline/` and `scripts/`.

---

## Subsystem Deep Dive

### 1. Backend Services (`server.py`, `services/`, `monitoring/`)
- **Flask API Gateway** (`server.py`)
  - Routes: `/api/transcribe`, `/parser`, `/api/annotations`, `/api/feedback`, `/api/evaluation/metrics`, `/api/system/health`, static asset serving.
  - Rate limiting via `flask_limiter`.
  - Graceful degradations (e.g., rule-based translation if ML model missing).
- **ASR Layer** (`services/asr_service.py`, `services/audio_processor.py`)
  - Whisper model loaded lazily with CUDA detection and FFmpeg-based preprocessing.
  - Supports local files and base64 payloads; returns transcripts and segments.
- **Translation Layer** (`services/translation_service.py`)
  - Prefers ML translator if files exist in `models/`.
  - Confidence heuristics prevent degraded ML outputs from reaching the avatar.
  - Fallback path leverages Stanford Parser (`StanfordParser` via NLTK); if Java fails, tokenizes input to keep UX intact.
  - Stop-word filtering and lemmatization ensure an avatar-friendly gloss list (`filter_stop_words`, `lemmatize_tokens`).
- **ISL Mapping** (`services/isl_mapper.py`)
  - Loads 800+ entries from `js/sigmlFiles.json`.
  - Finds best-fit gloss per token, with suffix handling and compound-word heuristics.
- **Health & Metrics** (`monitoring/health_check.py`, `monitoring/metrics.py`)
  - CPU/memory usage, Whisper availability, database checks.
  - Persisted metric history (`data/metrics.json`, `data/latest_metrics.json`) for dashboards.

### 2. Frontend & Avatar (`index.html`, `js/`, `css/`, `avatars/`, `SignFiles/`)
- **Dashboard UI** (`index.html`, `css/custom.css`)
  - Materialize CSS + custom components for transcripts, avatar, and queue status.
  - Live transcript panel shows ASR results; ISL panel shows final gloss sequence.
- **Interaction Logic** (`js/handler.js`)
  - Coordinates continuous listening,  Web Speech fallback, queue management.
  - Visual loader states for listening/processing.
  - Drives avatar by requesting SiGML/HamNoSys and pushing to CWASA player.
- **Avatar Assets**
  - `avatars/marc.jar` and `avatars/marc/` contain CWASA avatar definitions, textures, shaders.
  - `SignFiles/*.sigml` store pre-authored signs.
  - `hamnosysData/*.txt` caches generated AnimGen frames to avoid remote dependencies.
- **Fallback UX**
  - Unmapped words are auto-spelled letter-by-letter (`pre_process` in `server.py`).
  - `HOW_AVATAR_SIGNS_WORK.md` explains manual sign library usage.

### 3. ML Pipeline (`ml_pipeline/`, `scripts/`, `kaggle_notebooks/`)
- **Data Ingestion** (`ml_pipeline/data_collector.py`)
  - SQLite database (`data/training_data.db`) capturing audio samples, translation pairs, feedback, annotations.
  - REST endpoints feed this collector during runtime.
- **Dataset Prep** (`ml_pipeline/datasets/isl_dataset.py`)
  - Encodes pairs using vocabularies; handles padding and max-length constraints.
- **Model Definition** (`ml_pipeline/models/translator.py`)
  - Bidirectional LSTM encoder + decoder with attention-ready architecture.
  - Teacher forcing and inference loops optimized for short sequences.
- **Training Harness** (`ml_pipeline/models/translation_trainer.py`)
  - Gradient clipping, ReduceLROnPlateau scheduler, checkpointing, early stopping.
  - Saves best weights to `models/lstm_translator.pth`.
- **Config & Utilities** (`ml_pipeline/config.py`, `ml_pipeline/utils/vocab.py`)
  - Centralizes hyperparameters, file paths, Kaggle directories.
  - Flexible vocabulary builder with special tokens and min-frequency filtering.
- **Notebooks & Scripts**
  - `kaggle_notebooks/train_isl_model_complete.py`, `kaggle_notebooks/README.md`.
  - CLI helpers: `scripts/train_translation_model.py`, `scripts/evaluate_models.py`, `scripts/create_*_training_data.py`, Kaggle upload/download automations.

### 4. Documentation & Reports (`docs/`, `final report minor.pdf`)
- Step-by-step guides for API usage, data collection, deployment, Kaggle setup, and training.
- Visual reference assets in `images/` (system workflow diagram, demo screenshots).
- Academic report summarizing research outcomes.

---

## Technology Stack

- **Speech Recognition**: OpenAI Whisper (PyTorch) chosen for accuracy, multi-format support, and offline capability.
- **Translation**:
  - LSTM Seq2Seq model for adaptive learning.
  - Stanford Parser for deterministic fallback and explainable syntax handling.
- **Avatar Rendering**: CWASA toolkit with Java-based avatar (Marc) to deliver expressive ISL animations; uses SiGML standard for sign encoding.
- **Storage**:
  - SQLite for lightweight annotation persistence.
  - JSON vocabularies and metrics for portability.
- **Runtime**: Python 3.9+, Flask, `flask-limiter`, `flask-cors`.
- **Ops**: Docker, docker-compose, Kubernetes manifests, psutil-based health probes.
- **Tooling**: FFmpeg (audio conversion), NLTK (lemmatization), TQDM (training progress).

---

## Environment Setup

### Prerequisites
- Python 3.9+
- pip / virtualenv (or conda)
- FFmpeg (required for Whisper)
- Java JDK 8+ (Stanford Parser fallback)
- Optional: Docker, docker-compose, kubectl, Kaggle CLI

### Local Installation

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng'); nltk.download('wordnet')"
```

Run the server:
```bash
python server.py
# visit http://localhost:5001
```

### Quick Start Scripts
- `scripts/setup.sh` / `scripts/setup.bat`: install dependencies, verify prerequisites.
- `scripts/quick_start.py`: interactive assistant to set up env, test Whisper, and launch.
- `scripts/run.bat`: run server on Windows.

### Docker & Kubernetes
- Build locally: `docker build -t isl-classroom .`
- Compose (dev): `docker-compose up`
- Compose (prod): `docker-compose -f docker-compose.prod.yml up -d`
- Kubernetes: `kubectl apply -f k8s/` (includes PVC, Deployment, Service). Scale with `kubectl scale deployment sign-language-converter --replicas=3`.

### Kaggle GPU Training
1. Prepare data: `python scripts/prepare_training_data.py`
2. Package dataset: `python scripts/create_kaggle_dataset.py`
3. Upload via Kaggle CLI or web UI.
4. Run `kaggle_notebooks/train_translation_model_complete.py` notebook with GPU enabled.
5. Download `models/lstm_translator.pth`, `models/vocab_src.json`, `models/vocab_tgt.json` and replace the local files.

---

## Operating the Platform

1. **Start services** (`python server.py` or containerized deployment).
2. **Open UI** (`http://localhost:5001`): use microphone control to start/stop listening.
3. **Observe panels**: live transcript, ISL output, playback queue, loader states.
4. **Avatar playback**: `SignFiles/*.sigml` streamed to CWASA player, `hamnosysData` ensures offline caching.
5. **Annotation Tool** (`/annotation-tool`): curate new translation pairs and flag corrections.
6. **Evaluation Dashboard** (`/evaluation-dashboard`, `/ml-comparison`): compare metrics, inspect outputs.
7. **APIs**: integrate external clients via documented endpoints (see `docs/API.md`).

---

## Failure Handling & Fallbacks

| Scenario | Detection | Fallback Path | User Impact |
|----------|-----------|---------------|-------------|
| Whisper fails (missing FFmpeg, CUDA error, model absent) | `WHISPER_AVAILABLE` flag and runtime exceptions | Return 503 with actionable message; frontend switches to Web Speech API | Slightly lower ASR accuracy, still functional |
| ML translator unavailable or low confidence | `translation_service.use_ml_model` flag, `_is_ml_translation_confident` heuristic | Stanford Parser handles syntax; if Java missing, plain tokenization | Gloss order may degrade, avatar still spells words |
| Missing SiGML file | `ISLMapper` returns `None` | `pre_process` converts unknown word to finger-spelling | Avatar spells word character-by-character |
| AnimGen service unreachable | `/animgen` proxy serves cached frames from `hamnosysData/` | No external dependency, playback continues | None |
| Database offline / missing | `monitoring.health_check.check_service_health` | API responds with `degraded` status; annotations stored in memory until resolved | Admin alerted via health endpoints |
| High latency / overload | Rate limiting via `flask_limiter` | Requests throttled with 429 | Protects server stability |

Logging and error messaging encourage operators to install missing dependencies or retrain models as needed.

---

## Data, Models, and Assets

- **Models (`models/`)**
  - `lstm_translator.pth`: Seq2Seq weights (optional).
  - `vocab_src.json`, `vocab_tgt.json`: vocabularies for encoder/decoder.
  - `vocab_tgt.json` currently includes 444 ISL gloss entries (see file for exact vocabulary).
- **Datasets (`data/`)**
  - `train_pairs_*.json`, `val_pairs_*.json`: curated splits.
  - `all_pairs.json`, `train_pairs_massive.json`, etc. support experiments.
  - `training_data.db`: SQLite database populated by API events.
  - `latest_metrics.json`, `metrics.json`: evaluation traces.
- **Avatar & Sign Library**
  - `SignFiles/`: 848+ SiGML files authored by experts; named after gloss entries.
  - `hamnosysData/`: cached HamNoSys-to-JSON frames (used by avatar animation engine).
  - `avatars/`: CWASA assets for “Marc” avatar, including config, non-manual markers, shaders.
  - `js/cwacfg.json`: runtime configuration for CWASA.
- **Supporting Assets**
  - `images/workflowOfProposedSystem.jpg`: architecture illustration.
  - `images/demo.mp4`: demo recording.
  - `final report minor.pdf`: academic write-up.

---

## Scripts & Automation

Category | Scripts
---------|--------
Setup & Verification | `scripts/setup.sh`, `scripts/setup.bat`, `scripts/quick_start.py`, `scripts/test_installation.py`, `scripts/verify_setup.py`
Training Data | `scripts/prepare_training_data.py`, `scripts/create_*_training_data.py`, `scripts/package_massive_dataset.py`
Model Training & Eval | `scripts/train_translation_model.py`, `scripts/evaluate_models.py`, `scripts/demo.py`
Kaggle Ops | `scripts/create_kaggle_dataset.py`, `scripts/upload_to_kaggle.py`, `scripts/download_from_kaggle.py`, `scripts/setup_kaggle.py`, notebooks in `kaggle_notebooks/`
Deployment | `scripts/deploy.sh`, `docker-compose*.yml`, `k8s/*.yaml`
Utilities | `scripts/compare_ml_vs_stanford.py`, `scripts/quick_start.py` for cross-platform demo

Refer to `scripts/README.md` for detailed usage.

---

## Documentation Map

- `docs/API.md` – Endpoint specs, payloads, and rate limits.
- `docs/TRAINING.md` – Preparing data, configuring hyperparameters, training locally or on Kaggle.
- `docs/DATA_COLLECTION.md` – Using annotation tool, feedback loop, data quality tips.
- `docs/DEPLOYMENT.md` – Local, Docker, Kubernetes workflows.
- `docs/KAGGLE_SETUP.md` – Kaggle API token setup, dataset publishing, GPU runtime tips.
- `HOW_AVATAR_SIGNS_WORK.md` – Manual explanation of sign playback pipeline.

Each document aligns with the sections above, providing step-by-step procedures once you understand the overall architecture.

---

## Visual Guides & Examples

- **System Workflow Diagram**

![Workflow of Proposed System](images/workflowOfProposedSystem.jpg)

Illustrates audio capture, ASR, translation, gloss mapping, and avatar playback components plus supporting data loops.

- **UI Snapshot**

![Classroom Interface](images/Screenshot.png)

Highlights the avatar surface, live transcripts, ISL queue, and loader states described in [Operating the Platform](#operating-the-platform).

- **End-to-End Demo**

[Demo video](images/demo.mp4) (MP4) shows Whisper transcription, translation, and avatar signing a sample sentence.

### Example 1 — Speech to Sign

Input: Teacher says, “The students are learning about photosynthesis.”

1. Whisper transcript (ASR): `The students are learning about photosynthesis.`
2. Translation output (ISL gloss): `student learn photosynthesis`
3. Avatar playback: loads `student.sigml`, `learn.sigml`, `photosynthesis.sigml`, spelling letters if a gloss is missing.

### Example 2 — REST API Call

```bash
curl -X POST http://localhost:5001/parser \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=Please schedule the next class for tomorrow"
```

Response:

```json
{
  "isl_text_string": "please schedule next class tomorrow",
  "pre_process_string": "please schedule next class tomorrow",
  "original_english": "Please schedule the next class for tomorrow"
}
```

If the ML model confidence is low, the `isl_text_string` will be the Stanford Parser result, ensuring consistent avatar signing.

### Example 3 — Collecting Feedback

```bash
curl -X POST http://localhost:5001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
        "translation_pair_id": 42,
        "feedback_type": "user_correction",
        "is_correct": false,
        "corrected_text": "student learn future class",
        "comments": "Use FUTURE marker"
      }'
```

The entry is stored in `data/training_data.db` for later review and dataset augmentation via `ml_pipeline/data_collector.py`.

### Example 4 — Training on Kaggle

```python
from ml_pipeline.config import ModelConfig
from ml_pipeline.models.translator import Seq2SeqTranslator

cfg = ModelConfig()
model = Seq2SeqTranslator(
    src_vocab_size=5000,
    tgt_vocab_size=2000,
    embed_dim=cfg.EMBED_DIM,
    hidden_dim=cfg.HIDDEN_DIM,
    num_layers=cfg.NUM_LAYERS,
    dropout=cfg.DROPOUT
)

print("Model parameters:", sum(p.numel() for p in model.parameters()))
```

Run inside the Kaggle notebook to confirm architecture before calling `scripts/train_translation_model.py`. The notebook prints losses each epoch and saves checkpoints to `/kaggle/working/models/`.

---

## Testing & Monitoring

- **Manual Testing**
  - `scripts/test_installation.py`: verifies dependencies, key imports, configuration.
  - UI manual workflow: start/stop listening, inspect transcripts, ensure avatar signs.
- **Automated Checks**
  - Model evaluation via `scripts/evaluate_models.py --translation data/test_pairs.json`.
  - Compare ML vs Stanford outputs with `scripts/compare_ml_vs_stanford.py`.
- **Runtime Monitoring**
  - `GET /api/health`: quick status (Whisper + ML availability).
  - `GET /api/system/health`: CPU, memory, service checks.
  - Dashboards: `/evaluation-dashboard`, `/ml-comparison`.
  - Logs: server console (translation steps, fallbacks, errors).

---

## Roadmap & Contributions

Opportunities to extend the platform:
- Expand ISL vocabulary and collect nuanced sentence datasets through the annotation tool.
- Improve ML translation (transformer-based models, attention explainability, on-device inference).
- Integrate automated testing for avatar playback and ASR accuracy.
- Add multi-user session management and classroom scheduling.
- Explore additional avatars or WebGL alternatives to reduce Java dependencies.

Contributions welcome via pull requests. Please include tests or evaluation runs where appropriate.

---

## Support

1. Review guides under `docs/`.
2. Inspect server logs and browser console for detailed error traces.
3. Check health endpoints for dependency issues.
4. For academic collaboration or deployment guidance, reference `final report minor.pdf` and the included diagrams in `images/`.

---

**Last Updated**: 2025  
**Maintainers**: Virtual Classroom ISL research team (derivative of work by [sahilkhoslaa](https://github.com/sahilkhoslaa/AudioToSignLanguageConverter)).
