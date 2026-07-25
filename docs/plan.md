# Linux Fleet Management System

> *"You are the Commander. The Admiral watches your fleet."*

A self-hosted, AI-powered Linux fleet management platform built on top of an existing Prometheus + Grafana monitoring stack. The system adds remote command execution, intelligent alerting, metric forecasting, and an AI Admiral that proactively monitors your fleet and acts on your behalf — with a configurable autonomy level you control.

---

## Vision

The goal is not just a monitoring dashboard — those already exist. The vision is a **command center**: a single place where you can see everything happening across your Linux fleet, talk to an AI that understands your infrastructure in real time, and let it handle routine operations while you stay in command of the important decisions.

The AI Admiral is the centerpiece. It is proactive by default — it watches the fleet continuously and only speaks when something needs attention. When it recommends an action, you can approve it, or you can configure it to act autonomously. You control the trust boundary, per node, with a toggle.

The system is designed to scale from 3 nodes (current) to 20 nodes without architectural changes.

---

## What's Already Built

The foundation is a 3-node Ubuntu VM fleet (1 manager, 2 workers) running on VirtualBox, with a complete pull-based observability stack:

- **Node Exporter** — installed and running on all nodes, exposing hardware and OS-level metrics on port 9100
- **Prometheus** — running on the manager VM, scraping all nodes at defined intervals, storing time-series data
- **Grafana** — connected to Prometheus as a data source, pre-built Node Exporter dashboards provisioned
- **SSH** — passwordless key-based access already configured from manager → workers

The monitoring pipeline (collect → scrape → store → visualize) is complete and working. Everything being built in this project sits on top of it.

---

## What We're Building

