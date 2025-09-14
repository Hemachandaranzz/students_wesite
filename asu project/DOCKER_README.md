# ASU Project - Docker Deployment

This document provides instructions for running the ASU Project using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)

## Quick Start

### Method 1: Using Docker Compose (Recommended)

1. **Clone and navigate to the project directory:**
   ```bash
   cd "asu project"
   ```

2. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Open your browser and go to `http://localhost:5000`

### Method 2: Using Docker directly

1. **Build the Docker image:**
   ```bash
   docker build -t asu-project .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/logs:/app/logs asu-project
   ```

3. **Access the application:**
   - Open your browser and go to `http://localhost:5000`

## Environment Variables

Create a `.env` file in the project root with your configuration:

```env
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# Optional: Custom port
PORT=5000
```

## Docker Commands

### Build the image
```bash
docker build -t asu-project .
```

### Run the container
```bash
docker run -d -p 5000:5000 --name asu-app asu-project
```

### View logs
```bash
docker logs asu-app
```

### Stop the container
```bash
docker stop asu-app
```

### Remove the container
```bash
docker rm asu-app
```

### Remove the image
```bash
docker rmi asu-project
```

## Docker Compose Commands

### Start services
```bash
docker-compose up
```

### Start services in background
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs
```

### Rebuild and start
```bash
docker-compose up --build
```

## Features Included

- ✅ **Flask Web Application** with all features
- ✅ **Voice Assistant** with speech recognition
- ✅ **AI Chat** with Gemini integration
- ✅ **Document Processing** (PDF, DOCX, TXT)
- ✅ **YouTube Suggestions** with AI
- ✅ **Flashcard Generator** with AI
- ✅ **MCQ Generator** with AI
- ✅ **Text-to-Speech** with GTTS
- ✅ **Production-ready** with Gunicorn

## Production Deployment

For production deployment, consider:

1. **Use environment variables** for sensitive data
2. **Set up reverse proxy** (nginx) for better performance
3. **Use Docker secrets** for API keys
4. **Monitor logs** and set up logging
5. **Use Docker Swarm or Kubernetes** for scaling

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port in docker-compose.yml or use different port
   docker run -p 8080:5000 asu-project
   ```

2. **Permission issues:**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER uploads/ logs/
   ```

3. **API key not working:**
   - Check your `.env` file
   - Ensure `GEMINI_API_KEY` is set correctly

### View container logs
```bash
docker logs asu-app -f
```

### Access container shell
```bash
docker exec -it asu-app /bin/bash
```

## Health Check

The application includes a health check that verifies the service is running:
- **Endpoint:** `http://localhost:5000/`
- **Interval:** 30 seconds
- **Timeout:** 30 seconds
- **Retries:** 3

## Volumes

The following directories are mounted as volumes:
- `./uploads` → `/app/uploads` (file uploads)
- `./logs` → `/app/logs` (application logs)

This ensures data persistence across container restarts.
