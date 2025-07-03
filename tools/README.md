# Tools Directory

This directory contains deployment scripts, development tools, and configuration files for the HomeBase application.

## Deployment Scripts

### `deploy.sh`
Main deployment script for Raspberry Pi. Automates the entire deployment process.
```bash
./tools/deploy.sh
```

**Features:**
- SSH connection validation
- File synchronization
- Virtual environment setup
- Dependency installation
- Database initialization
- Systemd service creation
- Application startup

### `run_import_on_pi.sh`
Runs data import on Raspberry Pi deployment.
```bash
./tools/run_import_on_pi.sh
```

## Development Tools

### `dev.sh`
Development server startup script with hot reload.
```bash
./tools/dev.sh
```

**Features:**
- Virtual environment activation
- Development server startup
- Hot reload enabled
- Port 8000 configuration
- Debug mode enabled

## Configuration Files

### `deploy-config.env`
Deployment configuration template.
```bash
# Copy and customize for your deployment
cp tools/deploy-config.env .env
```

**Configuration Options:**
- `PI_HOST`: Raspberry Pi SSH connection string
- `PI_PORT`: SSH port (default: 22)
- `APP_PORT`: Application port (default: 8001)
- `PI_USER`: Pi username (default: pi)

## Usage

### Local Development
```bash
# Start development server
./tools/dev.sh

# Or manually
source venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```bash
# Configure deployment
export PI_HOST=pi@192.168.1.50  # Replace with your Pi's IP

# Deploy
./tools/deploy.sh
```

### Custom Deployment
```bash
# Use custom configuration
cp tools/deploy-config.env .env
# Edit .env with your settings
source .env
./tools/deploy.sh
```

## Deployment Process

### Prerequisites
1. Raspberry Pi running Raspberry Pi OS
2. SSH access to Pi (password or SSH key)
3. Network connectivity
4. Sufficient disk space (~500MB)

### Deployment Steps
1. **Validation**: Check SSH connection and Pi status
2. **File Sync**: Copy project files (excluding venv and database)
3. **Environment**: Set up Python virtual environment
4. **Dependencies**: Install all required packages
5. **Database**: Initialize database and seed categories
6. **Service**: Create and enable systemd service
7. **Startup**: Start the application

### Post-Deployment
- Application available at `http://YOUR_PI_IP:8001`
- Service auto-starts on boot
- Logs available via `sudo journalctl -u homebase -f`

## Management Commands

### Service Management
```bash
# Check status
ssh pi@YOUR_PI_IP 'sudo systemctl status homebase'

# View logs
ssh pi@YOUR_PI_IP 'sudo journalctl -u homebase -f'

# Restart service
ssh pi@YOUR_PI_IP 'sudo systemctl restart homebase'

# Stop service
ssh pi@YOUR_PI_IP 'sudo systemctl stop homebase'
```

### Updates
```bash
# Full redeploy
./tools/deploy.sh

# Quick update (if using git)
ssh pi@YOUR_PI_IP '/home/pi/HomeBase/update.sh'
```

## Troubleshooting

### Common Issues
1. **SSH Connection**: Verify Pi is powered on and connected
2. **Port Conflicts**: Check if port 8001 is available
3. **Permission Issues**: Ensure proper file permissions
4. **Python Version**: Verify Python 3.9+ is installed

### Debug Mode
```bash
# Enable debug output
DEBUG=1 ./tools/deploy.sh
```

### Manual Deployment
If automated deployment fails:
1. SSH to Pi manually
2. Clone/copy project files
3. Set up virtual environment
4. Install dependencies
5. Initialize database
6. Start application manually

## Security Considerations

- **Firewall**: Configure firewall on Pi
- **SSH Keys**: Use SSH keys instead of passwords
- **HTTPS**: Set up SSL/TLS for production
- **Updates**: Keep system and dependencies updated 