# API Documentation

## Base URL
- Development: `http://localhost:5001`
- Production: TBD

## Endpoints

### Health Check
**GET** `/api/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "whisper_available": true
}
```

### Speech Transcription
**POST** `/api/transcribe`

Transcribe audio to text using Whisper ASR.

**Rate Limit:** 10 requests per minute

**Request:**
- Content-Type: `multipart/form-data`
- Body: `audio` (file) - Audio file (mp3, wav, m4a, etc.)

**Response:**
```json
{
  "text": "transcribed text",
  "language": "en",
  "success": true
}
```

### Translation
**GET/POST** `/parser`

Translate English text to ISL.

**Parameters:**
- `speech` (GET) or `text` (POST): English text to translate

**Response:**
```json
{
  "isl_text_string": "translated isl text",
  "pre_process_string": "preprocessed text"
}
```

### Annotations
**POST** `/api/annotations`

Add translation pair annotation.

**Rate Limit:** 20 requests per minute

**Request Body:**
```json
{
  "english_text": "Hello",
  "isl_text": "hello",
  "isl_gloss": "hello",
  "sigml_file": "hello.sigml"
}
```

**Response:**
```json
{
  "id": 1,
  "success": true
}
```

### Feedback
**POST** `/api/feedback`

Submit user feedback on translations.

**Rate Limit:** 30 requests per minute

**Request Body:**
```json
{
  "translation_pair_id": 1,
  "feedback_type": "user_correction",
  "is_correct": false,
  "corrected_text": "corrected text",
  "comments": "optional comments"
}
```

**Response:**
```json
{
  "id": 1,
  "success": true
}
```

### Evaluation Metrics
**GET** `/api/evaluation/metrics`

Get current model evaluation metrics.

**Response:**
```json
{
  "wer": 0.05,
  "bleu": 0.65,
  "accuracy": 0.95,
  "rouge_l": 0.70
}
```

## Error Responses

All errors follow this format:
```json
{
  "error": "Error message",
  "message": "Detailed message"
}
```

**Status Codes:**
- 200: Success
- 400: Bad Request
- 404: Not Found
- 429: Rate Limit Exceeded
- 500: Internal Server Error
- 503: Service Unavailable

