param(
    [int]$PostgresPort = 5433,
    [int]$RedisPort = 6379,
    [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

function Test-PortReady {
    param(
        [string]$TargetHost,
        [int]$Port
    )

    try {
        return (Test-NetConnection -ComputerName $TargetHost -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
    } catch {
        return $false
    }
}

function Wait-PortReady {
    param(
        [string]$Name,
        [string]$TargetHost,
        [int]$Port,
        [int]$Timeout
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortReady -TargetHost $TargetHost -Port $Port) {
            Write-Host "$Name is ready on $TargetHost`:$Port"
            return
        }
        Start-Sleep -Seconds 2
    }

    throw "$Name did not become ready on $TargetHost`:$Port within $Timeout seconds."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI not found. Install Docker Desktop first."
}

$dockerReady = $false
try {
    docker version | Out-Null
    $dockerReady = $true
} catch {
    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerDesktop)) {
        throw "Docker Desktop is not available and daemon is not running."
    }
    Write-Host "Starting Docker Desktop..."
    Start-Process -FilePath $dockerDesktop | Out-Null
}

if (-not $dockerReady) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            docker version | Out-Null
            $dockerReady = $true
            break
        } catch {
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $dockerReady) {
    throw "Docker daemon did not become ready within $TimeoutSeconds seconds."
}

Write-Host "Starting PostgreSQL and Redis containers..."
docker compose up -d postgres redis | Out-Null

Wait-PortReady -Name "PostgreSQL" -TargetHost "127.0.0.1" -Port $PostgresPort -Timeout $TimeoutSeconds
Wait-PortReady -Name "Redis" -TargetHost "127.0.0.1" -Port $RedisPort -Timeout $TimeoutSeconds

Write-Host "Development infrastructure is ready."
