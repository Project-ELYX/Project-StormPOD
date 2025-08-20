#!/usr/bin/env bash
set -euo pipefail

# ── 0) sanity
if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash $0"; exit 1
fi

PROJECT_DIR="${PROJECT_DIR:-/home/pi/stormpod}"
PYTHON="${PYTHON:-python3}"
USER_NAME="${SUDO_USER:-pi}"
GROUP_NAME="${GROUP_NAME:-pi}"

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# ── 1) system enablements (i2c/spi/serial) ─────────────────────────────────────
apt-get update
apt-get install -y --no-install-recommends \
  git python3 python3-venv python3-pip python3-dev \
  python3-rpi.gpio python3-spidev python3-serial \
  i2c-tools can-utils net-tools

# Non-interactive raspi-config toggles (if present)
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_i2c 0 || true
  raspi-config nonint do_spi 0 || true
  raspi-config nonint do_serial 2 || true  # disable login shell, keep serial hw
fi

# Ensure groups
usermod -aG spi,i2c,gpio,dialout "$USER_NAME" || true

# ── 2) python venv + pip deps ──────────────────────────────────────────────────
sudo -u "$USER_NAME" bash -lc "
  cd '$PROJECT_DIR'
  $PYTHON -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip wheel
  pip install -r requirements.txt
"

# ── 3) udev tweaks for serial/spi (optional; usually group perms suffice) ──────
cat >/etc/udev/rules.d/99-stormpod.rules <<'UDEV'
KERNEL=="spidev*", MODE="0660", GROUP="spi"
KERNEL=="ttyAMA0", MODE="0660", GROUP="dialout"
KERNEL=="ttyS0",   MODE="0660", GROUP="dialout"
KERNEL=="serial0", MODE="0660", GROUP="dialout"
UDEV
udevadm control --reload-rules && udevadm trigger

# ── 4) CAN (socketcan) service ─────────────────────────────────────────────────
mkdir -p "$PROJECT_DIR/services"
cat >"$PROJECT_DIR/services/stormpod-can.service" <<'UNIT'
[Unit]
Description=StormPOD bring-up CAN0 @500k
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -lc 'ip link set can0 down 2>/dev/null || true; ip link add dev can0 type can bitrate 500000; ip link set up can0'
ExecStop=/bin/bash -lc 'ip link set can0 down || true'

[Install]
WantedBy=multi-user.target
UNIT
# ── 5) Lightning IRQ systemd unit (BCM 17 version in tools/) ───────────────────
cat >"$PROJECT_DIR/services/stormpod-irq.service" <<UNIT
[Unit]
Description=StormPOD AS3935 IRQ listener (SPI+IRQ)
After=network.target

[Service]
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PROJECT_DIR/.venv/bin/python tools/irq_listener.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT
# ── 6) System services install ────────────────────────────────────────────────
install -m 0644 "$PROJECT_DIR/services/stormpod-can.service" /etc/systemd/system/
install -m 0644 "$PROJECT_DIR/services/stormpod-irq.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable stormpod-can.service stormpod-irq.service
systemctl start  stormpod-can.service || true
# Do not auto-start if SPI wiring not attached; comment the next line if needed
systemctl start  stormpod-irq.service || true

# ── 7) Dev convenience ─────────────────────────────────────────────────────────
mkdir -p "$PROJECT_DIR/scripts"
cat >"$PROJECT_DIR/scripts/devenv.sh" <<'ENVH'
#!/usr/bin/env bash
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$THIS_DIR/.venv/bin/activate"
export PYTHONPATH="$THIS_DIR:$PYTHONPATH"
echo "StormPOD venv activated."
ENVH
chmod +x "$PROJECT_DIR/scripts/devenv.sh"
chmod +x scripts/display-check.sh
# ── 8) GUI Autostart Configuraton ──────────────────────────────────────────────
# Assumes PROJECT_DIR and USER_NAME were set earlier in this script.
TARGET_USER="${SUDO_USER:-$USER_NAME}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
AUTOSTART_DIR="$TARGET_HOME/.config/lxsession/LXDE-pi"

# Ensure helper script exists (touch alignment); safe to overwrite
install -d -o "$TARGET_USER" -g "$TARGET_USER" "$PROJECT_DIR/scripts"
cat >"$PROJECT_DIR/scripts/display-check.sh" <<'DISPLAYFIX'
#!/usr/bin/env bash
# Map likely touch HID to panel; identity matrix (adjust if you rotate screen)
if ! command -v xinput >/dev/null 2>&1; then exit 0; fi
DEV="$(xinput list --name-only | grep -i -m1 -E 'wave|touch|ft5|goodix|usb touch')"
if [[ -n "$DEV" ]]; then
  xinput set-prop "$DEV" 'Coordinate Transformation Matrix' 1 0 0  0 1 0  0 0 1
fi
DISPLAYFIX
chown "$TARGET_USER:$TARGET_USER" "$PROJECT_DIR/scripts/display-check.sh"
chmod +x "$PROJECT_DIR/scripts/display-check.sh"

# Create LXDE autostart to launch StormPOD GUI at login
install -d -o "$TARGET_USER" -g "$TARGET_USER" "$AUTOSTART_DIR"
cat >"$AUTOSTART_DIR/autostart" <<'AUTOSTART'
@bash -lc "cd ~/stormpod && ./scripts/devenv.sh && ./scripts/display-check.sh && python gui_main.py"
AUTOSTART
chown "$TARGET_USER:$TARGET_USER" "$AUTOSTART_DIR/autostart"

# ── 9) Done ────────────────────────────────────────────────────────────────────
echo "Setup complete. Reboot recommended."
