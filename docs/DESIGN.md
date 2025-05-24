# Architecture & Design

This document outlines the architectural decisions, concurrency model, and
deployment rationale for the Django WebSocket Blue/Green deployment etc.

---

## 1. System Overview

* **Django + Channels**: Core application built on Django, using Django
  Channels to handle WebSocket connections.
* **Uvicorn ASGI Server**: Runs the Channels application, providing
  high-performance async I/O. The startup commands can be found in
  [scripts/entrypoint.sh](entrypoint.sh).
* **Nginx**: Reverse proxy for HTTP/WebSocket traffic, and routes to active
  app instances.
* **Docker Compose**: Orchestrates multi-container environment, including two
  app instances (`app_blue` & `app_green`), monitoring, metrics, and load
  testing.
* **Blue/Green Deployment**: Ensures zero-downtime releases by maintaining two
  parallel environments and switching traffic via Nginx proxy.

---

## 2. Concurrency & WebSocket Scaling

1. **ASGI Workers**

   * Uvicorn is launched with multiple worker processes (`--workers 8`) to
     utilize multi-core CPUs.
   * Each worker handles asynchronous event loops via `uvloop` for fast network
     I/O.

2. **Channel Layers**

   * Currently, we're dumping everything in memory.
   * (Optimization): Redis (or alternative) can be used as the channel layer
     for pub/sub and group messaging.
   * Ensures messages broadcasted (e.g., chat rooms) are propagated across all
     Uvicorn workers.

3. **Session & Connection Management**

   * Connections are tracked in an in-memory map (`SESSIONS`) and metrics
     counters (active connections, total messages).

---

## 3. Observability & Health Checks

* **Prometheus Metrics** exposed at `/metrics`:

  * **Active Connections**: Gauge of current live WebSocket sessions.
  * **Total Messages**: Counter of messages received.
  * **Error Count**: Counter for exceptions in consumer logic.

* **Grafana Dashboards**:

  * Visualize real-time metrics, trends, and alert thresholds.
  * Preconfigured via `docker/compose.yml` and mounted to `/etc/grafana/dashboards`.

* **Health Endpoints**:

  * `/healthz`: Liveness probe — returns 200 if the server process is running.
  * `/readyz`: Readiness probe — returns 200 if the application has started.
    Tracked via globa variables + shutdown singal (SIGTERM)

---

## 4. Blue/Green Deployment Rationale

1. **Zero-Downtime Releases**

   * Maintain two identical environments (`app_blue` & `app_green`).
   * Deploy new code to the idle environment, run health checks, then flip
     traffic by updating Nginx.

2. **Rollback Capability**

   * If smoke tests or production monitoring detect issues, the deployment
     doesn't go through and older stuff keeps on running.

3. **Automation**

   * `promote.sh` encapsulates build, smoke tests, proxy update, and teardown
     logic.
   * Ensures consistent and repeatable deployment process.

---

## 5. Nginx Settings

* **Nginx Proxy Settings**:

  * Upgrade and Connection headers for WebSocket handshake.
  * Timeouts tuned for long-lived connections.

---

## 6. Optimizations

* **Autoscaling**: Use docker swarm to run replicas of application. Ensuring
  application is horizontally scalable.
* **Channel Layer Backend**: Integrate Redis or other in-memory cache.

---
