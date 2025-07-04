#!/bin/bash
set -e

# --- Configuration ---
PI_HOST="${PI_HOST:-pi@192.168.4.41}"  # Update this to your Pi's IP
PI_DIR="${PI_DIR:-/home/pi/HomeBase}"

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Running Fuzzy Match Cleanup on Pi 🧹${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if arguments were provided
if [ "$1" = "--execute" ]; then
    echo -e "${YELLOW}⚠️  LIVE MODE - Will actually remove duplicates${NC}"
    CLEANUP_ARGS="--execute"
elif [ "$1" = "--dry-run" ]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE - Will only show what would be removed${NC}"
    CLEANUP_ARGS=""
else
    echo -e "${YELLOW}🔍 DRY RUN MODE - Will only show what would be removed${NC}"
    echo -e "${YELLOW}   Use --execute to actually remove duplicates${NC}"
    echo -e "${YELLOW}   Use --dry-run to explicitly run in dry-run mode${NC}"
    echo ""
    CLEANUP_ARGS=""
fi

echo ""
echo -e "${YELLOW}📡 Connecting to Pi and running cleanup...${NC}"

# Run the cleanup script on the Pi
ssh "$PI_HOST" "cd $PI_DIR && source venv/bin/activate && PYTHONPATH=$PI_DIR python scripts/cleanup_ios_duplicates_advanced.py --local $CLEANUP_ARGS"

echo ""
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo ""
echo -e "${BLUE}📊 To check the cleanup results:${NC}"
echo -e "   ssh $PI_HOST 'cd $PI_DIR && source venv/bin/activate && PYTHONPATH=$PI_DIR python scripts/cleanup_ios_duplicates_advanced.py --local'"
echo ""
echo -e "${BLUE}🌐 View your calendar at:${NC}"
echo -e "   http://$(ssh $PI_HOST 'hostname -I | awk "{print \$1}"'):8001" 