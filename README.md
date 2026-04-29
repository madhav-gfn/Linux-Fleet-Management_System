# Linux Fleet

> A small Linux fleet management and observability lab built to simulate how real infrastructure is provisioned, monitored, and verified across multiple nodes.

[images]

## Table of Contents

- [Dev Timeline](#dev-timeline)
- [Overview](#overview)
- [What This Project Is](#what-this-project-is)
- [What This Project Does](#what-this-project-does)
- [Architecture](#architecture)
- [Monitoring Flow](#monitoring-flow)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Backend Service](#backend-service)
- [How the Lab Works](#how-the-lab-works)
- [Demo Flow](#demo-flow)
- [Getting Started](#getting-started)
- [Operational Notes](#operational-notes)
- [Project Highlights](#project-highlights)
- [Current Scope](#current-scope)
- [Image Placeholders](#image-placeholders)

## Dev Timeline

Use this section to record problems faced during development and how they were solved.

| Date | Problem | Solution |
| --- | --- | --- |
|  |  |  |

## Overview

Linux Fleet is a hands-on infrastructure lab centered around a simple but realistic idea: one manager node controls and observes a small group of Linux machines. Instead of treating servers as isolated systems, the project models them as a fleet with defined roles, repeatable setup, centralized monitoring, and a clear operational flow.

The repository combines several infrastructure concerns in one place:

- Node-level monitoring with Prometheus and Node Exporter
- Dashboard-based visualization with Grafana
- Centralized administration patterns through a manager node
- Automation for exporter deployment using Ansible
- A FastAPI backend service that stores fleet nodes, runs SSH commands, and records audit history

This makes the project useful as both a portfolio-grade lab and a practical learning environment for Linux administration, observability, and small-scale infrastructure design.

[images]

## What This Project Is

This project is a lab environment for understanding how a fleet of Linux systems can be managed and observed from a central point.

At its core, it represents:

- A manager-worker topology
- A pull-based monitoring model
- A reproducible setup approach
- A documentation-first infrastructure project

It is not a full enterprise orchestration platform, and it does not try to hide that. Its strength is that it keeps the moving parts understandable while still reflecting patterns used in real environments.

## What This Project Does

The project currently delivers the following capabilities:

1. It organizes a fleet into clear node roles.
   The `manager` node acts as the control and monitoring point, while `node-1` and `node-2` act as worker machines.

2. It enables centralized monitoring.
   Prometheus runs on the manager and scrapes metrics from each worker via Node Exporter.

3. It provides a visualization layer.
   Grafana is configured to use Prometheus as its data source so infrastructure health can be inspected through dashboards.

4. It supports automated agent installation.
   An Ansible playbook is included to install and start Node Exporter on worker nodes.

5. It includes a backend foundation.
   A FastAPI manager API exposes node registry, SSH command execution, broadcast execution, streaming terminal output, and audit history endpoints.

6. It documents the architecture and demo path.
   The repository includes supporting markdown files for architecture notes and walkthrough steps.

## Architecture

The lab models a three-node layout:

| Role | Hostname | Purpose |
| --- | --- | --- |
| Manager | `manager` | Runs Prometheus, Grafana, and the backend service |
| Worker | `node-1` | Exposes system metrics through Node Exporter |
| Worker | `node-2` | Exposes system metrics through Node Exporter |

Each machine is designed to play a focused role:

- The manager is the only central coordination point
- The workers are monitored targets rather than control-plane systems
- Monitoring data flows inward toward the manager
- Administrative actions originate from the manager side

The documented networking model uses:

- NAT for internet/package access
- A host-only network for internal fleet communication, SSH, metrics scraping, and dashboard access

[images]

## Monitoring Flow

The observability path in this project is intentionally simple and clean:

```text
Worker Nodes
  node_exporter on :9100
        |
        v
Prometheus on manager :9090
        |
        v
Grafana on manager :3000
```

What this means in practice:

- Node Exporter exposes operating system and hardware metrics on each worker
- Prometheus scrapes those metrics every 15 seconds
- Grafana queries Prometheus to turn raw metrics into readable dashboards
- The manager becomes the single place to inspect fleet health

This pull-based design keeps the system easier to reason about and closely matches common observability patterns used in production environments.

## Repository Structure

```text
Linux-Fleet/
|-- ansible/                 # Automation for worker setup
|-- backend/                 # Manager-side FastAPI service
|-- demo/                    # Demo script for quick verification
|-- docs/                    # Architecture and demo documentation
|-- grafana/                 # Grafana notes and provisioning config
|-- node_exporter/           # Node Exporter install artifacts and systemd unit
|-- ova/                     # Reserved for appliance/export assets
|-- presentation/            # Reserved for presentation material
|-- prometheus/              # Prometheus scrape configuration
`-- README.md
```

### Directory Notes

`ansible/`
Contains the playbook that automates Node Exporter installation and service startup on worker nodes.

`backend/`
Contains the manager API. It keeps the node registry and audit log in SQLite and uses AsyncSSH to run commands on fleet nodes.

`demo/`
Contains a shell script that checks SSH access, Node Exporter output, and Prometheus readiness.

`docs/`
Contains supporting project documentation, including architecture notes and demo instructions.

`grafana/`
Contains Grafana provisioning files and usage notes. The dashboards folder is currently set up as a location for dashboard assets and documentation.

`node_exporter/`
Contains the systemd service file and shell installation helper for Node Exporter.

`prometheus/`
Contains the Prometheus scrape configuration for the manager and worker nodes.

`ova/` and `presentation/`
These folders are present as project scaffolding for future packaging and presentation assets.

## Technology Stack

| Layer | Tools |
| --- | --- |
| Operating system | Ubuntu Server 22.04 LTS |
| Fleet communication | SSH |
| Metrics exporter | Node Exporter |
| Metrics collection | Prometheus |
| Visualization | Grafana |
| Automation | Ansible |
| Backend foundation | Python, FastAPI, SQLite, AsyncSSH |
| Virtualization context | VirtualBox |

## Backend Service

The backend FastAPI app lives in [`backend/app/main.py`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/backend/app/main.py).

Current behavior:

- Runs on port `8000` with Uvicorn
- Enables CORS
- Stores nodes and audit history in `backend/fleet.db`
- Seeds `manager`, `node-1`, and `node-2` on first boot
- Uses AsyncSSH for single-node commands, streamed commands, and broadcast commands
- Exposes `GET /health`

Phase 1 API surface:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/nodes` | List all fleet nodes |
| `POST` | `/api/nodes` | Register a new node |
| `GET` | `/api/nodes/{id}` | Get node detail |
| `DELETE` | `/api/nodes/{id}` | Remove a node |
| `POST` | `/api/nodes/{id}/command` | Run a command and return stdout, stderr, and exit code |
| `WS` | `/ws/nodes/{id}/command` | Stream command output line by line |
| `POST` | `/api/nodes/broadcast` | Run the same command on all nodes in parallel |
| `GET` | `/api/audit` | View command history |

[images]

## How the Lab Works

From an operational perspective, the lab follows a straightforward sequence:

1. Worker nodes boot and become reachable over the internal network.
2. Node Exporter runs on each worker and exposes system metrics.
3. Prometheus on the manager scrapes those metrics on a fixed interval.
4. Grafana reads from Prometheus and renders dashboards for inspection.
5. The backend service can provide manager-side API functionality as the project grows.

This separation is one of the strongest design choices in the repository:

- Exporters collect host data
- Prometheus stores and queries metrics
- Grafana visualizes data
- The backend can evolve independently into an application layer

## Demo Flow

The included demo path focuses on validating the main moving pieces of the lab:

1. Start all virtual machines.
2. Connect to the `manager` node.
3. Verify SSH access to `node-1` and `node-2`.
4. Confirm Node Exporter is reachable on the workers.
5. Confirm Prometheus is ready and scraping targets.
6. Open Grafana and inspect the dashboards.

The demo script in [`demo/demo_script.sh`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/demo/demo_script.sh) automates part of this flow by checking:

- SSH connectivity
- Node Exporter metric output
- Prometheus readiness

## Getting Started

Because this repository represents a lab rather than a one-command local app, setup is best approached by component.

### 1. Prepare the Nodes

- Create or start the VirtualBox virtual machines
- Ensure the manager and worker nodes can resolve or reach each other
- Confirm SSH connectivity from the manager to the workers

### 2. Install Node Exporter on Workers

Use either:

- The Ansible playbook in [`ansible/playbook.yml`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/ansible/playbook.yml)
- The shell-based installation helper in [`node_exporter/install_node_exporter.sh`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/node_exporter/install_node_exporter.sh)

### 3. Configure Prometheus on the Manager

Prometheus is configured through [`prometheus/prometheus.yml`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/prometheus/prometheus.yml) to scrape:

- `localhost:9090`
- `node-1:9100`
- `node-2:9100`

### 4. Configure Grafana

Grafana provisioning files point Grafana to Prometheus as the default data source:

- [`grafana/provisioning/datasources.yml`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/grafana/provisioning/datasources.yml)
- [`grafana/provisioning/dashboards.yml`](/c:/Users/madmi/OneDrive/Desktop/Linux-Fleet/grafana/provisioning/dashboards.yml)

### 5. Run the Backend Service

From the `backend` directory:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then verify:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"manager-up"}
```

Open Swagger UI at:

```text
http://localhost:8000/docs
```

If your SSH username is different from the local OS user, set it before first boot:

```bash
export FLEET_SSH_USER=ubuntu
```

## Operational Notes

- Prometheus is configured with a `15s` scrape interval and `15s` evaluation interval.
- The current Grafana notes describe Prometheus as a local manager-side data source at `http://localhost:9090`.
- The system is intentionally lab-oriented and keeps authentication, TLS, and RBAC minimal or out of scope.
- The backend stores runtime state in local SQLite by default. Override the location with `FLEET_DB_PATH` if needed.

## Project Highlights

Why this repository stands out:

- It shows a full observability chain rather than a single tool in isolation.
- It reflects real infrastructure role separation in a way that is easy to explain.
- It includes both manual and automated setup paths.
- It is small enough to understand end-to-end.
- It can evolve naturally into a richer fleet-control platform.

## Current Scope

The repository is strongest today as:

- A Linux fleet monitoring lab
- A DevOps and infrastructure portfolio project
- A learning environment for Prometheus, Grafana, Node Exporter, SSH, and Ansible

It should be understood as an actively extensible foundation rather than a finished production platform. In particular:

- The backend service is a lab control-plane foundation, not a hardened production API
- Dashboard JSON assets are not committed in the current tree
- `ova/` and `presentation/` are scaffolded but currently empty

That does not weaken the project. It makes the roadmap visible and gives the repository room to grow in a structured way.

## Image Placeholders

Use the placeholders below wherever you want to later replace them with screenshots, diagrams, or exports:

### Hero Banner

[images]

### Architecture Diagram

[images]

### Prometheus Targets View

[images]

### Grafana Dashboard View

[images]

### Terminal Demo / SSH Verification

[images]

### Backend Health Check

[images]
