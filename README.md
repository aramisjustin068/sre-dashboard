# sre-dashboard

A Grafana dashboard definition in JSON, plus a Python validator that checks
the panel structure before you import it.

## Why

I watched someone push a dashboard with a broken panel target and nobody
noticed for two weeks because the panel just showed "No data" and everyone
assumed the service had no traffic. It did. The query was wrong.

The validator catches the things that silently break: missing expressions,
empty titles, duplicate panel IDs, panels without grid positions. Run it in
CI, not at 02:00 during an incident.

## What is in here

- `dashboard.json` — a Grafana dashboard with six panels covering the four
  signals an on-call engineer actually looks at: request rate, latency, errors,
  and resource saturation (CPU, memory, restarts). Uses Prometheus as the
  datasource with variables for namespace and service selection.

- `validate.py` — a standalone Python script (no dependencies beyond stdlib)
  that checks every panel has the required fields: id, title, type, datasource,
  gridPos, and at least one target with a non-empty expression. Also detects
  duplicate panel IDs and missing top-level dashboard fields.

## Usage

```bash
# Validate the dashboard
python3 validate.py dashboard.json

# Strict mode (also checks panel types against a known set)
python3 validate.py dashboard.json --strict

# Use in CI — exits 0 on success, 1 on validation errors
python3 validate.py dashboard.json && echo "dashboard OK" || exit 1
```

## Dashboard panels

1. **Request Rate (req/s)** — by status code, so you see 4xx and 5xx separately
2. **P99 Latency** — histogram quantile, with yellow/red thresholds at 500ms/1s
3. **Error Rate (5xx)** — stat panel, percentage of 5xx responses, red above 5%
4. **Pod CPU Usage** — per-pod, so you can see which one is the loud neighbour
5. **Pod Memory** — working set bytes, not RSS, because that is what the OOM
   killer watches
6. **Pod Restarts (24h)** — table panel, because restarts are a signal not a
   chart

## License

MIT. See [LICENSE](LICENSE).
