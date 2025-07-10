# Docker Compose Install Script for PSN AI Guide Bot
# This script checks for Docker installation and runs the application

# Function to check if Docker is installed
function Test-DockerInstalled {
    try {
        docker --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to detect Docker Compose command
function Get-DockerComposeCommand {
    # Try modern Docker Compose (docker compose)
    try {
        docker compose version | Out-Null
        return "docker compose"
    } catch {
        # Fall back to legacy Docker Compose (docker-compose)
        try {
            docker-compose --version | Out-Null
            return "docker-compose"
        } catch {
            return $null
        }
    }
}

Write-Host "=== PSN AI Guide Bot Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
if (-not (Test-DockerInstalled)) {
    Write-Host "Docker is not installed." -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "After installation, restart this script." -ForegroundColor White
    exit 1
} else {
    Write-Host "Docker is installed." -ForegroundColor Green
}

# Check if Docker is running
Write-Host "Checking if Docker is running..." -ForegroundColor Yellow
if (-not (Test-DockerRunning)) {
    Write-Host "Docker is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop and then re-run this script." -ForegroundColor White
    exit 1
} else {
    Write-Host "Docker is running." -ForegroundColor Green
}

# Detect Docker Compose command
Write-Host "Detecting Docker Compose..." -ForegroundColor Yellow
$composeCmd = Get-DockerComposeCommand
if ($null -eq $composeCmd) {
    Write-Host "Docker Compose not found." -ForegroundColor Red
    Write-Host "Please ensure Docker Compose is installed with Docker Desktop." -ForegroundColor White
    exit 1
} else {
    Write-Host "Using: $composeCmd" -ForegroundColor Green
}

# Navigate to docker directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Join-Path $scriptPath ".."
$dockerPath = Join-Path $projectRoot "docker"

if (-not (Test-Path $dockerPath)) {
    Write-Host "Docker directory not found at: $dockerPath" -ForegroundColor Red
    Write-Host "Please ensure you are running this script from the scripts/ directory." -ForegroundColor White
    exit 1
}

Write-Host "Navigating to docker directory..." -ForegroundColor Yellow
Set-Location $dockerPath

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "docker-compose.yml not found in docker directory." -ForegroundColor Red
    exit 1
}

Write-Host "Found docker-compose.yml" -ForegroundColor Green
Write-Host ""

# Ask user about run mode
Write-Host "Choose run mode:" -ForegroundColor Cyan
Write-Host "1. Foreground (see logs, press Ctrl+C to stop)" -ForegroundColor White
Write-Host "2. Background (detached, runs in background)" -ForegroundColor White
Write-Host ""

do {
    $choice = Read-Host "Enter your choice (1 or 2)"
} while ($choice -notmatch "^[12]$")

$runDetached = $choice -eq "2"

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
try {
    if ($composeCmd -eq "docker compose") {
        docker compose -p psn-ai-guide-bot down --remove-orphans 2>$null
    } else {
        docker-compose -p psn-ai-guide-bot down --remove-orphans 2>$null
    }
    Write-Host "Cleaned up existing containers." -ForegroundColor Green
} catch {
    Write-Host "No existing containers to stop." -ForegroundColor Blue
}

# Start the application
Write-Host ""
if ($runDetached) {
    Write-Host "Starting application in background..." -ForegroundColor Yellow
    try {
        if ($composeCmd -eq "docker compose") {
            docker compose -p psn-ai-guide-bot up -d
        } else {
            docker-compose -p psn-ai-guide-bot up -d
        }
        Write-Host "Application started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Useful commands:" -ForegroundColor Cyan
        Write-Host "- Check status: $composeCmd -p psn-ai-guide-bot ps" -ForegroundColor White
        Write-Host "- View logs: $composeCmd -p psn-ai-guide-bot logs -f" -ForegroundColor White
        Write-Host "- Stop app: $composeCmd -p psn-ai-guide-bot down" -ForegroundColor White
    } catch {
        Write-Host "Failed to start application." -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Starting application in foreground..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Blue
    Write-Host ""
    try {
        if ($composeCmd -eq "docker compose") {
            docker compose -p psn-ai-guide-bot up
        } else {
            docker-compose -p psn-ai-guide-bot up
        }
    } catch {
        Write-Host "Failed to start application." -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green