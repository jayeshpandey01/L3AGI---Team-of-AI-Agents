# L3AGI XAgent Integration Setup Script for Windows
# This script sets up XAgent integration in the L3AGI monorepo

param(
    [switch]$SkipDockerCheck
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up XAgent integration for L3AGI..." -ForegroundColor Blue

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "This script must be run from the L3AGI root directory"
    exit 1
}

# Check if XAgent submodule exists
if (-not (Test-Path "third_party/xagent")) {
    Write-Error "XAgent submodule not found. Please run: git submodule update --init --recursive"
    exit 1
}

Write-Status "Setting up XAgent integration..."

# Create necessary directories
Write-Status "Creating directory structure..."
New-Item -ItemType Directory -Path "configs/xagent" -Force | Out-Null
New-Item -ItemType Directory -Path "logs/xagent" -Force | Out-Null
New-Item -ItemType Directory -Path "local_workspace" -Force | Out-Null
New-Item -ItemType Directory -Path "docker" -Force | Out-Null

# Copy XAgent configuration
if (Test-Path "configs/xagent/config.yml") {
    Write-Warning "XAgent config already exists, backing up..."
    Copy-Item "configs/xagent/config.yml" "configs/xagent/config.yml.backup"
}

# Create local workspace
Write-Status "Setting up local workspace..."
if (-not (Test-Path "local_workspace/.gitkeep")) {
    New-Item -ItemType File -Path "local_workspace/.gitkeep" -Force | Out-Null
}

# Set up environment file
if (-not (Test-Path ".env.xagent")) {
    Write-Status "Creating .env.xagent from template..."
    Copy-Item "env.xagent.example" ".env.xagent"
    Write-Warning "Please update .env.xagent with your actual API keys and configuration"
} else {
    Write-Warning ".env.xagent already exists, please ensure it's properly configured"
}

# Install XAgent dependencies
Write-Status "Installing XAgent dependencies..."
try {
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        pip install -r requirements-xagent.txt
        Write-Success "XAgent dependencies installed successfully"
    } elseif (Get-Command pip3 -ErrorAction SilentlyContinue) {
        pip3 install -r requirements-xagent.txt
        Write-Success "XAgent dependencies installed successfully"
    } else {
        Write-Error "pip not found. Please install pip and try again"
        exit 1
    }
} catch {
    Write-Warning "Failed to install dependencies: $($_.Exception.Message)"
    Write-Warning "Please install dependencies manually: pip install -r requirements-xagent.txt"
}

# Check Docker availability
if (-not $SkipDockerCheck) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Success "Docker found"
        
        # Check Docker Compose
        if ((Get-Command docker-compose -ErrorAction SilentlyContinue) -or 
            (docker compose version 2>$null)) {
            Write-Success "Docker Compose found"
            
            # Test Docker daemon
            try {
                docker info 2>$null | Out-Null
                Write-Success "Docker daemon is running"
            } catch {
                Write-Warning "Docker daemon is not running. Please start Docker and try again"
            }
        } else {
            Write-Warning "Docker Compose not found. Please install Docker Compose"
        }
    } else {
        Write-Warning "Docker not found. Please install Docker to use XAgent with ToolServer"
    }
}

# Create logs directory
Write-Status "Setting up logging..."
New-Item -ItemType Directory -Path "logs/xagent" -Force | Out-Null
if (-not (Test-Path "logs/xagent/.gitkeep")) {
    New-Item -ItemType File -Path "logs/xagent/.gitkeep" -Force | Out-Null
}

# Set up gitignore entries
Write-Status "Updating .gitignore..."
if (Test-Path ".gitignore") {
    # Check if XAgent entries already exist
    $gitignoreContent = Get-Content ".gitignore" -Raw
    if ($gitignoreContent -notmatch "XAgent") {
        Add-Content ".gitignore" ""
        Add-Content ".gitignore" "# XAgent Integration"
        Add-Content ".gitignore" "logs/xagent/"
        Add-Content ".gitignore" "local_workspace/"
        Add-Content ".gitignore" ".env.xagent"
        Add-Content ".gitignore" "*.log"
        Write-Success "Added XAgent entries to .gitignore"
    } else {
        Write-Warning "XAgent entries already exist in .gitignore"
    }
} else {
    Write-Warning ".gitignore not found, please add XAgent entries manually"
}

