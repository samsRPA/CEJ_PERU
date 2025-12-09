#!/bin/sh

apk add --no-cache autossh openssh

chmod 600 "$SSH_KEY_PATH"

export AUTOSSH_LOGLEVEL=1
export AUTOSSH_DEBUG=0

echo "[INFO] Iniciando túnel SSH..."

# Ejecuta autossh en segundo plano
autossh -v -f -M 0 -i "$SSH_KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=2 \
    -o ExitOnForwardFailure=yes \
    -N -L 0.0.0.0:$TUNNEL_PORT:$DB_INTERNAL:$TUNNEL_PORT \
    ec2-user@$SSH_HOST

STATUS=$?
if [ $STATUS -eq 0 ]; then
    echo "[SUCCESS] Túnel SSH establecido exitosamente 🎉"
else
    echo "[ERROR] autossh terminó con código $STATUS"
    exit $STATUS
fi

# Mantiene el contenedor corriendo
tail -f /dev/null
