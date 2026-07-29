#!/usr/bin/env bash
# DataNexus AI - Automated OTC Cloud Deployment Script (Bash)
set -e

OTC_HOST="${1:-otc-ecs-instance.telekom.de}"
USER="${2:-ubuntu}"
KEY_PATH="${3:-$HOME/.ssh/otc_key}"

echo "========================================================="
echo " DataNexus AI - OTC Cloud Rollout Automation"
echo "========================================================="

echo "[1/4] Running automated Pytest suite..."
python -m pytest

echo "[2/4] Archiving release bundle..."
tar -czf datanexus_release.tar.gz src deploy Dockerfile docker-compose.yml requirements.txt

echo "[3/4] Uploading to OTC ECS ($OTC_HOST)..."
scp -i "$KEY_PATH" datanexus_release.tar.gz "$USER@$OTC_HOST:~/datanexus/"

echo "[4/4] Restarting Docker Compose Stack on OTC ECS..."
ssh -i "$KEY_PATH" "$USER@$OTC_HOST" "cd ~/datanexus && tar -xzf datanexus_release.tar.gz && docker compose up -d --build"

echo "========================================================="
echo " OTC Deployment completed successfully!"
echo "========================================================="