```
┌─────────────────────────────── MANAGER VM ──────────────────────────────────┐
│                                                                               │
│  ┌──────────────────┐    ┌─────────────────────────────────────────────┐    │
│  │  Existing Stack  │    │           New Backend (FastAPI)              │    │
│  │                  │    │                                               │    │
│  │  Prometheus :9090│◄───┤  Prometheus Query Layer                      │    │
│  │  Grafana    :3000│    │  SSH Commander (asyncssh)                    │    │
│  │  Node Exporter   │    │  AI Admiral Service (Gemini)                 │    │
│  └──────────────────┘    │  ├─ Reactive (chat interface)               │    │
│                           │  ├─ Proactive (background monitor loop)     │    │
│                           │  └─ Prediction Engine (metric forecasting)  │    │
│                           │  Alert Engine                               │    │
│                           │  Autonomy System                            │    │
│                           │  Graceful Shutdown Orchestrator             │    │
│                           │  Audit Log (SQLite)                         │    │
│                           └─────────────────────────────────────────────┘    │
│                                          │ REST API + WebSocket              │
│                           ┌──────────────▼──────────────┐                   │
│                           │       Web UI (React)         │                   │
│                           │  Fleet Dashboard             │                   │
│                           │  Admiral Chat Terminal       │                   │
│                           │  SSH Command Runner          │                   │
│                           │  Alert Center                │                   │
│                           │  Autonomy Control Panel      │                   │
│                           └──────────────────────────────┘                   │
└───────────────────────────────────────────────────────────────────────────────┘
          │ SSH (already set up)          │ SSH
          ▼                              ▼
    ┌──────────┐                   ┌──────────┐
    │ Worker 1 │                   │ Worker 2 │  ... up to Worker 20
    │ Node Exp │                   │ Node Exp │
    └──────────┘                   └──────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend framework | **FastAPI (Python)** | Lightest serious web framework, native async, WebSocket support built in, Swagger UI auto-generated |
| SSH execution | **asyncssh** | Non-blocking async SSH, supports live output streaming, parallel execution across nodes |
| AI Admiral brain | **Google Gemini API** | Via `google-generativeai` Python SDK |
| Database | **SQLite + aiosqlite** | Zero-config, no extra process, perfect for fleet state and audit logs at this scale |
| Metric forecasting | **NumPy** (linear regression) | Lightweight, no extra service; Prophet added later if seasonality-aware forecasting is needed |
| Prometheus client | **httpx** | Async HTTP client to query Prometheus HTTP API |
| Frontend | **React + Vite** | Fast dev server, simple build pipeline |
| Production serving | **nginx** | Serves built frontend on port 80, reverse proxies to FastAPI on port 8000 |
| Process manager | **systemd** | Runs the backend as a persistent service on the manager VM |

Total memory footprint of the new backend: ~150-250MB RAM alongside existing Prometheus and Grafana.

---

## Infrastructure

### Current Fleet

| Node | Role | IP (Host-Only) | SSH |
|------|------|----------------|-----|
| Manager VM | Backend + Prometheus + Grafana | 192.168.56.101 | Key-based |
| Worker 1 | Node Exporter | 192.168.56.102 | Key-based from manager |
| Worker 2 | Node Exporter | 192.168.56.103 | Key-based from manager |

Target scale: **20 nodes**. The node registry is database-driven, so adding nodes is a single API call with no code changes.

### Host Machine

- **Windows** (development machine)
- **VirtualBox** for all VMs
- Development workflow: VS Code with Remote SSH extension → writes and runs code directly on the manager VM over the host-only network
- Browser on Windows accesses all services via VirtualBox port forwarding → `localhost:8000` on Windows hits FastAPI on the manager VM

### VirtualBox Network Setup

Each VM requires two network adapters:

- **Adapter 1: NAT** — gives VMs internet access
- **Adapter 2: Host-Only** — gives Windows host a stable, static IP route to all VMs

Port forwarding on the Manager VM NAT adapter:

| Service | Windows Port | Manager VM Port |
|---------|-------------|-----------------|
| FastAPI | 8000 | 8000 |
| Web UI (dev) | 5173 | 5173 |
| Prometheus | 9090 | 9090 |
| Grafana | 3000 | 3000 |

---

## Project Structure

```
fleet-manager/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Node IPs, Prometheus URL, Gemini API key
│   │   ├── database.py              # SQLite + aiosqlite setup
│   │   ├── models/
│   │   │   ├── node.py              # Node registry model
│   │   │   ├── audit_log.py         # Every action ever taken, by whom
│   │   │   ├── alert.py             # Alert records
│   │   │   ├── action.py            # Pending / completed Admiral actions
│   │   │   └── session.py           # Admiral conversation sessions
│   │   ├── api/
│   │   │   ├── nodes.py             # Fleet node CRUD + SSH endpoints
│   │   │   ├── commands.py          # SSH command runner endpoints
│   │   │   ├── metrics.py           # Prometheus query endpoints
│   │   │   ├── admiral.py           # Gemini chat endpoints
│   │   │   └── alerts.py            # Alert management endpoints
│   │   ├── services/
│   │   │   ├── ssh.py               # asyncssh wrapper (single, stream, broadcast)
│   │   │   ├── prometheus.py        # Prometheus HTTP API client + cache
│   │   │   ├── admiral.py           # Gemini integration + context injection
│   │   │   ├── alert_engine.py      # Background alert monitor loop (60s)
│   │   │   ├── proactive_loop.py    # Proactive Admiral loop (5 min)
│   │   │   ├── prediction.py        # Metric forecasting engine (15 min)
│   │   │   └── shutdown.py          # Graceful node shutdown orchestrator
│   │   └── schemas/                 # Pydantic request/response models
│   ├── requirements.txt
│   ├── .env                         # Secrets — never commit this
│   └── run.sh                       # Starts uvicorn
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Fleet overview, node cards, live metrics
│   │   │   ├── AdmiralChat.jsx      # Chat interface with command cards
│   │   │   ├── CommandRunner.jsx    # SSH terminal with live output streaming
│   │   │   ├── AlertCenter.jsx      # Live alert feed + pending action approvals
│   │   │   └── AutonomyPanel.jsx    # Per-node autonomy levels + audit log
│   │   ├── components/
│   │   └── api/                     # Axios API client + WebSocket hooks
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Core Features

### SSH Command Engine
Remote command execution on any node or all nodes simultaneously. Three execution modes:
- **Single node, full output** — run a command, get stdout/stderr/exit code
- **Single node, streaming** — live output streamed over WebSocket to the terminal UI
- **Broadcast** — same command runs in parallel on all nodes via `asyncio.gather()`

