#!/bin/bash
# StreamSniper Installer
# Run with: bash install.sh

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗"
echo "  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║"
echo "  ███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║"
echo "  ╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║"
echo "  ███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║"
echo "  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝"
echo -e "${NC}"
echo -e "${CYAN}  StreamSniper Installer${NC}"
echo "  ─────────────────────────────────────────"
echo ""

# Check running as non-root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}❌ Don't run this as root. Run as your normal user.${NC}"
  exit 1
fi

USERNAME=$(whoami)
INSTALL_DIR="$HOME/streamsniper"

echo -e "${YELLOW}📦 Installing system packages...${NC}"
sudo apt-get update -qq
sudo apt-get install -y \
  streamlink \
  vlc \
  python3-pygame \
  x11-xserver-utils \
  python3 \
  --no-install-recommends

echo ""
echo -e "${YELLOW}📁 Installing StreamSniper files...${NC}"
mkdir -p "$INSTALL_DIR"
cp sniper.py "$INSTALL_DIR/"
cp standby.py "$INSTALL_DIR/"
cp config.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/sniper.py"
chmod +x "$INSTALL_DIR/standby.py"

echo ""
echo -e "${YELLOW}🔧 Installing systemd service...${NC}"
sudo cp streamsniper@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable streamsniper@${USERNAME}.service

echo ""
echo -e "${YELLOW}📋 Creating log directory...${NC}"
mkdir -p "$HOME/.streamsniper"

CHANNELS_FILE="$HOME/.streamsniper/channels.txt"
echo ""
echo -e "${YELLOW}📺 Which Twitch channel(s) should it watch?${NC}"
echo "  Separate several with spaces or commas."
echo "  Order is priority — if two are live, the first one gets the screen."
echo "  Press Enter to skip and edit the file yourself later."
echo ""
read -r -p "  Channels: " CHANNEL_INPUT

{
  echo "# StreamSniper — channels to watch"
  echo "#"
  echo "# One Twitch username per line. Order is priority."
  echo "# Lines starting with # are ignored."
  echo "# Edits apply at the next check — no restart needed."
  echo ""
  if [ -n "$CHANNEL_INPUT" ]; then
    echo "$CHANNEL_INPUT" | tr ',' '\n' | tr ' ' '\n' | sed '/^$/d' | tr '[:upper:]' '[:lower:]'
  fi
} > "$CHANNELS_FILE"

if [ -n "$CHANNEL_INPUT" ]; then
  echo -e "${GREEN}  ✓ Saved to $CHANNELS_FILE${NC}"
else
  echo -e "${YELLOW}  ! No channels set. Add them to $CHANNELS_FILE before starting.${NC}"
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "  To start now:     sudo systemctl start streamsniper@${USERNAME}"
echo "  To check status:  sudo systemctl status streamsniper@${USERNAME}"
echo "  To watch logs:    tail -f ~/.streamsniper/sniper.log"
echo "  To stop:          sudo systemctl stop streamsniper@${USERNAME}"
echo "  To disable boot:  sudo systemctl disable streamsniper@${USERNAME}"
echo ""
WATCHING=$(grep -v '^\s*#' "$CHANNELS_FILE" 2>/dev/null | sed '/^\s*$/d' | paste -sd ', ' -)
echo -e "${CYAN}  Watching: ${WATCHING:-nothing yet} — checking every 5 minutes${NC}"
echo -e "${CYAN}  Change anytime: $CHANNELS_FILE${NC}"
echo ""
