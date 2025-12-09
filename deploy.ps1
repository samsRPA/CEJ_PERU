# Script que espera a que cada VPN reporte su IP publica en los logs

$COMPOSE_FILE = "docker-compose.yml"
$VPNS = @("vpn_00", "vpn_01", "vpn_02")
$WORKERS = @("worker_01", "worker_02", "worker_03")
$MAX_WAIT = 120

Write-Host "Levantando VPNs..." -ForegroundColor Green
docker-compose -f $COMPOSE_FILE up -d $VPNS

Write-Host "Esperando a que los VPNs reporte IP publica..." -ForegroundColor Yellow

foreach ($vpn in $VPNS) {
    Write-Host "  Checkeando $vpn..." -ForegroundColor Cyan
    $seconds = 0
    $connected = $false
    
    while ($seconds -lt $MAX_WAIT) {
        try {
            $logs = docker logs $vpn 2>$null
            
            if ($logs -match "Public IP address is (\d+\.\d+\.\d+\.\d+)") {
                $ip = $matches[1]
                Write-Host "  OK - $vpn conectado! IP: $ip" -ForegroundColor Green
                $connected = $true
                break
            }
        }
        catch {
            # Aun no tiene logs
        }
        
        Write-Host "    esperando... ($seconds/$MAX_WAIT)" -ForegroundColor Gray
        Start-Sleep -Seconds 3
        $seconds += 3
    }
    
    if (-not $connected) {
        Write-Host "  ERROR - $vpn no reporto IP!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Todos los VPNs conectados, levantando workers..." -ForegroundColor Green
docker-compose -f $COMPOSE_FILE up -d $WORKERS

Write-Host "LISTO! VPNs + Workers corriendo" -ForegroundColor Green
docker-compose -f $COMPOSE_FILE ps