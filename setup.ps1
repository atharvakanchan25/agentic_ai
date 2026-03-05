# University Timetable Management System Setup Script
Write-Host "Setting up University Timetable Management System..." -ForegroundColor Green

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.([0-9]+)") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 10) {
            Write-Host "Python 3.10+ required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v([0-9]+)") {
        $majorVersion = [int]$matches[1]
        if ($majorVersion -lt 18) {
            Write-Host "Node.js 18+ required. Found: $nodeVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Setup backend
Write-Host "Setting up backend..." -ForegroundColor Yellow
Set-Location backend

# Install Python dependencies
Write-Host "Installing Python dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Initialize database
Write-Host "Initializing database..."
python seed_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to initialize database" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Backend setup complete" -ForegroundColor Green

# Setup frontend
Write-Host "Setting up frontend..." -ForegroundColor Yellow
Set-Location ..\frontend

# Install Node dependencies
Write-Host "Installing Node.js dependencies..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install Node.js dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Frontend setup complete" -ForegroundColor Green

# Return to root
Set-Location ..

Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "1. Backend: cd backend && python main.py" -ForegroundColor White
Write-Host "2. Frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Then open http://localhost:5173 in your browser" -ForegroundColor Cyan