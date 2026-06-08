# Logging Strategy - DeepOcean Nexus

This document outlines the logging strategy implemented for the subsea monitoring infrastructure.

## 1. Current Logging Implementation

The application writes diagnostic telemetry events to standard output (stdout). Since the application runs within Docker containers inside Kubernetes, stdout streams are captured by the runtime engine automatically.

To inspect application logs in real-time, run:
```bash
kubectl logs deployment/deepocean-app -c app -n deepocean -f
```

To fetch logs from a specific pod:
```bash
kubectl logs <pod-name> -n deepocean
```

To view events related to namespace creation, pod crashes, or probe alerts:
```bash
kubectl get events -n deepocean --sort-by='.metadata.creationTimestamp'
```

## 2. Future Production Enhancement (ELK Stack)

In a live production setting, local console log inspection is insufficient. The architecture can scale to integrate the Elasticsearch, Logstash, and Kibana (ELK) stack:

1. **Log Collection (Filebeat/Logstash)**: A lightweight shipper (Filebeat) runs as a DaemonSet on each Kubernetes cluster node to harvest container log files from `/var/log/containers/*`.
2. **Log Aggregation & Indexing (Elasticsearch)**: Logstash filters, parses (e.g., extracting status codes and timestamps), and indices JSON records in Elasticsearch clusters.
3. **Log Visualization (Kibana)**: System administrators build dashboards in Kibana to query events, filter logs by pod namespace, and monitor signal strength anomalies over time.