Every command is written to the audit log before execution: timestamp, node, command, triggered by (user or Admiral), result.

### Fleet Health Snapshot
A structured JSON snapshot of the entire fleet — current CPU, RAM, disk, network per node, trend directions (rising/stable/falling), and a `most_stressed_node` field. Cached with a 30-second TTL. This snapshot is injected as context into every Gemini request so the Admiral always has current situational awareness before responding.

### AI Admiral — Reactive Mode
A Gemini-powered chat interface with full fleet context. The Admiral's system prompt establishes its role and behavior:

> *You are the Admiral, an AI operations officer managing a Linux fleet on behalf of your Commander. You always have the current fleet health snapshot available. You are direct, precise, and concise — no filler. When you diagnose a problem, you specify exactly which node, which metric, and what to do. When you suggest a command, wrap it in `[CMD:node-id:command]` format so the UI can extract it. You never act destructively without explicit confirmation. You flag risk clearly.*

When the Admiral suggests a command, the UI extracts it from the response and renders it as a clickable action card with a one-click Execute button. Conversation history is stored per session in SQLite.

### AI Admiral — Proactive Mode
A background loop running every 5 minutes. Fetches current fleet snapshot, active alerts, and forecasts. If everything is healthy — silent, does nothing. If something warrants attention, sends the context to Gemini and asks it to assess whether action is required. If Gemini recommends an action, it becomes a `PendingAction` and is handled according to the target node's autonomy level.

This is the primary mode — the Admiral watches without being asked.

### Prediction Engine
Background task running every 15 minutes. For each node, pulls the last 24 hours of metrics from Prometheus and fits trend models:
- **Disk** — linear regression, gives "projected full in N hours at current rate"
- **CPU / RAM** — rolling window average + variance, flags sustained anomalies

Predictions are stored in SQLite and injected into the Admiral's context. Alert types include `PREDICTED_WARNING` and `PREDICTED_CRITICAL` — the system warns before the threshold is breached, not after.

### AI-Inferred Thresholds
Instead of hardcoded numbers, Gemini analyzes 7 days of metric history per node and returns per-node alert thresholds as structured JSON, with reasoning. Stored in SQLite and overridable manually.

Example output:
```json
{
  "node": "worker-1",
  "thresholds": {
    "cpu":  { "warning": 75, "critical": 90 },
    "ram":  { "warning": 80, "critical": 93 },
    "disk": { "warning": 70, "critical": 85 }
  },
  "reasoning": "Worker-1 shows sustained CPU spikes to 68% during peak hours — warning threshold set conservatively at 75%."
}
```

### Alert Engine
Background loop running every 60 seconds:
1. Pull current metrics from Prometheus
2. Compare against per-node AI-inferred thresholds
3. Check prediction engine — is any metric projected to breach threshold within 2 hours?
4. If yes → create alert in DB, push to all connected UI clients via WebSocket

Alert severity levels: `THRESHOLD_WARNING`, `THRESHOLD_CRITICAL`, `PREDICTED_WARNING`, `PREDICTED_CRITICAL`

### Autonomy System
Configurable per node. Three levels:

| Level | Behavior |
|-------|----------|
| `SUPERVISED` | Admiral recommends only. Every action requires your explicit approval. |
| `SEMI_AUTO` | Admiral executes low-risk actions autonomously (restart service, clear cache). Escalates medium/high-risk actions for approval. |
| `FULL_AUTO` | Admiral executes all recommended actions, logs everything, notifies you after. |

**Global override** — one toggle in the UI instantly forces all nodes to `SUPERVISED`. This is the emergency kill switch, styled prominently in red.

### Graceful Shutdown Orchestrator
Triggered by a critical alert, an Admiral recommendation (approved or autonomous), or a manual trigger from the UI. No workload migration — clean shutdown only.

```
Stage 1 — WARN (10 seconds)
  SSH: wall "Fleet Manager: Graceful shutdown in 60 seconds"
  Alert pushed to UI

Stage 2 — DRAIN (60 seconds)
  SSH: stop non-essential services in configured order
  Each stop logged with result
  SSH: sync (flush disk writes)

Stage 3 — SHUTDOWN
  SSH: sudo shutdown -h +1
  Node marked OFFLINE in registry
  Audit log entry written
  Alert resolved in UI
```

