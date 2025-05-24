# Observability

This document details the metrics, dashboards, and alerting setup for the
Django WebSocket service.

[Grafana Dashboard](data/grafana-dashboard.png)

---

## 1. Prometheus Metrics

The service exposes operational metrics at the `/metrics` endpoint:

* **active\_connections** (Gauge)  – current number of live WebSocket sessions.
* **total\_messages** (Counter)   – cumulative messages received.
* **error\_count** (Counter)      – exceptions encountered in the WebSocket
  consumer.

These metrics are instrumented using the official Prometheus Python client and
automatically scraped by Prometheus (configured in `docker/compose.yml`).

---

## 2. Grafana Dashboards

Dashboards are preconfigured and loaded under `/etc/grafana/dashboards` via
Docker Compose. They include:

* **WebSocket Overview**: Trends of connections, messages, and errors over
  time.
* **Latency Heatmap**: Distribution of processing latency per message.
* **Resource Utilization**: Host CPU, memory, and network usage.

Each dashboard consists of multiple panels that query Prometheus for:

![Grafana Dashboard Load Testing](data/grafana-dashboard-load-testing.png)

```promql
# Number of open connections
active_connections

# Message rate per second
rate(total_messages[1m])

# Error rate per second
rate(error_count[1m])
```
---

## 3. Alerts & Notifications

![Prometheus Alert Firing](data/prometheus-rule-firing.png)

Alerts are defined in Prometheus using simple rules:

- It'll raise when active connections drop down to 0 for 60s.

---

## 4. Adding or Updating Dashboards

1. Modify or add JSON files under `docker/grafana/dashboards/`.
2. Restart the Grafana container:

   ```bash
   docker-compose restart grafana
   ```
3. Verify changes at `http://localhost:3000`.

---
