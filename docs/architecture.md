# Architecture — Linux Fleet Management Lab

## Overview

This lab models a small Linux fleet managed through a central control node.
All management actions originate from the manager.

---

## Node Roles

### Manager
- Hostname: `manager`
- Runs:
  - Prometheus
  - Grafana
- Initiates:
  - SSH connections
  - Monitoring configuration

### Worker Nodes
- Hostnames:
  - `node-1`
  - `node-2`
- Run:
  - Node Exporter
- Do not initiate outbound management actions

---

## Networking

Each VM uses two interfaces:

1. **NAT**
   - Internet access
   - Package downloads

2. **Host-only network**
   - Fleet communication
   - SSH
   - Prometheus scraping
   - Grafana access

---

## Monitoring Flow

node_exporter (nodes)
↓
Prometheus (manager)
↓
Grafana (manager)


Prometheus pulls metrics every 15 seconds.
Grafana queries Prometheus on demand.

---

## Design Rationale

- Pull-based monitoring is safer and simpler
- Centralized control mirrors real infrastructure
- Minimal dependencies improve debuggability