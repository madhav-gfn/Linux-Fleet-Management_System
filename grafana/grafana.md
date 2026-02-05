# Grafana — Visualization Layer

## Role in the Lab

Grafana serves as the **visualization layer** for the Linux Fleet Management Lab.

It does not collect metrics itself.  
Instead, it queries **Prometheus**, which acts as the single source of truth.

---

## Deployment Details

- Installed on: `manager` node
- Managed via: `systemd`
- Default port: `3000`
- Accessed over host-only network

---

## Data Source Configuration

Grafana is configured with Prometheus as its data source:

- Type: Prometheus
- URL: `http://localhost:9090`
- Access mode: Server

Connection verified using Grafana's **Save & Test** functionality.

---

## Dashboards Used

### Node Exporter Full Dashboard

- Dashboard ID: **1860**
- Source: Grafana Community Dashboards
- Metrics provided:
  - CPU usage (per core and aggregate)
  - Memory utilization
  - Disk I/O and filesystem usage
  - Network traffic
  - Load average

This dashboard provides per-node visibility for:
- `node-1`
- `node-2`

---

## What This Demonstrates

Using Grafana in this lab demonstrates:

- Separation of concerns (collection vs visualization)
- Query-based dashboards (PromQL-driven)
- Centralized visibility into a Linux fleet
- Real-time observability of system health

---

## Notes

- Authentication is left at default (admin user) for lab simplicity
- TLS and role-based access control are intentionally omitted
- Grafana is treated as a **read-only consumer** of Prometheus data

These choices keep the lab focused on core infrastructure concepts.
