# Multi-architecture base
FROM --platform=$BUILDPLATFORM python:3.9-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip supervisor && \
    rm -rf /var/lib/apt/lists/*

# Set versions
ENV PROMETHEUS_VERSION=2.47.0
ENV GRAFANA_VERSION=10.2.3

# Install Prometheus (auto-detect arch)
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
    "amd64") DL_SUFFIX="linux-amd64" ;; \
    "arm64") DL_SUFFIX="linux-arm64" ;; \
    *) echo "Unsupported arch"; exit 1 ;; \
    esac && \
    wget -q https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.${DL_SUFFIX}.tar.gz && \
    tar xfz prometheus-*.tar.gz && \
    mv prometheus-${PROMETHEUS_VERSION}.${DL_SUFFIX} /prometheus && \
    rm prometheus-*.tar.gz

# Install Grafana
RUN wget -q https://dl.grafana.com/oss/release/grafana-${GRAFANA_VERSION}.linux-${TARGETARCH}.tar.gz && \
    tar xfz grafana-*.tar.gz && \
    mv grafana-${GRAFANA_VERSION} /grafana && \
    rm grafana-*.tar.gz

# Install Python requirements
COPY exporter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy configurations
COPY exporter/exporter.py /app/
COPY prometheus/prometheus.yml /prometheus/
COPY grafana/provisioning/ /grafana/conf/provisioning/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directories
RUN mkdir -p /var/log/supervisor && \
    mkdir -p /prometheus/data && \
    mkdir -p /grafana/data

# Expose ports
EXPOSE 8118 9090 3000

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]