# Create startup script
Write-Status "Creating startup script..."
$startScript = @"
# L3AGI XAgent Startup Script for Windows

Write-Host "🚀 Starting L3AGI XAgent services..." -ForegroundColor Blue

# Check if .env.xagent exists
if (-not (Test-Path ".env.xagent")) {
    Write-Host "❌ .env.xagent not found. Please copy env.xagent.example to .env.xagent and configure it." -ForegroundColor Red
    exit 1
}

# Start XAgent services
Write-Host "📦 Starting XAgent services with Docker Compose..." -ForegroundColor Blue
docker-compose -f docker-compose.xagent.yml up -d

Write-Host "✅ XAgent services started!" -ForegroundColor Green
Write-Host "🌐 XAgent Web UI: http://localhost:5173" -ForegroundColor Cyan
Write-Host "🔌 XAgent API: http://localhost:8090" -ForegroundColor Cyan
Write-Host "🛠️  ToolServer: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker-compose -f docker-compose.xagent.yml logs -f" -ForegroundColor Yellow
Write-Host "To stop services: docker-compose -f docker-compose.xagent.yml down" -ForegroundColor Yellow
"@

Set-Content "start-xagent.ps1" $startScript

# Create stop script
Write-Status "Creating stop script..."
$stopScript = @"
# L3AGI XAgent Stop Script for Windows

Write-Host "🛑 Stopping L3AGI XAgent services..." -ForegroundColor Yellow

docker-compose -f docker-compose.xagent.yml down

Write-Host "✅ XAgent services stopped!" -ForegroundColor Green
"@

Set-Content "stop-xagent.ps1" $stopScript

# Create health check script
Write-Status "Creating health check script..."
$healthScript = @"
# L3AGI XAgent Health Check Script for Windows

Write-Host "🏥 Checking XAgent services health..." -ForegroundColor Blue

# Check XAgent Server
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8090/health" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ XAgent Server: Healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ XAgent Server: Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ XAgent Server: Unhealthy or not running" -ForegroundColor Red
}

# Check ToolServer
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ ToolServer: Healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ ToolServer: Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ ToolServer: Unhealthy or not running" -ForegroundColor Red
}

# Check XAgent Web UI
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ XAgent Web UI: Accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ XAgent Web UI: Not accessible (Status: $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ XAgent Web UI: Not accessible" -ForegroundColor Red
}

# Check Docker containers
Write-Host ""
Write-Host "🐳 Docker container status:" -ForegroundColor Blue
docker-compose -f docker-compose.xagent.yml ps
"@

Set-Content "check-xagent-health.ps1" $healthScript

Write-Success "XAgent integration setup completed successfully!"
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update .env.xagent with your API keys and configuration" -ForegroundColor White
Write-Host "2. Run: .\start-xagent.ps1 to start XAgent services" -ForegroundColor White
Write-Host "3. Run: .\check-xagent-health.ps1 to verify services are healthy" -ForegroundColor White
Write-Host "4. Access XAgent Web UI at: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "- XAgent config: configs/xagent/config.yml" -ForegroundColor White
Write-Host "- Docker compose: docker-compose.xagent.yml" -ForegroundColor White
Write-Host "- Environment template: env.xagent.example" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Troubleshooting:" -ForegroundColor Cyan
Write-Host "- Check logs: docker-compose -f docker-compose.xagent.yml logs -f" -ForegroundColor White
Write-Host "- Restart services: .\stop-xagent.ps1 then .\start-xagent.ps1" -ForegroundColor White
Write-Host "- Verify Docker is running: docker info" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Note: If you encounter execution policy issues, run:" -ForegroundColor Yellow
Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
