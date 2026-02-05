# Architecture

## System Overview

The Linux Fleet Management system consists of:

### Components

1. **Prometheus Server**
   - Central metrics collection
   - Data storage and querying
   - Alert management

2. **Node Exporters**
   - System metrics collection
   - Hardware monitoring
   - Performance data

### Data Flow

```
Linux Servers → Node Exporter → Prometheus → Monitoring Dashboard
```

### Network Architecture

- Prometheus: Port 9090
- Node Exporter: Port 9100
- Communication via HTTP/HTTPS

### Deployment Model

- Centralized Prometheus instance
- Distributed node exporters on each server
- Service-based management