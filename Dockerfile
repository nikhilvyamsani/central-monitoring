# syntax=docker/dockerfile:1.4
FROM ubuntu:22.04

ARG TARGETARCH
ENV ARCH=${TARGETARCH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip wget curl tar supervisor \
    && apt-get clean

# Create Prometheus user and install Prometheus
RUN useradd --no-create-home --shell /bin/false prometheus && \
    mkdir -p /etc/prometheus /prometheus && \
    cd /tmp && \
    wget https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-${ARCH}.tar.gz && \
    tar xvf prometheus-2.51.0.linux-${ARCH}.tar.gz && \
    mv prometheus-2.51.0.linux-${ARCH}/prometheus /usr/local/bin/ && \
    mv prometheus-2.51.0.linux-${ARCH}/promtool /usr/local/bin/ && \
    rm -rf prometheus-2.51.0*

# Install Grafana
RUN wget https://dl.grafana.com/oss/release/grafana_10.4.2_${ARCH}.deb && \
    apt-get install -y ./grafana_10.4.2_${ARCH}.deb && \
    rm grafana_10.4.2_${ARCH}.deb

# Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Grafana & Prometheus configuration
RUN mkdir -p /etc/grafana/provisioning/datasources \
    /etc/grafana/provisioning/dashboards \
    /etc/grafana/dashboards

COPY app.py /app/app.py
COPY prometheus/prometheus.yml /etc/prometheus/prometheus.yml
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY grafana/dashboards/*.json /etc/grafana/dashboards/
COPY grafana/provisioning/datasources/ /etc/grafana/provisioning/datasources/
COPY grafana/provisioning/dashboards/ /etc/grafana/provisioning/dashboards/
COPY grafana/grafana.ini /etc/grafana/grafana.ini

RUN chown -R grafana:grafana /etc/grafana

ENV PYTHONUNBUFFERED=1
EXPOSE 8118 9090 3000

CMD ["/usr/bin/supervisord", "-n"]
