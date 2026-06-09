# DeepOcean Nexus - Global Subsea Communications Infrastructure Platform

DeepOcean Nexus is a DevOps-driven simulation of a subsea communications monitoring network. This repository implements automated infrastructure provisioning, containerization, orchestration, continuous integration/continuous delivery (CI/CD), security protocols, disaster recovery planning, and real-time observability.

## Directory Structure

* **`app/`**: Contains the source code of the Python Flask monitoring web application, HTML frontend, and the Dockerfile.
* **`kubernetes/`**: Contains resources for deploying the containerized application on Kubernetes (Deployments, Services, and Secrets).
* **`terraform/`**: Contains provisioning scripts to configure target namespace infrastructure inside Kubernetes.
* **`jenkins/`**: Pipeline orchestration rules defining the build, test, and release cycle.
* **`monitoring/`**: Docker Compose configuration setting up Prometheus and Grafana metrics scraper.

## Installation and Execution Flow

### 1. Pre-requisites
Ensure you have the following installed on your local machine:
* Docker Desktop
* Kubectl
* Terraform
* Minikube (or local Kubernetes context enabled in Docker Desktop settings)

### 2. Infrastructure Provisioning
Initialize and apply the Terraform plan to prepare the cluster namespace:
```bash
cd terraform
terraform init
terraform apply -auto-approve
```

### 3. Build Container Locally
Verify the application container compiles and launches correctly:
```bash
cd ../app
docker build -t deepocean-app:latest .
docker run -d -p 5000:5000 -p 8000:8000 --name deepocean-local deepocean-app:latest
```

### 4. Orchestrate on Kubernetes
Make sure the cluster is active and apply deployment details:
```bash
cd ../kubernetes
kubectl apply -f .
```

### 5. Launch Observability Stack
Run Prometheus and Grafana services locally to pull metrics:
```bash
cd ../monitoring
docker-compose up -d
```
* **Flask Application Dashboard**: `http://localhost:5000`
* **Prometheus Targets Panel**: `http://localhost:9090`
* **Grafana Dashboards**: `http://localhost:3000` (default login: admin/admin)
Webhook Test