Which services are stopped during drain, and in what order, is configurable per node in the registry.

### Audit Log
Everything the system does to a node is logged — user commands, Admiral recommendations, autonomous actions, shutdown sequences. When the Admiral acts in FULL_AUTO mode, the audit log is your complete record of what happened and why.

---

## API Reference

### Nodes
```
GET    /api/nodes                       List all fleet nodes
POST   /api/nodes                       Register a new node
GET    /api/nodes/{id}                  Node detail
DELETE /api/nodes/{id}                  Remove a node
```

### Commands
```
POST   /api/nodes/{id}/command          Run command, get full output
WS     /ws/nodes/{id}/command           Run command, stream output live
POST   /api/nodes/broadcast             Run command on all nodes in parallel
GET    /api/audit                       Full command audit history
```

### Metrics
```
GET    /api/fleet/health                Full fleet snapshot (all nodes, all metrics)
GET    /api/nodes/{id}/metrics          Current metrics for one node
GET    /api/nodes/{id}/metrics/range    Historical metric range (for graphs)
GET    /api/nodes/{id}/forecast         Metric predictions for a node
```

### Admiral
```
POST   /api/admiral/chat                Send message, get response + extracted commands
GET    /api/admiral/sessions            List conversation sessions
GET    /api/admiral/sessions/{id}       Full conversation history
DELETE /api/admiral/sessions/{id}       Clear a session
POST   /api/admiral/infer-thresholds    Trigger AI threshold inference for a node
```

### Alerts
```
GET    /api/alerts                      All active alerts
GET    /api/alerts/history              Past resolved alerts
POST   /api/nodes/{id}/thresholds       Manually set/override thresholds
WS     /ws/alerts                       Live alert stream
```

### Autonomy & Actions
```
GET    /api/nodes/{id}/autonomy         Get node autonomy level
PATCH  /api/nodes/{id}/autonomy         Set node autonomy level
POST   /api/fleet/autonomy/supervised   Force all nodes to SUPERVISED
GET    /api/actions/pending             List pending Admiral actions
POST   /api/actions/{id}/approve        Approve a pending action
POST   /api/actions/{id}/deny           Deny a pending action
```

### Shutdown
```
POST   /api/nodes/{id}/shutdown         Trigger graceful shutdown sequence
GET    /api/nodes/{id}/shutdown/status  Shutdown sequence progress
```

---

## Web UI

### Fleet Dashboard
Grid of node cards. Each card shows live CPU/RAM/disk bars, status indicator (green/yellow/red), a 30-minute sparkline, and active alert count. Cards pulse on active alerts. Click any node for a drill-down view with full metric history and the Admiral's assessment of that node.

### Admiral Chat
Split panel. Left: live fleet mini-status. Right: full chat interface. Admiral responses render as formatted text with command suggestions extracted into clickable cards — each card shows the node, the command, and an Execute button. Admiral responses stream in real time via WebSocket so you see it thinking.

### Command Runner
Node selector (individual node or "All Nodes"). Command input field. Terminal-style output panel that streams via WebSocket. Command history sidebar with re-run buttons.

### Alert Center
Live feed via WebSocket. Each alert shows severity icon, node name, metric name, current value, projected trajectory, and the Admiral's plain-English explanation of why it matters. Predicted alerts are visually distinct from active threshold breaches. Pending Admiral actions appear as cards with Approve / Deny buttons.

### Autonomy Control Panel
Table of all nodes with autonomy level dropdown per row. Global SUPERVISED override toggle at the top (red, prominent). Section below showing last Admiral action per node. Full audit log table at the bottom — every action the system took, timestamped, with the triggering reason.

---

## Development Phases

### Phase 0 — Dev Environment Setup *(~1-2 days)*
Configure VirtualBox host-only networking, assign static IPs to all VMs, set up VS Code Remote SSH to connect to manager VM, configure port forwarding so Windows browser reaches all services.

**Goal:** `http://localhost:8000` on Windows hits the manager VM. VS Code saves files directly on Linux.

### Phase 1 — Backend Foundation + SSH Command Engine *(~4-5 days)*
FastAPI scaffold, SQLite database, node registry, asyncssh wrapper with single/streaming/broadcast modes, audit logging.

