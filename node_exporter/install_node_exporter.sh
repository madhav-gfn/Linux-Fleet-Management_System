#!/bin/bash
set -e

VERSION="1.7.0"

useradd -rs /bin/false node_exporter || true

cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v${VERSION}/node_exporter-${VERSION}.linux-amd64.tar.gz
tar xvf node_exporter-${VERSION}.linux-amd64.tar.gz

mv node_exporter-${VERSION}.linux-amd64/node_exporter /usr/local/bin/
cp node_exporter.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter
