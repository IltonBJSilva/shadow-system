# Shadow System: abre em http://localhost:5050
#   .\run.ps1          modo normal (waitress)
#   .\run.ps1 --dev    modo desenvolvimento (recarrega ao salvar, mostra erros detalhados)
#
# Na primeira vez: cria o .venv, instala as dependências, cria o .env a partir do .env.example
# (com uma SECRET_KEY aleatória) e cria o banco. Nas próximas, só aplica migrations novas e abre.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "[SYSTEM] Criando ambiente Python (.venv)..."
    python -m venv .venv
    .\.venv\Scripts\python -m pip install --quiet --upgrade pip
}
.\.venv\Scripts\python -m pip install --quiet -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "[SYSTEM] Criando .env a partir do .env.example..."
    $secret = .\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
    (Get-Content .env.example) -replace "^SECRET_KEY=.*", "SECRET_KEY=$secret" | Set-Content .env -Encoding utf8
}

Write-Host "[SYSTEM] Atualizando banco de dados..."
.\.venv\Scripts\flask --app wsgi db upgrade

if ($args -contains "--dev") {
    $env:SHADOW_ENV = "development"
    Start-Process "http://localhost:5050"
    .\.venv\Scripts\flask --app wsgi run --debug --port 5050
} else {
    Start-Process "http://localhost:5050"
    Write-Host "[SYSTEM] Shadow System rodando em http://localhost:5050 (Ctrl+C para parar)"
    .\.venv\Scripts\waitress-serve --listen=127.0.0.1:5050 --call app:create_app
}
