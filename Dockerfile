 # Multi-stage build for AI Pneumonia Detection System
 # Stage 1: Build stage with all dependencies
 FROM python:3.9-slim as builder
 
 # Set build arguments
 ARG MODEL_VERSION=1.0
 ARG BUILD_DATE
 ARG VCS_REF
 
 # Set metadata labels
 LABEL maintainer="AI Development Team <dev@pneumonia-ai.com>" \
       org.opencontainers.image.title="AI Pneumonia Detection System" \
       org.opencontainers.image.description="AI-powered pneumonia detection from chest X-rays" \
       org.opencontainers.image.version="${MODEL_VERSION}" \
       org.opencontainers.image.created="${BUILD_DATE}" \
       org.opencontainers.image.revision="${VCS_REF}" \
       org.opencontainers.image.source="https://github.com/yourusername/pneumonia-detector"
 
 # Install system dependencies
 RUN apt-get update && apt-get install -y \
     gcc \
     g++ \
     libgl1-mesa-glx \
     libglib2.0-0 \
     libsm6 \
     libxext6 \
     libxrender-dev \
     libgomp1 \
     libgcc-s1 \
     && rm -rf /var/lib/apt/lists/*
 
 # Set working directory
 WORKDIR /app
 
 # Copy requirements first for better caching
 COPY requirements.txt .
 
 # Install Python dependencies
 RUN pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir -r requirements.txt
 
 # Stage 2: Production stage
 FROM python:3.9-slim as production
 
 # Install runtime dependencies only
 RUN apt-get update && apt-get install -y \
     libgl1-mesa-glx \
     libglib2.0-0 \
     libsm6 \
     libxext6 \
     libxrender-dev \
     libgomp1 \
     && rm -rf /var/lib/apt/lists/* \
     && apt-get clean
 
 # Create non-root user for security
 RUN groupadd -r pneumonia && useradd -r -g pneumonia pneumonia
 
 # Set working directory
 WORKDIR /app
 
 # Copy Python packages from builder stage
 COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
 COPY --from=builder /usr/local/bin /usr/local/bin
 
 # Copy application code
 COPY . .
 
 # Create necessary directories and set permissions
 RUN mkdir -p /app/uploads /app/logs /app/models && \
     chown -R pneumonia:pneumonia /app
 
 # Copy model file (if available)
 # COPY pneumonia_cnn_model.h5 /app/models/
 
 # Set environment variables
 ENV PYTHONPATH=/app \
     PYTHONUNBUFFERED=1 \
     FLASK_ENV=docker \
     PORT=5000 \
     WORKERS=4 \
     TIMEOUT=120
 
 # Expose port
 EXPOSE 5000
 
 # Health check
 HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:5000/api/health || exit 1
 
 # Switch to non-root user
 USER pneumonia
 
 # Start application with gunicorn
 CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS --timeout $TIMEOUT --access-logfile - --error-logfile - app:app"]