# HomeBase Deployment Guide

## 🚀 Quick Deployment to Raspberry Pi

### Prerequisites

1. **Raspberry Pi Setup**
   - Pi running Raspberry Pi OS (or similar Linux)
   - SSH enabled
   - Connected to your network
   - IP address known

2. **Local Machine Setup**
   - SSH access to Pi (password or SSH key)
   - This HomeBase project directory

### Step 1: Configure Deployment

1. **Find your Pi's IP address:**
   ```bash
   # On Pi or router admin panel
   hostname -I
   ```

2. **Set the Pi's IP in the deployment script:**
   ```bash
   # Option 1: Set environment variable
   export PI_HOST=pi@192.168.1.50  # Replace with your Pi's IP
   
   # Option 2: Edit deploy-config.env and source it
   cp deploy-config.env .env
   # Edit .env with your Pi's IP
   source .env
   ```

### Step 2: Deploy

```bash
# Make sure you're in the HomeBase directory
cd /path/to/HomeBase

# Run the deployment script
./tools/deploy.sh
```

The script will:
- ✅ Check SSH connection to Pi
- ✅ Copy all project files (excluding venv and database)
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Initialize database with categories
- ✅ Create systemd service for auto-start
- ✅ Start the application

### Step 3: Access Your Application

After deployment, your HomeBase Calendar will be available at:
```
http://YOUR_PI_IP:8001
```

Example: `http://192.168.1.50:8001`

## 🔧 Management Commands

### Check Status
```bash
ssh pi@YOUR_PI_IP 'sudo systemctl status homebase'
```

### View Logs
```bash
ssh pi@YOUR_PI_IP 'sudo journalctl -u homebase -f'
```

### Restart Application
```bash
ssh pi@YOUR_PI_IP 'sudo systemctl restart homebase'
```

### Stop Application
```bash
ssh pi@YOUR_PI_IP 'sudo systemctl stop homebase'
```

## 🔄 Updating the Application

### Option 1: Full Redeploy
```bash
./tools/deploy.sh
```

### Option 2: Quick Update (if using git)
```bash
ssh pi@YOUR_PI_IP '/home/pi/HomeBase/update.sh'
```

## 🛠️ Troubleshooting

### SSH Connection Issues
- Verify Pi is powered on and connected to network
- Check SSH is enabled: `sudo raspi-config` → Interface Options → SSH
- Test connection: `ssh pi@YOUR_PI_IP`

### Port Issues
- Check if port 8001 is available: `sudo netstat -tlnp | grep 8001`
- Change port in `deploy-config.env` if needed

### Service Issues
- Check service status: `sudo systemctl status homebase`
- View detailed logs: `sudo journalctl -u homebase -n 50`

### Python/Dependency Issues
- Reinstall dependencies: `source venv/bin/activate && pip install -r requirements.txt`
- Check Python version: `python3 --version`

## 📁 File Structure on Pi

After deployment, your Pi will have:
```
/home/pi/HomeBase/
├── app/                    # FastAPI application
├── frontend/              # Templates and static files
├── venv/                  # Python virtual environment
├── database.db            # SQLite database
├── requirements.txt       # Python dependencies
├── dev.sh                 # Development script
├── deploy.sh              # Deployment script
├── update.sh              # Update script (created by deploy)
└── ... (other project files)
```

## 🔒 Security Considerations

- **Firewall**: Consider setting up a firewall on your Pi
- **HTTPS**: For production, set up SSL/TLS certificates
- **Authentication**: Add user authentication if needed
- **Backups**: Regularly backup your `database.db` file

## 🎯 Next Steps

1. **Test the application** - Visit the web interface
2. **Configure iCloud sync** - Update the calendar URL in settings
3. **Set up automatic backups** - Create a cron job for database backups
4. **Monitor logs** - Set up log rotation and monitoring 