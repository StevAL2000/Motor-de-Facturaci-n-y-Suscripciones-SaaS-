# Motor-de-Facturaci-n-y-Suscripciones-SaaS-
Escenario del Proyecto: Una empresa SaaS ficticia necesita automatizar su ciclo de vida de facturación y suscripciones. El sistema debe gestionar recordatorios de prueba, procesar renovaciones, manejar reintentos de pago fallido (dunning) y permitir a los clientes ver el estado de su suscripción en un portal.

## Reproducción del entorno (Windows)

Estas instrucciones ayudan a crear un entorno virtual y a instalar las dependencias listadas en `requirements.txt`.

### Requisitos
- Python 3.12 instalado (recomendado usar el lanzador `py` en Windows).

### Crear y activar el entorno virtual

PowerShell (recomendado):

```powershell
# Crear env (usa py -3.12 si está disponible, fallback a python)
py -3.12 -m venv .env 2>$null || python -m venv .env

# Activar (PowerShell)
.\.env\Scripts\Activate.ps1

# Para desactivar
deactivate
```

CMD (símbolo del sistema):

```cmd
py -3.12 -m venv .env || python -m venv .env
.env\Scripts\activate.bat
```

### Instalar dependencias

Con el entorno activado:

```powershell
pip install -r requirements.txt
```

Sin activar (usa el python del venv directamente):

```powershell
.\.env\Scripts\python.exe -m pip install -r requirements.txt
```

### Uso rápido

```powershell
# Ejecutar el script principal
.\.env\Scripts\python.exe main.py
```

### Script de ayuda (PowerShell)

Ejecuta `.\setup.ps1` para crear el entorno e instalar dependencias automáticamente. El script no activa el entorno en la sesión padre (por restricciones de ejecución de scripts), pero deja todo listo; después puedes activar manualmente.

### Actualizar `requirements.txt`

Si instalas o actualizas paquetes, genera un nuevo `requirements.txt` con:

```powershell
.\.env\Scripts\python.exe -m pip freeze > requirements.txt
```

### Notas
- El repositorio incluye `.gitignore` que ya ignora `.env/`.
- Si tienes problemas con la ejecución de scripts en PowerShell, puedes ejecutar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\setup.ps1

## Despliegue en Render.com

Pasos mínimos para desplegar esta aplicación en Render usando el buildpack de Python:

1. Empuja tu repo a GitHub y conéctalo en Render.
2. En la creación del servicio web en Render:
	- Selecciona 'Web Service'.
	- En 'Build Command' puedes dejar vacío; Render instalará dependencias usando `requirements.txt`.
	- Asegúrate de que `requirements.txt` contenga `gunicorn` (ya está incluido).
	- El `Start Command` puede dejarse vacío si tienes un `Procfile` en la raíz (se usará automáticamente).
3. Revisa que `Procfile` exista y contenga la línea:

```
web: gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
```

4. Añade las variables de entorno necesarias en Render (Settings → Environment → Env Vars), por ejemplo `API_SECRET_KEY`.

5. Si necesitas forzar la versión de Python, `runtime.txt` está presente con `python-3.12.7`.

6. Logs y troubleshooting: revisa los logs de build/deploy en Render y ajusta el Procfile si tu app principal no se llama `app` o si `main.py` está dentro de un paquete.

Si quieres, puedo crear automáticamente la aplicación en Render vía su API, o validar el `Procfile` vs la estructura del proyecto antes de que hagas el deploy.
```

