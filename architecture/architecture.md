# Architecture Overview — Linux Fleet Management Lab

## High-Level Design

This lab simulates a small-scale Linux fleet managed through a central control node.
The design follows real-world infrastructure principles:

- Centralized control
- Agent-based monitoring
- Pull-based metrics collection
- Minimal trust surface

---

## Node Roles

### Manager Node
Hostname: `manager`

Responsibilities:
- Acts as SSH control plane
- Runs Prometheus (metrics collection)
- Runs Grafana (visualization)
- Initiates all management actions

### Worker Nodes
Hostnames:
- `node-1`
- `node-2`

Responsibilities:
- Run Node Exporter
- Expose system metrics
- Accept SSH connections from manager only

---

## Networking Model

Each VM uses dual networking:

1. NAT  
   - Internet access (updates, downloads)

2. Host-only Network (vboxnet0)  
   - Private fleet communication
   - SSH
   - Prometheus scraping
   - Grafana access

No external exposure of worker nodes.

---

## Monitoring Flow

1. Node Exporter runs on each node (port 9100)
2. Prometheus on manager scrapes metrics every 15 seconds
3. Metrics stored locally on manager
4. Grafana queries Prometheus for visualization

---

## Security Model

- SSH key-based authentication
- No shared credentials
- Read-only metrics exposure
- Separate system users for services

---

## Why This Architecture

This structure mirrors:
- Traditional data center monitoring
- Cloud VM fleets
- Pre-container infrastructure

It provides a strong conceptual base before introducing automation or containers.
