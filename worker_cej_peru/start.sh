#!/bin/bash
set -e

# ChromeDriver
./install-chromedriver.sh

echo "🔍 Versiones instaladas:"
google-chrome --version
chromedriver --version

# Xvfb
display="${DISPLAY_NUM:-99}"
resolution="${RESOLUTION:-1920x1080x24}"

echo "🚀 Arrancando Xvfb en :${display} con resolución ${resolution}"

rm -f /tmp/.X${display}-lock /tmp/.X11-unix/X${display}

Xvfb :${display} -screen 0 ${resolution} &
export DISPLAY=:${display}

# Carpeta para undetected-chromedriver
mkdir -p ~/.local/share/undetected_chromedriver

python3 main.py
