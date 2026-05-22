param(
    [string]$Action,
    [string]$AgentId,
    [string]$Task = "",
    [string]$Files = ""
)

$coordFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".COORDINATION.json"

function Read-Coordination {
    if (Test-Path $coordFile) {
        return Get-Content $coordFile -Raw | ConvertFrom-Json
    }
    return $null
}

function Write-Coordination {
    param($Data)
    $Data | ConvertTo-Json -Depth 4 | Set-Content $coordFile -Encoding UTF8
}

function Show-Status {
    $data = Read-Coordination
    if (-not $data) { Write-Host "No coordination file found"; return }

    Write-Host "`n=== SKYCAST AGENT COORDINATION ===" -ForegroundColor Cyan
    foreach ($agent in $data.agents.PSObject.Properties) {
        $a = $agent.Value
        $color = if ($a.status -eq "activo") { "Green" } else { "Gray" }
        Write-Host "  [$($agent.Name)]" -ForegroundColor $color -NoNewline
        Write-Host " status: $($a.status)" -ForegroundColor White -NoNewline
        if ($a.current_task) { Write-Host " | task: $($a.current_task)" -NoNewline }
        if ($a.files_touching.Count -gt 0) { Write-Host " | files: $($a.files_touching -join ', ')" -NoNewline }
        Write-Host ""
    }
    Write-Host "===============================`n" -ForegroundColor Cyan
}

function Claim-Files {
    param($AgentId, $Task, $Files)
    $data = Read-Coordination
    if (-not $data) { Write-Error "No coordination file"; return }

    $files = $Files -split ',' | ForEach-Object { $_.Trim() }

    # Check conflicts
    foreach ($agent in $data.agents.PSObject.Properties) {
        if ($agent.Name -eq $AgentId) { continue }
        $conflicts = $agent.Value.files_touching | Where-Object { $_ -in $files }
        if ($conflicts) {
            Write-Error "CONFLICT: $($agent.Name) ya está tocando: $($conflicts -join ', ')"
            return $false
        }
    }

    # Check if agent already exists
    if ($data.agents.$AgentId) {
        $data.agents.$AgentId.status = "activo"
        $data.agents.$AgentId.current_task = $Task
        $data.agents.$AgentId.files_touching = @($files)
        $data.agents.$AgentId.last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    } else {
        Write-Error "Agent '$AgentId' no reconocido. IDs válidos: opencode_1, opencode_2"
        return $false
    }

    Write-Coordination $data
    Write-Host "OK: $AgentId claimó '$Task' (files: $Files)" -ForegroundColor Green
    return $true
}

function Release-Agent {
    param($AgentId)
    $data = Read-Coordination
    if (-not $data) { return }

    if ($data.agents.$AgentId) {
        $data.agents.$AgentId.status = "inactivo"
        $data.agents.$AgentId.current_task = ""
        $data.agents.$AgentId.files_touching = @()
        $data.agents.$AgentId.last_updated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        Write-Coordination $data
        Write-Host "OK: $AgentId liberado" -ForegroundColor Yellow
    }
}

# --- MAIN ---
switch ($Action.ToLower()) {
    "claim"   { Claim-Files $AgentId $Task $Files }
    "release" { Release-Agent $AgentId }
    "status"  { Show-Status }
    default   {
        Write-Host "Uso: .\scripts\coordinate.ps1 [claim|release|status] [agent_id] [task] [files]"
        Write-Host ""
        Write-Host "Ejemplos:"
        Write-Host "  .\scripts\coordinate.ps1 status"
        Write-Host "  .\scripts\coordinate.ps1 claim opencode_1 'Fix AEMET encoding' app/services/aemet_service.py"
        Write-Host "  .\scripts\coordinate.ps1 release opencode_1"
    }
}
