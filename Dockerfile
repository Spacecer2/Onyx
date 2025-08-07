# JARVIS AI Assistant - Production Docker Image
FROM nvidia/cuda:12.4-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    wget \
    curl \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 jarvis && chown -R jarvis:jarvis /app
USER jarvis

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=jarvis:jarvis . .

# Create necessary directories
RUN mkdir -p jarvis/logs jarvis/photos jarvis/temp jarvis/models

# Set Python path
ENV PYTHONPATH=/app
ENV PATH=/home/jarvis/.local/bin:$PATH

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Default command
CMD ["python3", "jarvis_simple_launcher.py"]
