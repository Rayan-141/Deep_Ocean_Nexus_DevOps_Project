# System Architecture - DeepOcean Nexus

This document outlines the architecture, toolflow, and responsibilities of each component within the DevOps pipeline.

## 1. Flow Diagram

```text
[Developer]
     │ (git push)
     ▼
[GitHub Repository]
     │
     ▼ (webhook / polling)
[Jenkins Build Server] ─── (runs stages)
     │
     ├───► [Docker Agent] ─── (compiles image) ───► [Docker Hub]
     │                                                     │
     └───► [Kubectl Deployer] ─────────────────────────────┼────────┐
                                                           │        │
                                                           ▼        ▼
                                                 [Kubernetes Cluster (Pods)]
                                                           │        │
                                                   (pulls) │        │ (exposes)
                                                           ▼        ▼
                                                      [Prometheus]  [Web UI]
                                                           │
                                                           ▼
                                                       [Grafana]
```

## 2. Component Directory

* **Application (Python/Flask)**: Houses logic to emit raw system metrics and serve the frontend dashboard showing real-time subsea health indicators (temperatures, signal-to-noise ratio, seismic events, cyber threat levels).
* **Terraform**: Manages cluster setup at the infrastructure layer (IaC). Configures target isolation (`deepocean` namespace) on top of the Kubernetes resource grid.
* **Kubernetes (Orchestration)**: Launches 3 container replicas running the app. Configures health probes to detect issues, manages service routing internally, and exposes services to users on specific ports.
* **Jenkins (CI/CD)**: Monitors code updates, builds and validates containers, uploads images to the registry, and rolls out changes inside Kubernetes automatically.
* **Observability (Prometheus & Grafana)**:
  * Prometheus scrapes metrics on port 8000.
  * Grafana reads data from Prometheus and renders dashboard charts.
