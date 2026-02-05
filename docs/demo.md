# How to Run the Demo

1. Start all VirtualBox VMs
2. SSH into manager
3. Verify SSH access to nodes:
ssh node-1
ssh node-2

4. Check Prometheus:
- http://<manager-ip>:9090
- Targets page shows all UP
5. Check Grafana:
- http://<manager-ip>:3000
- Node Exporter dashboard visible