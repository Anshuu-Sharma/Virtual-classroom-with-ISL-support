# Deployment Guide

## Local Development

### Prerequisites
- Python 3.9+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download Stanford Parser (if using rule-based translation):
```bash
# Download from: https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip
# Extract to AudioToSignLanguageConverter/ directory
```

3. Run server:
```bash
python server.py
```

4. Open browser:
```
http://localhost:5001
```

## Docker Deployment

### Build Image

```bash
docker build -t sign-language-converter .
```

### Run Container

```bash
docker run -p 5001:5001 sign-language-converter
```

### Docker Compose

Development:
```bash
docker-compose up
```

Production:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured

### Deploy

1. Create persistent volumes:
```bash
kubectl apply -f k8s/pvc.yaml
```

2. Deploy application:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

3. Check status:
```bash
kubectl get pods -l app=sign-language-converter
kubectl get services
```

### Access Application

Get service URL:
```bash
kubectl get service sign-language-converter-service
```

## Environment Variables

- `FLASK_ENV`: `development` or `production`
- `PYTHONUNBUFFERED`: `1`
- `CUDA_VISIBLE_DEVICES`: GPU device IDs (optional)

## Resource Requirements

### Minimum
- CPU: 1 core
- Memory: 2GB
- Disk: 5GB

### Recommended
- CPU: 2 cores
- Memory: 4GB
- Disk: 10GB
- GPU: Optional (for faster inference)

## Monitoring

Health check endpoint:
```
GET /api/health
```

Evaluation dashboard:
```
http://localhost:5001/evaluation-dashboard
```

## Scaling

### Docker Compose
Edit `docker-compose.yml` to add more replicas.

### Kubernetes
```bash
kubectl scale deployment sign-language-converter --replicas=3
```

