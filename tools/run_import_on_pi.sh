#!/bin/bash
set -e

# --- Configuration ---
PI_HOST="${PI_HOST:-pi@192.168.4.41}"  # Update this to your Pi's IP
PI_DIR="${PI_DIR:-/home/pi/HomeBase}"

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Running Calendar Import on Pi 🚀${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}📡 Connecting to Pi and running import...${NC}"
ssh "$PI_HOST" "cd $PI_DIR && source venv/bin/activate && python prod_import_events.py"

echo ""
echo -e "${GREEN}✅ Import completed!${NC}"
echo ""
echo -e "${BLUE}📊 To check the import log:${NC}"
echo -e "   ssh $PI_HOST 'tail -f $PI_DIR/import_events.log'"
echo ""
echo -e "${BLUE}🌐 View your calendar at:${NC}"
echo -e "   http://$(ssh $PI_HOST 'hostname -I | awk "{print \$1}"'):8001" 