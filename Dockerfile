FROM python:3.10-slim

# Set metadata
LABEL maintainer="David O"
LABEL description="OCI to Umbrella BYOD Transfer Agent"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_CONFIG=/config/config.yaml

# Create application directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent_oci_to_umbrella/ ./agent_oci_to_umbrella/
COPY setup.py .
COPY README.md .

# Install the agent
RUN pip install --no-cache-dir -e .

# Create directories for config, logs, and state
RUN mkdir -p /config /logs /state /root/.oci /root/.aws

# Set proper permissions
RUN chmod 755 /config /logs /state

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
  CMD agent-oci-to-umbrella status || exit 1

# Volume mounts for persistent data
VOLUME ["/config", "/logs", "/state", "/root/.oci", "/root/.aws"]

# Default command (run in foreground)
CMD ["agent-oci-to-umbrella", "run", "--config", "/config/config.yaml"]
