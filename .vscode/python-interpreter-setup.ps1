# Python 解釋器設定腳本
Write-Host "設定 Python 解釋器..." -ForegroundColor Green

$workspaceRoot = Get-Location
$pythonPath = Join-Path $workspaceRoot "backend\.venv\Scripts\python.exe"

Write-Host "工作區路徑: $workspaceRoot" -ForegroundColor Yellow
Write-Host "Python 路徑: $pythonPath" -ForegroundColor Yellow

if (Test-Path $pythonPath) {
    Write-Host "✅ Python 解釋器找到: $pythonPath" -ForegroundColor Green
    
    # 測試 Python 版本
    & $pythonPath --version
    
    Write-Host "`n📝 請在 VS Code 中:" -ForegroundColor Cyan
    Write-Host "1. 按 Ctrl+Shift+P" -ForegroundColor White
    Write-Host "2. 輸入 'Python: Select Interpreter'" -ForegroundColor White
    Write-Host "3. 選擇: $pythonPath" -ForegroundColor White
    Write-Host "4. 然後按 F5 啟動 debug" -ForegroundColor White
} else {
    Write-Host "❌ Python 解釋器未找到: $pythonPath" -ForegroundColor Red
    Write-Host "請先運行: cd backend && uv sync" -ForegroundColor Yellow
}