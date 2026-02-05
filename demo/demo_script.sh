#!/bin/bash

echo "Checking SSH access..."
ssh node-1 hostname
ssh node-2 hostname

echo "Checking Node Exporter..."
curl node-1:9100/metrics | head

echo "Checking Prometheus..."
curl localhost:9090/-/ready

echo "Demo complete."
