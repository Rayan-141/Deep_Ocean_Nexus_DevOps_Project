# Project Report - DeepOcean Nexus
## Subsea Communications Infrastructure Platform

---

### Abstract
This project implements a cloud-native DevOps ecosystem designed to resolve system resilience, deployment speed, and monitoring visibility issues highlighted in Case Study 134: Project DeepOcean Nexus. The solution containerizes a real-time cable telemetry application, provisions resources declaratively using Terraform, orchestrates high-availability deployments on Kubernetes, automates integration via Jenkins, and implements metrics scraping with Prometheus and Grafana.

---

### 1. Introduction & Case Study Analysis
DeepOcean Nexus operates global subsea telecommunication networks. The legacy infrastructure suffered from:
* Manual deployments causing latency and human error.
* Fragmented diagnostics preventing fast response to cyber attacks or cable damages.
* Zero automated failover, delaying service recovery.

To address these challenges, we built a modern architecture combining infrastructure automation, containerization, orchestration, and continuous monitoring.

---

### 2. DevOps Technology Stack

* **Application Layer**: Python Flask web server generating subsea telemetry parameters (temperature, pressure, attenuation, seismic activity, packet loss) and exposing monitoring metrics.
* **Infrastructure Provisioning**: Terraform Kubernetes provider provisioning isolated workspaces.
* **Orchestrator**: Kubernetes (Deployment and Services) running 3 replicas with readiness/liveness health probes.
* **Container Runtime**: Docker Desktop creating compact python-slim runner images.
* **CI/CD Automation**: Jenkins Pipeline declaring multi-phase builds, registry pushes, and deployment rollouts.
* **Observability**: Prometheus pulling application-specific parameters and Grafana rendering live metric values.

---

### 3. Implementation Details

#### 3.1 Docker Containerization
The container packages the application and exposes port 5000 (web traffic) and port 8000 (Prometheus metrics) to isolate environments.

#### 3.2 Kubernetes Resource Management
* **Deployments**: Configured to run 3 replicas to guarantee high availability.
* **Health Probes**: Liveness and readiness HTTP probes hit `/health` on port 5000 every 5 seconds to detect container locks.
* **Secrets Management**: Base64 encoded Secret resources hold sensitive keys, avoiding hardcoded configuration vulnerabilities.

---

### 4. System Validation & Demonstration

1. **Dashboard Verification**: Check the Flask interface on port 5000 to verify live telemetry updates.
2. **Auto-Healing Validation**: Terminate a Pod:
   ```bash
   kubectl delete pod <pod-name> -n deepocean
   ```
   Observe Kubernetes detecting the loss and creating a replacement instance immediately to maintain availability.
3. **Observability Verification**: Open Prometheus (`localhost:9090`) to verify target metrics scraping, then map gauges into Grafana dashboards.
