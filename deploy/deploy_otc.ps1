# DataNexus AI - Automated OTC (Open Telekom Cloud) Deployment Script (PowerShell)
param (
    [string]$OtcHost = "otc-ecs-instance.telekom.de",
    [string]$User = "ubuntu",
    [string]$KeyPath = "$HOME\.ssh\otc_key"
)

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " DataNexus AI - OTC Cloud Rollout Automation" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

Write-Host "[1/4] Verifying local Docker build & Pytest suite..." -ForegroundColor Yellow
python -m pytest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest suite failed! Aborting deployment."
    exit 1
}

Write-Host "[2/4] Packaging deployment artifacts..." -ForegroundColor Yellow
$ArchiveName = "datanexus_release.zip"
if (Test-Path $ArchiveName) { Remove-Item $ArchiveName }
Compress-Archive -Path "src", "deploy", "Dockerfile", "docker-compose.yml", "requirements.txt" -DestinationPath $ArchiveName

Write-Host "[3/4] Uploading artifacts to Open Telekom Cloud ECS ($OtcHost)..." -ForegroundColor Yellow
scp -i $KeyPath $ArchiveName "$User@${OtcHost}:~/datanexus/"

Write-Host "[4/4] Executing Docker Compose Stack restart on OTC ECS..." -ForegroundColor Yellow
ssh -i $KeyPath "$User@${OtcHost}" "cd ~/datanexus && unzip -o datanexus_release.zip && docker compose up -d --build"

Write-Host "=========================================================" -ForegroundColor Green
Write-Host " Deployment successfully finished on Open Telekom Cloud!" -ForegroundColor Green
Write-Host " Services running: PostgreSQL, Milvus, DataNexus API & Nginx HITNET Gateway" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
