# bench_ollama.ps1
# Benchmark Qwen3 4B via Ollama: latency, tokens/s, VRAM

param(
    [string]$Model = "qwen3:4b"
)

$ErrorActionPreference = "Stop"
$outFile = "C:\Projects\ai-english-tutor\benchmark-results\ollama-benchmark.json"

Write-Host "=== Ollama Benchmark: $Model ===" -ForegroundColor Cyan
Write-Host "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# --- Warm up ---
Write-Host "Warming up model..." -ForegroundColor Yellow
$warmupBody = @{
    model = $Model
    prompt = "Say 'ready' in one word."
    stream = $false
    think = $false
} | ConvertTo-Json -Depth 5

$swWarm = [System.Diagnostics.Stopwatch]::StartNew()
$respWarm = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $warmupBody -ContentType "application/json"
$swWarm.Stop()
Write-Host "Warmup time: $($swWarm.Elapsed.TotalSeconds) sec"
Write-Host ""

# --- Test 1: English teaching ---
Write-Host "Test 1: English teaching explanation..." -ForegroundColor Yellow
$prompt1 = "Explain the difference between Present Perfect and Past Simple in English, in 3 short sentences."
$body1 = @{
    model = $Model
    prompt = $prompt1
    stream = $false
    think = $false
    options = @{ num_predict = 200 }
} | ConvertTo-Json -Depth 5

$sw1 = [System.Diagnostics.Stopwatch]::StartNew()
$resp1 = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $body1 -ContentType "application/json"
$sw1.Stop()

# --- Test 2: Persian explanation ---
Write-Host "Test 2: Persian explanation..." -ForegroundColor Yellow
$prompt2 = "Please explain in Persian (Farsi) the difference between Present Perfect and Past Simple. (Max 3 sentences)"
$body2 = @{
    model = $Model
    prompt = $prompt2
    stream = $false
    think = $false
    options = @{ num_predict = 200 }
} | ConvertTo-Json -Depth 5

$sw2 = [System.Diagnostics.Stopwatch]::StartNew()
$resp2 = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $body2 -ContentType "application/json"
$sw2.Stop()

# --- Test 3: Structured JSON output ---
Write-Host "Test 3: Structured JSON output..." -ForegroundColor Yellow
$prompt3 = @"
Return ONLY valid JSON (no markdown, no explanation) with this structure:
{"correction": "string", "explanation_fa": "string", "example": "string"}
Correct this sentence: "I have went to the store yesterday."
"@
$body3 = @{
    model = $Model
    prompt = $prompt3
    stream = $false
    think = $false
    format = "json"
    options = @{ num_predict = 300 }
} | ConvertTo-Json -Depth 5

$sw3 = [System.Diagnostics.Stopwatch]::StartNew()
$resp3 = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $body3 -ContentType "application/json"
$sw3.Stop()

# --- VRAM monitoring during a longer generation ---
Write-Host "Measuring peak VRAM during generation..." -ForegroundColor Yellow
$vramSamples = @()
$vramJob = Start-Job -ScriptBlock {
    $samples = @()
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $out = & nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>$null
            if ($out) { $samples += [int]$out.Trim() }
        } catch {}
        Start-Sleep -Milliseconds 200
    }
    return $samples
}

$bodyLong = @{
    model = $Model
    prompt = "Write a 200-word English essay about learning languages."
    stream = $false
    think = $false
    options = @{ num_predict = 300 }
} | ConvertTo-Json -Depth 5
$respLong = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -Body $bodyLong -ContentType "application/json"

Wait-Job $vramJob -Timeout 10 | Out-Null
$vramSamples = Receive-Job $vramJob
Remove-Job $vramJob -Force

$peakVRAM = if ($vramSamples.Count -gt 0) { ($vramSamples | Measure-Object -Maximum).Maximum } else { 0 }

# --- Results ---
$results = [PSCustomObject]@{
    timestamp          = (Get-Date).ToString("o")
    model              = $Model
    warmup_seconds     = [math]::Round($swWarm.Elapsed.TotalSeconds, 2)
    test1_english_s    = [math]::Round($sw1.Elapsed.TotalSeconds, 2)
    test1_tokens       = $resp1.eval_count
    test1_tokens_per_s = if ($sw1.Elapsed.TotalSeconds -gt 0) { [math]::Round($resp1.eval_count / $sw1.Elapsed.TotalSeconds, 2) } else { 0 }
    test1_output       = $resp1.response.Trim()
    test2_persian_s    = [math]::Round($sw2.Elapsed.TotalSeconds, 2)
    test2_tokens       = $resp2.eval_count
    test2_output       = $resp2.response.Trim()
    test3_json_s       = [math]::Round($sw3.Elapsed.TotalSeconds, 2)
    test3_valid_json   = ($resp3.response.Trim() -match '^\s*\{.*\}\s*$')
    test3_output       = $resp3.response.Trim()
    vram_peak_mb       = $peakVRAM
    vram_samples       = $vramSamples.Count
}

Write-Host "`n=== Results ===" -ForegroundColor Green
$results | Format-List

# Save to JSON
$resultsDir = Split-Path $outFile -Parent
if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null }
$results | ConvertTo-Json -Depth 5 | Out-File -FilePath $outFile -Encoding utf8
Write-Host "`nSaved to: $outFile" -ForegroundColor Green