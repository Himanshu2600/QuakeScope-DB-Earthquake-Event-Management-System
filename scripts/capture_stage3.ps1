# capture_stage3.ps1
# Automated capture of Stage 3 Dashboard Screenshots using Microsoft Edge Headless

$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$outDir = "C:\quakescopedb\screenshots\stage3"

if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir
}

$shots = @(
    @{
        name = "01_dashboard_overview.png";
        url = "http://127.0.0.1:5000/#overview";
        width = "1400";
        height = "900"
    },
    @{
        name = "02_analytics_charts.png";
        url = "http://127.0.0.1:5000/#analytics";
        width = "1400";
        height = "980"
    },
    @{
        name = "03_earthquake_explorer.png";
        url = "http://127.0.0.1:5000/#explorer";
        width = "1400";
        height = "920"
    },
    @{
        name = "04_manage_events.png";
        url = "http://127.0.0.1:5000/#manage";
        width = "1400";
        height = "920"
    },
    @{
        name = "05_backend_verification.png";
        url = "http://127.0.0.1:5000/api/health";
        width = "1200";
        height = "700"
    },
    @{
        name = "06_detail_view.png";
        url = "http://127.0.0.1:5000/?event=us6000qw60";
        width = "1400";
        height = "900"
    }
)

foreach ($s in $shots) {
    $targetPath = Join-Path $outDir $s.name
    Write-Host "Capturing $($s.name)..."
    
    $args = @(
        "--headless=new",
        "--disable-gpu",
        "--window-size=$($s.width),$($s.height)",
        "--virtual-time-budget=3500",
        "--screenshot=$targetPath",
        $s.url
    )
    
    Start-Process $edge -ArgumentList $args -Wait
    
    if (Test-Path $targetPath) {
        $size = (Get-Item $targetPath).Length
        Write-Host "  -> [SUCCESS] Saved $($s.name) ($([math]::Round($size / 1024, 1)) KB)"
    } else {
        Write-Host "  -> [FAILED] Could not capture $($s.name)"
    }
}
