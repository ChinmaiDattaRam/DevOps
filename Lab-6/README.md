# Lab 6 - Delivery Metrics, Prometheus, and Grafana

This lab exposes simulated delivery metrics on port 8000, scrapes them with
Prometheus, evaluates alert rules, and provisions a Grafana data source and
dashboard. The Compose stack uses a private project network and only publishes
the three service ports on localhost.

## Code

### `delivery_metrics.py`

```python
from prometheus_client import Gauge, Summary, start_http_server
import random
import time

total_deliveries = Gauge("total_deliveries", "Total number of deliveries")
pending_deliveries = Gauge("pending_deliveries", "Number of pending deliveries")
on_the_way_deliveries = Gauge(
    "on_the_way_deliveries", "Number of deliveries on the way"
)
average_delivery_time = Summary(
    "average_delivery_time", "Average delivery time in seconds"
)


def simulate_delivery():
    pending = random.randint(10, 20)
    on_the_way = random.randint(5, 20)
    delivered = random.randint(30, 70)
    avg_time = random.uniform(15, 45)
    total = pending + on_the_way + delivered
    total_deliveries.set(total)
    pending_deliveries.set(pending)
    on_the_way_deliveries.set(on_the_way)
    average_delivery_time.observe(avg_time)
    return {
        "total": total,
        "pending": pending,
        "on_the_way": on_the_way,
        "delivered": delivered,
        "average_seconds": avg_time,
    }


if __name__ == "__main__":
    start_http_server(8000, addr="0.0.0.0")
    while True:
        print(simulate_delivery(), flush=True)
        time.sleep(1)
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY delivery_metrics.py .
EXPOSE 8000
CMD ["python", "delivery_metrics.py"]
```

### `requirements.txt`

```text
prometheus-client>=0.22,<1
```

### `test_metrics.py`

```python
import unittest

from delivery_metrics import simulate_delivery


class TestDeliveryMetrics(unittest.TestCase):
    def test_simulation_returns_consistent_delivery_counts(self):
        result = simulate_delivery()
        self.assertEqual(
            result["total"],
            result["pending"] + result["on_the_way"] + result["delivered"],
        )
        self.assertGreaterEqual(result["pending"], 10)
        self.assertLessEqual(result["pending"], 20)
        self.assertGreaterEqual(result["average_seconds"], 15)
        self.assertLessEqual(result["average_seconds"], 45)


if __name__ == "__main__":
    unittest.main()
```

### `prometheus.yml`

```yaml
global:
  scrape_interval: 5s
rule_files:
  - /etc/prometheus/alert_rules.yml
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["prometheus:9090"]
  - job_name: delivery_service
    static_configs:
      - targets: ["delivery-metrics:8000"]
```

### `alert_rules.yml`

```yaml
groups:
  - name: delivery_alerts
    rules:
      - alert: HighPendingDeliveries
        expr: pending_deliveries > 10
        for: 15s
        labels:
          severity: warning
        annotations:
          summary: High pending deliveries
          description: Pending deliveries are above 10 for 15 seconds.
      - alert: HighAverageDeliveryTime
        expr: average_delivery_time_sum / average_delivery_time_count > 30
        for: 15s
        labels:
          severity: critical
        annotations:
          summary: High average delivery time
          description: Average delivery time is above 30 seconds for 15 seconds.
```

### `docker-compose.yml`

```yaml
services:
  delivery-metrics:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
    depends_on:
      - delivery-metrics
  grafana:
    image: grafana/grafana:latest
    ports:
      - "127.0.0.1:3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
```

### `grafana/provisioning/datasources/prometheus.yml`

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### `grafana/provisioning/dashboards/dashboards.yml`

