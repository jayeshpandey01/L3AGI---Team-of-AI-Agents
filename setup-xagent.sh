#!/bin/bash

# L3AGI XAgent Integration Setup Script
# This script sets up XAgent integration in the L3AGI monorepo

set -e

echo "🚀 Setting up XAgent integration for L3AGI..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the L3AGI root directory"
    exit 1
fi

# Check if XAgent submodule exists
if [ ! -d "third_party/xagent" ]; then
    print_error "XAgent submodule not found. Please run: git submodule update --init --recursive"
    exit 1
fi

print_status "Setting up XAgent integration..."

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p configs/xagent
mkdir -p logs/xagent
mkdir -p local_workspace
mkdir -p docker

# Copy XAgent configuration
if [ -f "configs/xagent/config.yml" ]; then
    print_warning "XAgent config already exists, backing up..."
    cp configs/xagent/config.yml configs/xagent/config.yml.backup
fi

# Create local workspace
print_status "Setting up local workspace..."
if [ ! -f "local_workspace/.gitkeep" ]; then
    touch local_workspace/.gitkeep
fi

# Set up environment file
if [ ! -f ".env.xagent" ]; then
    print_status "Creating .env.xagent from template..."
    cp env.xagent.example .env.xagent
    print_warning "Please update .env.xagent with your actual API keys and configuration"
else
    print_warning ".env.xagent already exists, please ensure it's properly configured"
fi

# Install XAgent dependencies
print_status "Installing XAgent dependencies..."
if command -v pip &> /dev/null; then
    pip install -r requirements-xagent.txt
    print_success "XAgent dependencies installed successfully"
elif command -v pip3 &> /dev/null; then
    pip3 install -r requirements-xagent.txt
    print_success "XAgent dependencies installed successfully"
else
    print_error "pip not found. Please install pip and try again"
    exit 1
fi

# Check Docker availability
if command -v docker &> /dev/null; then
    print_success "Docker found"
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose found"
        
        # Test Docker daemon
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_warning "Docker daemon is not running. Please start Docker and try again"
        fi
    else
        print_warning "Docker Compose not found. Please install Docker Compose"
    fi
else
    print_warning "Docker not found. Please install Docker to use XAgent with ToolServer"
fi

# Create logs directory
print_status "Setting up logging..."
mkdir -p logs/xagent
touch logs/xagent/.gitkeep

# Set up gitignore entries
print_status "Updating .gitignore..."
if [ -f ".gitignore" ]; then
    # Check if XAgent entries already exist
    if ! grep -q "XAgent" .gitignore; then
        echo "" >> .gitignore
        echo "# XAgent Integration" >> .gitignore
        echo "logs/xagent/" >> .gitignore
        echo "local_workspace/" >> .gitignore
        echo ".env.xagent" >> .gitignore
        echo "*.log" >> .gitignore
        print_success "Added XAgent entries to .gitignore"
    else
        print_warning "XAgent entries already exist in .gitignore"
    fi
else
    print_warning ".gitignore not found, please add XAgent entries manually"
fi

# Create startup script
print_status "Creating startup script..."
cat > start-xagent.sh << 'EOF'
#!/bin/bash

# L3AGI XAgent Startup Script

echo "🚀 Starting L3AGI XAgent services..."

# Check if .env.xagent exists
if [ ! -f ".env.xagent" ]; then
    echo "❌ .env.xagent not found. Please copy env.xagent.example to .env.xagent and configure it."
    exit 1
fi

# Start XAgent services
echo "📦 Starting XAgent services with Docker Compose..."
docker-compose -f docker-compose.xagent.yml up -d

echo "✅ XAgent services started!"
echo "🌐 XAgent Web UI: http://localhost:5173"
echo "🔌 XAgent API: http://localhost:8090"
echo "🛠️  ToolServer: http://localhost:8080"
echo ""
echo "To view logs: docker-compose -f docker-compose.xagent.yml logs -f"
echo "To stop services: docker-compose -f docker-compose.xagent.yml down"
EOF

chmod +x start-xagent.sh

# Create stop script
print_status "Creating stop script..."
cat > stop-xagent.sh << 'EOF'
#!/bin/bash

# L3AGI XAgent Stop Script

echo "🛑 Stopping L3AGI XAgent services..."

docker-compose -f docker-compose.xagent.yml down

echo "✅ XAgent services stopped!"
EOF

chmod +x stop-xagent.sh

# Create health check script
print_status "Creating health check script..."
cat > check-xagent-health.sh << 'EOF'
#!/bin/bash

# L3AGI XAgent Health Check Script

echo "🏥 Checking XAgent services health..."

# Check XAgent Server
if curl -s http://localhost:8090/health &> /dev/null; then
    echo "✅ XAgent Server: Healthy"
else
    echo "❌ XAgent Server: Unhealthy or not running"
fi

# Check ToolServer
if curl -s http://localhost:8080/health &> /dev/null; then
    echo "✅ ToolServer: Healthy"
else
    echo "❌ ToolServer: Unhealthy or not running"
fi

# Check XAgent Web UI
if curl -s http://localhost:5173 &> /dev/null; then
    echo "✅ XAgent Web UI: Accessible"
else
    echo "❌ XAgent Web UI: Not accessible"
fi

# Check Docker containers
echo ""
echo "🐳 Docker container status:"
docker-compose -f docker-compose.xagent.yml ps
EOF

chmod +x check-xagent-health.sh

print_success "XAgent integration setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.xagent with your API keys and configuration"
echo "2. Run: ./start-xagent.sh to start XAgent services"
echo "3. Run: ./check-xagent-health.sh to verify services are healthy"
echo "4. Access XAgent Web UI at: http://localhost:5173"
echo ""
echo "📚 Documentation:"
echo "- XAgent config: configs/xagent/config.yml"
echo "- Docker compose: docker-compose.xagent.yml"
echo "- Environment template: env.xagent.example"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check logs: docker-compose -f docker-compose.xagent.yml logs -f"
echo "- Restart services: ./stop-xagent.sh && ./start-xagent.sh"
echo "- Verify Docker is running: docker info"