**Goal:** `POST /api/nodes/{id}/command` runs a command on a worker and streams output to Swagger UI.

### Phase 2 — Prometheus Integration *(~2-3 days)*
Prometheus HTTP API client with 30s cache, per-node metric endpoints, fleet health snapshot endpoint.

**Goal:** `GET /api/fleet/health` returns a full structured fleet snapshot.

### Phase 3 — AI Admiral, Reactive Mode *(~3-4 days)*
Gemini integration, fleet context injection pipeline, conversation history, command extraction from responses, per-session storage.

**Goal:** Chat with the Admiral in the UI. It knows current fleet state. Suggested commands are one-click executable.

### Phase 4 — Prediction Engine + Alert System *(~5-6 days)*
NumPy-based metric forecasting background task, AI-inferred threshold generation, alert engine background loop, WebSocket alert streaming.

**Goal:** Alert Center shows live alerts including predicted future breaches. Admiral can explain any alert.

### Phase 5 — Proactive Admiral + Autonomy + Shutdown *(~5-6 days)*
Proactive Admiral background loop, autonomy level system with global override, graceful shutdown orchestrator.

**Goal:** Admiral monitors fleet autonomously. Autonomy toggle controls whether it acts or asks. Shutdown sequence executes cleanly on demand or on trigger.

### Phase 6 — Web UI *(~8-10 days, parallel to Phases 3-5)*
React + Vite frontend: Fleet Dashboard, Admiral Chat, Command Runner, Alert Center, Autonomy Control Panel.

**Goal:** Full command center UI running on the manager VM, accessible from Windows browser.

### Total Estimated Time: 4-5 weeks

---

## Deployment on Manager VM

When the backend is ready to run permanently (not just during a dev session):

**Backend as a systemd service:**
```ini
[Unit]
Description=Fleet Manager Backend
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/fleet-manager/backend
ExecStart=/home/youruser/fleet-manager/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/youruser/fleet-manager/backend/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fleet-manager
sudo systemctl start fleet-manager
```

**Frontend served by nginx:**
```bash
cd frontend && npm run build
# Copy dist/ to nginx web root, proxy /api/ to :8000
```

Both services start automatically on VM boot. Prometheus and Grafana continue running as before.

---

## Key Design Decisions

**Why FastAPI over Flask or Django?** Lowest RAM footprint of any production Python web framework. Native async support is essential for running SSH commands across multiple nodes in parallel without thread pools.

**Why asyncssh over Paramiko?** Paramiko is synchronous — it blocks the event loop during SSH operations. asyncssh is fully async, meaning 10 simultaneous SSH commands run truly in parallel in a single process.

**Why SQLite over PostgreSQL?** No extra process, no config, zero RAM overhead. At a fleet of 20 nodes, SQLite handles the write throughput of audit logs and metric snapshots without issue. Migrating to Postgres later is straightforward if needed.

**Why Gemini?** It's what the Commander chose. The system is designed so the AI provider is swappable — the Gemini service layer is isolated behind the `services/admiral.py` interface.

**Why not containerize yet?** The system runs inside VMs which are already an isolation layer. Docker adds complexity without benefit at this stage. Containerization is a natural future improvement once the system is stable.

**Why dropped workload migration?** Migration requires knowing what a "workload" is, where it can run, and how to verify it came up correctly on the target node. That's a significant orchestration problem that isn't relevant at the current fleet composition. The shutdown orchestrator handles node decommissioning cleanly without it. Migration can be revisited when the fleet has a clearer service topology.

---

## Future Improvements

- Containerize with Docker Compose (Prometheus, Grafana, and the new backend in one `docker-compose.yml`)
- Service discovery instead of static node registry (Prometheus service discovery config as source of truth)
- Ansible integration — Admiral can generate and execute Ansible playbooks for configuration changes
- Workload migration once fleet has a defined service topology
- Multi-user support with role-based access (Commander vs Observer)
- Mobile-friendly UI for on-the-go fleet checks
- Webhook / email notifications for critical alerts
- Prophet-based forecasting for seasonality-aware predictions (upgrade from linear regression)