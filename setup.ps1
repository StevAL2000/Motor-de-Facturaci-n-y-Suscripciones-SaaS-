<#
setup.ps1
Script sencillo para crear el entorno virtual `.env` con Python 3.12 y (opcionalmente) instalar `requirements.txt`.
#>


# =============================
# setup.ps1 mejorado: permite elegir nombre de entorno
# Uso: .\setup.ps1 [nombre_entorno]
# Por defecto crea .env si no se pasa argumento
# =============================

param(
    [string]$venv = ".env"
)

Write-Host "== Setup: crear venv '$venv' e instalar dependencias =="

# Eliminar el entorno si ya existe (opcional, descomentar si se desea)
# if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }

# Intentar crear el venv con py -3.12 si existe, si no usar python
$created = $false
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        py -3.12 -m venv $venv
        $created = $true
        Write-Host "Entorno creado con 'py -3.12'"
    } catch {
        Write-Host "Fallo crear con 'py -3.12' – intentando con 'python'..."
    }
}

if (-not $created) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            python -m venv $venv
            $created = $true
            Write-Host "Entorno creado con 'python'"
        } catch {
            Write-Host "Fallo crear entorno con 'python'."
        }
    } else {
        Write-Host "No se encontró 'py' ni 'python' en PATH. Instala Python 3.12 y vuelve a intentarlo."
        exit 1
    }
}

if (-not (Test-Path $venv)) {
    Write-Host "No se pudo crear el entorno $venv. Salir."
    exit 1
}

# Actualizar pip y herramientas
Write-Host "Actualizando pip..."
$pyexe = Join-Path $venv "Scripts\python.exe"
& $pyexe -m pip install --upgrade pip setuptools wheel -q

# Instalar requirements.txt si existe
if (Test-Path .\requirements.txt) {
    Write-Host "Instalando dependencias desde requirements.txt..."
    & $pyexe -m pip install -r .\requirements.txt
} else {
    Write-Host "No se encontró requirements.txt — Salta instalación de dependencias."
}

Write-Host "Listo. Para usar el entorno, activa con: .\\$venv\\Scripts\\Activate.ps1 (PowerShell) o .\\$venv\\Scripts\\activate.bat (CMD)."
Write-Host "Si PowerShell bloquea scripts: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\\setup.ps1"