```yaml
apiVersion: 1
providers:
  - name: Delivery Operations
    orgId: 1
    folder: Delivery
    type: file
    disableDeletion: true
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

### `grafana/provisioning/dashboards/delivery-operations.json`

```json
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "targets": [
        {
          "expr": "total_deliveries",
          "legendFormat": "Total deliveries",
          "refId": "A"
        }
      ],
      "title": "Total Deliveries",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "targets": [
        {
          "expr": "pending_deliveries",
          "legendFormat": "Pending deliveries",
          "refId": "A"
        }
      ],
      "title": "Pending Deliveries",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 8
      },
      "id": 3,
      "targets": [
        {
          "expr": "on_the_way_deliveries",
          "legendFormat": "On the way",
          "refId": "A"
        }
      ],
      "title": "On-the-Way Deliveries",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 8
      },
      "id": 4,
      "targets": [
        {
          "expr": "average_delivery_time_sum / average_delivery_time_count",
          "legendFormat": "Average delivery time",
          "refId": "A"
        }
      ],
      "title": "Average Delivery Time",
      "type": "timeseries"
    }
  ],
  "schemaVersion": 39,
  "title": "Delivery Operations",
  "uid": "delivery-operations",
  "version": 1
}
```

### `Jenkinsfile`

```groovy
pipeline {
    agent any

    stages {
        stage('Pre-check Docker') {
            steps {
                sh 'docker version'
                sh 'docker info'
            }
        }
        stage('Setup Workspace') {
            steps {
                sh 'test -s Lab-6/delivery_metrics.py'
                sh 'test -s Lab-6/prometheus.yml'
                sh 'test -s Lab-6/alert_rules.yml'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker compose -p devops-lab6-jenkins -f Lab-6/docker-compose.yml build'
            }
        }
        stage('Run Application') {
            steps {
                sh 'docker compose -p devops-lab6-jenkins -f Lab-6/docker-compose.yml up -d'
            }
        }
        stage('Run Prometheus & Grafana') {
            steps {
                sh '''
python3 - <<'PY'
import json
import time
import urllib.parse
import urllib.request

def get_json(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)

deadline = time.monotonic() + 180
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8000/metrics", timeout=5
        ) as response:
            metrics = response.read().decode()
        assert "total_deliveries " in metrics
        query = urllib.parse.quote('up{job="delivery_service"}')
        result = get_json(
            f"http://127.0.0.1:9090/api/v1/query?query={query}"
        )
        assert result["status"] == "success"
        assert result["data"]["result"][0]["value"][1] == "1"
        health = get_json("http://127.0.0.1:3000/api/health")
        assert health["database"] == "ok"
        break
    except Exception:
        time.sleep(3)
else:
    raise RuntimeError("Monitoring stack did not become healthy.")
print("Metrics, Prometheus target, and Grafana health verified.")
PY
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose -p devops-lab6-jenkins -f Lab-6/docker-compose.yml down --remove-orphans'
        }
    }
}
```

For the Jenkins Docker stages, the Jenkins agent needs the Docker CLI,
`docker compose`, and access to the Docker daemon. Mounting the Docker socket
gives Jenkins host-level control over Docker and should only be done for a
trusted, local Jenkins instance.

## Run

```powershell
docker compose up -d --build
Invoke-WebRequest http://127.0.0.1:8000/metrics
Invoke-RestMethod 'http://127.0.0.1:9090/api/v1/query?query=total_deliveries'
Invoke-WebRequest http://127.0.0.1:3000/api/health
```

To exercise the alert rules, temporarily change `pending = random.randint(10, 20)`
to `pending = random.randint(50, 100)` in `delivery_metrics.py`, rebuild/restart
the metrics service, wait for the Prometheus `for: 15s` period, and verify
`HighPendingDeliveries` under Prometheus **Alerts**. Restore the original range
after the check, then rebuild/restart `delivery-metrics` to return to normal
metrics.

Grafana is available at <http://localhost:3000> (the local exercise stack uses
the default `admin` / `admin` login). The provisioned dashboard is named
**Delivery Operations**. To stop and remove only this lab's containers:

```powershell
docker compose down
```

## Results

Screenshots show the [Grafana dashboard](./screenshots/01-delivery-dashboard.jpg),
[metrics endpoint](./screenshots/02-prometheus-metrics.jpg),
[running monitoring stack](./screenshots/03-monitoring-stack.jpg),
[healthy Prometheus targets](./screenshots/04-prometheus-targets.jpg),
[alert pending](./screenshots/05-high-pending-alert-pending.jpg), and
[alert firing](./screenshots/06-high-pending-alert-firing.jpg).
