# Viva Preparation - DeepOcean Nexus

This document compiles questions and detailed explanations commonly asked during DevOps project evaluations and viva examinations.

---

## 1. Docker & Containerization

### Q1: Why did you containerize your application?
* **Answer**: Containerization packages the Python application, external library dependencies (Flask, prometheus-client), and configurations together. This ensures the application runs identically on local systems, test servers, and production clusters without "it works on my machine" issues.

### Q2: Explain the structure of your Dockerfile.
* **Answer**:
  * `FROM python:3.11-slim`: Starts from a lightweight python baseline image.
  * `WORKDIR /app`: Creates the default working directory inside the container.
  * `COPY requirements.txt .`: Copies only the dependency definitions first.
  * `RUN pip install ...`: Installs necessary python dependencies (separated from source copying to leverage Docker layer caching).
  * `COPY . .`: Copies the remaining source code.
  * `EXPOSE 5000` & `EXPOSE 8000`: Documents that the web application uses port 5000 and the metrics server uses port 8000.
  * `CMD ["python", "app.py"]`: Defines the command to start the application process.

---

## 2. Infrastructure as Code (IaC) - Terraform

### Q3: What is Infrastructure as Code, and how is it used in this project?
* **Answer**: Infrastructure as Code (IaC) enables defining and managing infrastructure assets using configuration files. In this project, we write declarative configurations in Terraform (`main.tf`) to automatically provision the target namespace (`deepocean`) within the Kubernetes cluster, removing manual portal operations.

### Q4: What do 'terraform init', 'terraform plan', and 'terraform apply' do?
* **Answer**:
  * `terraform init`: Downloads the required provider plugins (the Kubernetes provider in this case).
  * `terraform plan`: Performs a dry-run comparison between the local code configuration and the remote infrastructure state, printing out a list of changes it will perform.
  * `terraform apply`: Executes the changes specified in the configuration files to create or modify resources.

---

## 3. Orchestration - Kubernetes

### Q5: What is a Pod, and what is a Deployment in Kubernetes?
* **Answer**:
  * **Pod**: The smallest deployable unit in Kubernetes that represents a single running instance of your container application.
  * **Deployment**: An abstraction layer that manages Pod creation, scales replicas up or down, performs rolling updates, and ensures auto-healing by restarting failed Pods.

### Q6: How does Kubernetes handle auto-healing in your project?
* **Answer**: We configured `livenessProbe` and `readinessProbe` in `deployment.yaml`. The liveness probe periodically checks the `/health` endpoint of the application. If the container process locks up or crashes (returning non-200 HTTP statuses), Kubernetes detects the failure and automatically recreates the container to restore functionality.

---

## 4. CI/CD - Jenkins

### Q7: Explain the stages in your Jenkinsfile.
* **Answer**:
  * **Clone Stage**: Pulls the latest project updates from the Git source repository.
  * **Build Docker Stage**: Assembles a fresh Docker container image using the `Dockerfile`.
  * **Push Stage**: Authenticates with Docker Hub using Jenkins credentials and uploads the fresh image tag.
  * **Deploy Stage**: Commands the Kubernetes controller to apply resource configurations, triggering rolling updates.

---

## 5. Observability - Prometheus & Grafana

### Q8: How does Prometheus scrape metrics from your application?
* **Answer**: The Python script uses `prometheus-client` to expose metric records (such as `cable_latency_ms` and `cable_status`) on port 8000 at `/metrics`. Prometheus is configured with scrape targets pointing to the metrics port, pulling updates periodically.
