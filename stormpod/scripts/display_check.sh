#!/usr/bin/env bash
# Detect likely touch device and ensure identity transform at 1024x600

if ! command -v xinput >/dev/null 2>&1; then exit 0; fi

DEV="$(xinput list --name-only | grep -i -m1 -E 'wave|touch|ft5|goodix|usb touch')"
if [[ -n "$DEV" ]]; then
  # Identity matrix; adjust if you set display_lcd_rotate in /boot/config.txt
  xinput set-prop "$DEV" 'Coordinate Transformation Matrix' 1 0 0  0 1 0  0 0 1
fi
