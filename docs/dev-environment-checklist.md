# Dev Environment Checklist

Before starting new backend phases (Prometheus integration, AI Admiral, etc.), sanity-check that the Windows host has full development control over the VM fleet. Run each check below and record the actual result — especially real IPs, SSH user, and dev loop — since later phases (e.g. `PROMETHEUS_URL` config) depend on this being accurate.

## 1. VirtualBox networking

- [ ] All 3 VMs running with **two adapters each** (NAT + Host-Only), per `docs/architecture.md`.
- [ ] Host-only adapter has a known subnet — check via VirtualBox `File → Host Network Manager`. Confirm it matches the IPs in `docs/plan.md` (`192.168.56.101/.102/.103`) or note what it actually is now.
- [ ] From Windows, ping each VM on its host-only IP:
  ```powershell
  ping 192.168.56.101   # manager
  ping 192.168.56.102   # worker 1
  ping 192.168.56.103   # worker 2
  ```

## 2. SSH from Windows → manager

- [ ] You (Windows) can SSH into the manager directly (not just manager→workers):
  ```powershell
  ssh <user>@192.168.56.101
  ```
- [ ] Key-based, no password prompt. If a password is currently required, note it — a key will be needed for automation later.

## 3. SSH from manager → workers

Should already be true per `docs/plan.md`, just confirm. From inside the manager VM:

```bash
ssh node-1 whoami
ssh node-2 whoami
```

- [ ] Confirm `node-1` / `node-2` resolve — via `/etc/hosts` on the manager or actual DNS. This matters because the backend's `ssh_service.py` connects using whatever `ip` is stored per node in SQLite.

## 4. Port forwarding (VirtualBox NAT adapter on manager VM)

Per `docs/plan.md` this should map Windows → manager for `8000`, `5173`, `9090`, `3000`. Check VirtualBox → manager VM → Settings → Network → Adapter 1 (NAT) → Port Forwarding, then from Windows:

- [ ] `curl http://localhost:9090` → Prometheus UI responds
- [ ] `curl http://localhost:3000` → Grafana responds
- [ ] `curl http://localhost:8000/health` → only works if the backend is currently running on the manager (see §6)
- [ ] `5173` — nothing to check yet, no frontend exists.

## 5. Prometheus scrape health (via forwarded 9090)

- [ ] Open `http://localhost:9090/targets` in browser — confirm all 3 targets (`prometheus`, `node-1:9100`, `node-2:9100`) show state **UP**.

## 6. Manager VM — Python backend runtime

SSH into the manager and check:

- [ ] `python3 --version` (matters for FastAPI/pydantic compatibility)
- [ ] Is there a venv already, or does the backend run off system Python? `which uvicorn` / `pip show fastapi`
- [ ] Can it actually start right now:
  ```bash
  cd fleet-manager/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
  Then from Windows, `curl http://localhost:8000/health` should return `{"status":"manager-up"}`.
- [ ] Is the code on the manager VM the **same** as this git repo on Windows, or has it drifted? I.e. is the dev loop "edit on Windows, push, pull on VM" or "VS Code Remote-SSH editing directly on the VM"?

## 7. Editor / dev loop

- [ ] VS Code **Remote-SSH** extension installed and able to open a window connected to the manager VM (the workflow described in `docs/plan.md`).
- [ ] Git installed and configured on the manager VM if commits will happen from there too, or confirm commits only ever happen from Windows.

## 8. Node exporter (workers) — sanity only, not directly reachable from Windows

- [ ] From the **manager**, not Windows:
  ```bash
  curl node-1:9100/metrics | head
  curl node-2:9100/metrics | head
  ```
  Confirms exporters are actually up, independent of Prometheus.
