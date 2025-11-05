# Data Collection Guide

## Overview

This guide explains how to collect and annotate data for training the translation model.

## Data Collection Tools

### Web Annotation Tool

Access the annotation tool at:
```
http://localhost:5001/annotation-tool
```

Features:
- Add English-ISL translation pairs
- Provide feedback on translations
- View existing annotations

### API Endpoints

#### Add Translation Pair

```bash
curl -X POST http://localhost:5001/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "english_text": "Hello",
    "isl_text": "hello",
    "isl_gloss": "hello",
    "sigml_file": "hello.sigml"
  }'
```

#### Add Feedback

```bash
curl -X POST http://localhost:5001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "translation_pair_id": 1,
    "is_correct": false,
    "corrected_text": "corrected text",
    "comments": "Better translation needed"
  }'
```

## Data Sources

### Existing SiGML Files

The system automatically uses existing SiGML files from `SignFiles/` directory.

### Manual Annotation

Use the web annotation tool or API to add new translation pairs.

### User Feedback

Collect feedback from users:
- Correct/incorrect translations
- Corrections
- Comments

## Data Format

### Translation Pairs

```json
{
  "english": "Hello world",
  "isl": "hello world"
}
```

### Database Schema

Translation pairs are stored in SQLite database:
- `data/training_data.db`

Tables:
- `audio_samples`: Audio files and transcripts
- `translation_pairs`: English-ISL pairs
- `user_feedback`: User corrections
- `annotations`: Additional annotations

## Exporting Data

Export translation pairs for training:

```python
from ml_pipeline.data_collector import DataCollector

collector = DataCollector()
collector.export_to_json("data/exported_pairs.json", verified_only=True)
```

## Data Quality

### Verification

- Mark pairs as verified after review
- Use verified pairs for training
- Review user feedback regularly

### Best Practices

1. **Consistency**: Use consistent ISL gloss format
2. **Completeness**: Include all necessary words
3. **Accuracy**: Verify translations with native speakers
4. **Coverage**: Collect diverse sentence types

## Active Learning

The system supports active learning:
- Identify low-confidence predictions
- Prioritize user corrections
- Build dataset incrementally

## Data Privacy

- Store user data securely
- Anonymize user IDs
- Follow data protection regulations

