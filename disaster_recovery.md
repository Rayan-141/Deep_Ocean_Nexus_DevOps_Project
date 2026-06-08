# Disaster Recovery Plan - DeepOcean Nexus

This document defines the strategies, mechanisms, and backup actions used to ensure high availability and disaster resilience across the subsea monitoring infrastructure.

## 1. High Availability Architecture

To guarantee the case study's required operational continuity, redundancy is built into every layer:
* **Application Layer**: Configured with 3 container replicas managed by a Kubernetes Deployment. If one container crashes, the others continue serving traffic while the orchestrator initializes replacements.
* **Health Monitoring (Probes)**:
  * **Liveness Probe**: Monitors whether the application is alive. If the `/health` endpoint stops responding, Kubernetes terminates and restarts the container immediately.
  * **Readiness Probe**: Ensures a container only receives traffic once initialized, preventing startup routing errors.

## 2. Backup Strategy

| Component | Target Location | RPO (Recovery Point Objective) | Backup Procedure |
|---|---|---|---|
| **Source Code** | GitHub Repository | Immediate | Git pushes on branch commits. |
| **Container Images** | Docker Hub | Per Release | Jenkins pushes versioned tags on successful pipelines. |
| **Infrastructure Configuration** | Terraform State & HCL | Version Control | State files stored in secure remote storage. |
| **Access Keys & Configuration** | Kubernetes Secrets | Per Deployment | Exported YAML configs securely backed up. |

## 3. Recovery Procedures

### Scenario A: Pod Failure / Crash Loop
* **Detection**: Liveness probe detects failure (HTTP status code != 200).
* **Action**: Kubernetes auto-healing restarts the container.
* **Manual Intervention**: None required. Run `kubectl get pods -n deepocean` to view restarts.

### Scenario B: Cluster Outage / Regional Disaster
* **Detection**: Prometheus alerts signal target endpoint downtime.
* **Action**: Re-provision the infrastructure and deploy the application:
  1. Boot a fresh cluster.
  2. Run `terraform apply` in the Terraform folder to build namespaces.
  3. Deploy files by running `kubectl apply -f kubernetes/`.
  4. Build containers via Jenkins pipeline to restore application states.
