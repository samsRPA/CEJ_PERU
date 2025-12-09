#!/bin/bash
echo "🔍 Instalando ChromeDriver compatible..."
CHROME_VERSION=$(google-chrome --version | grep -oP "\d+\.\d+\.\d+\.\d+")
CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d. -f1)
echo "Chrome: $CHROME_VERSION (major: $CHROME_MAJOR)"

DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_MAJOR")
echo "ChromeDriver: $DRIVER_VERSION"

wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/$DRIVER_VERSION/linux64/chromedriver-linux64.zip"
unzip /tmp/chromedriver.zip -d /tmp/
sudo mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

echo "✅ ChromeDriver instalado correctamente"
