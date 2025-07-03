#!/bin/bash
set -e

# --- Configuration ---
PI_HOST="${PI_HOST:-pi@192.168.4.41}"  # Change this to your Pi's IP
PI_DIR="${PI_DIR:-/home/pi/HomeBase}"
LOCAL_DIR="$(pwd)"
PROJECT_NAME="HomeBase"

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Functions ---
function print_header() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${BLUE}🚀 HomeBase Deployment to Raspberry Pi 🚀${NC}"
    echo -e "${BLUE}==================================================${NC}"
}

function print_step() {
    echo -e "${YELLOW}📋 $1${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function check_ssh() {
    print_step "Checking SSH connection to Pi..."
    if ssh -o ConnectTimeout=10 "$PI_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
        print_success "SSH connection successful"
    else
        print_error "Cannot connect to Pi via SSH. Please check:"
        echo "  1. Pi is powered on and connected to network"
        echo "  2. SSH is enabled on Pi"
        echo "  3. PI_HOST variable is correct (currently: $PI_HOST)"
        echo "  4. SSH key is set up or password authentication is enabled"
        echo ""
        echo "Trying with password authentication..."
        if ssh -o ConnectTimeout=10 "$PI_HOST" "echo 'SSH connection successful'"; then
            print_success "SSH connection successful with password"
        else
            exit 1
        fi
    fi
}

function create_pi_directory() {
    print_step "Creating directory on Pi..."
    ssh "$PI_HOST" "mkdir -p $PI_DIR"
    print_success "Directory created: $PI_DIR"
}

function copy_files() {
    print_step "Copying project files to Pi..."
    
    # Create a temporary archive
    print_step "Creating project archive..."
    tar --exclude='venv' --exclude='database.db' --exclude='.DS_Store' --exclude='__pycache__' -czf /tmp/homebase-deploy.tar.gz .
    
    # Copy to Pi
    print_step "Transferring files..."
    scp /tmp/homebase-deploy.tar.gz "$PI_HOST:$PI_DIR/"
    
    # Extract on Pi
    print_step "Extracting files on Pi..."
    ssh "$PI_HOST" "cd $PI_DIR && tar -xzf homebase-deploy.tar.gz && rm homebase-deploy.tar.gz"
    
    # Clean up local archive
    rm /tmp/homebase-deploy.tar.gz
    
    print_success "Files copied successfully"
}

function setup_pi_environment() {
    print_step "Setting up Python environment on Pi..."
    
    # Check if Python 3 is available
    ssh "$PI_HOST" "python3 --version || (echo 'Python 3 not found. Installing...' && sudo apt update && sudo apt install -y python3 python3-pip python3-venv)"
    
    # Create virtual environment
    ssh "$PI_HOST" "cd $PI_DIR && python3 -m venv venv"
    
    # Install dependencies
    print_step "Installing Python dependencies..."
    ssh "$PI_HOST" "cd $PI_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    print_success "Python environment setup complete"
}

function setup_database() {
    print_step "Setting up database on Pi..."
    ssh "$PI_HOST" "cd $PI_DIR && source venv/bin/activate && python create_db.py && python seed_categories.py"
    print_success "Database initialized"
}

function create_service_file() {
    print_step "Creating systemd service file..."
    
    SERVICE_CONTENT="[Unit]
Description=HomeBase Calendar Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PI_DIR
Environment=PATH=$PI_DIR/venv/bin
ExecStart=$PI_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"
    
    echo "$SERVICE_CONTENT" | ssh "$PI_HOST" "sudo tee /etc/systemd/system/homebase.service > /dev/null"
    print_success "Service file created"
}

function enable_service() {
    print_step "Enabling and starting HomeBase service..."
    ssh "$PI_HOST" "sudo systemctl daemon-reload && sudo systemctl enable homebase && sudo systemctl start homebase"
    print_success "Service enabled and started"
}

function check_service_status() {
    print_step "Checking service status..."
    ssh "$PI_HOST" "sudo systemctl status homebase --no-pager"
}

function create_update_script() {
    print_step "Creating update script on Pi..."
    
    UPDATE_SCRIPT="#!/bin/bash
set -e

cd $PI_DIR
git pull origin main || echo 'No git repo, skipping pull'
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart homebase
echo 'Update complete!'"
    
    echo "$UPDATE_SCRIPT" | ssh "$PI_HOST" "tee $PI_DIR/update.sh > /dev/null"
    ssh "$PI_HOST" "chmod +x $PI_DIR/update.sh"
    print_success "Update script created: $PI_DIR/update.sh"
}

function print_final_instructions() {
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}🎉 Deployment Complete! 🎉${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo ""
    echo -e "${BLUE}Your HomeBase Calendar is now running on:${NC}"
    echo -e "   🌐 http://$(ssh $PI_HOST 'hostname -I | awk "{print \$1}"'):8001"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo -e "   📊 Check status: ssh $PI_HOST 'sudo systemctl status homebase'"
    echo -e "   🔄 Restart: ssh $PI_HOST 'sudo systemctl restart homebase'"
    echo -e "   📝 View logs: ssh $PI_HOST 'sudo journalctl -u homebase -f'"
    echo -e "   🔧 Update: ssh $PI_HOST '$PI_DIR/update.sh'"
    echo ""
    echo -e "${BLUE}To deploy updates in the future:${NC}"
    echo -e "   1. Run this script again: ./deploy.sh"
    echo -e "   2. Or use the update script on Pi: ssh $PI_HOST '$PI_DIR/update.sh'"
}

# --- Main execution ---
print_header

# Check if PI_HOST is set
if [ -z "$PI_HOST" ]; then
    echo -e "${YELLOW}⚠️  PI_HOST not set. Using default: pi@192.168.4.41${NC}"
    echo -e "${YELLOW}   Set PI_HOST environment variable to customize${NC}"
    echo -e "${YELLOW}   Example: PI_HOST=pi@192.168.1.50 ./deploy.sh${NC}"
    echo ""
fi

check_ssh
create_pi_directory
copy_files
setup_pi_environment
setup_database
create_service_file
enable_service
check_service_status
create_update_script
print_final_instructions

ssh pi@192.168.4.41 "pkill -f 'python.*main.py'; cd /home/pi/HomeBase && source venv/bin/activate && nohup python main.py > app.log 2>&1 &"
uvicorn app.main:app --reload --log-level debug 