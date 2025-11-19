import os
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware # <-- NUEVA IMPORTACIÓN DE CORS
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables de entorno (como API_SECRET_KEY) desde un archivo .env
load_dotenv()
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "UaLY_U0gkvXdsYjYof2pa1vEMnMgM") 
app = FastAPI()

# --- Configuración de CORS ---
# Esto es CRÍTICO para que el frontend pueda hacer llamadas fetch al microservicio.
origins = [
    # En desarrollo/prueba, se permite cualquier origen ("*").
    # En producción, se debería restringir a la URL exacta del portal del cliente (ej: "https://portal.midominio.com").
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True, # Permitir credenciales (como el Bearer Token)
    allow_methods=["*"],    # Permitir todos los métodos (GET, POST)
    allow_headers=["*"],    # Permitir todos los headers (incluyendo el de Authorization)
)
# --- Fin de Configuración de CORS ---

@app.get("/", include_in_schema=False)
async def root():
    """Raíz mínima: devuelve OK y la ruta a la documentación para facilitar pruebas."""
    return {"status": "ok", "message": "Service running", "docs": "/docs"}


@app.get("/health", include_in_schema=False)
async def health():
    """Health check rápido que devuelve 200 OK en texto plano."""
    return PlainTextResponse("OK", status_code=200)

# Configuración de Seguridad para el Bearer Token
security = HTTPBearer()

# --- 1. Modelos de Datos (Pydantic) ---

# Modelo para la data de suscripción que viene de n8n
class Subscription(BaseModel):
    user_id: str
    email: str
    plan_type: str
    status: str # 'trial', 'active', 'past_due', 'canceled'
    trial_ends_at: Optional[datetime] = None
    next_billing_at: Optional[datetime] = None
    last_payment_attempt: Optional[datetime] = None
    
# Modelo para la acción que se devuelve a n8n
class BillingAction(BaseModel):
    action: str
    user_id: str
    email: str # Se añade el email para facilitar la notificación en n8n


# --- 2. Middleware de Autenticación (Bearer Token) ---

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifica que el Bearer Token enviado en el encabezado sea correcto."""
    
    # Compara el token enviado con la clave secreta configurada.
    if credentials.scheme != "Bearer" or credentials.credentials != API_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Token Bearer inválido o no autorizado."
        )
    return credentials.credentials # La dependencia pasa si es exitoso

# Requerimos el token en este endpoint usando la dependencia
@app.get("/subscription-status/{user_id}", dependencies=[Depends(verify_api_key)])
async def get_subscription_status(user_id: str):
    """Permite al portal del cliente consultar el estado de su suscripción."""
    
    # --- SIMULACIÓN DE CONSULTA A BASE DE DATOS (REEMPLAZAR) ---
    # En una implementación real, aquí se usaría un ORM/conector para consultar la tabla 'subscriptions'.
    
    # Fecha de hoy simulada para la demostración
    current_time = datetime.now()
    
    # Ejemplo de datos de simulación
    if user_id == "juan-perez-123":
        return {
            "plan": "pro",
            "status": "active",
            "next_billing_at": (current_time + timedelta(days=20)).isoformat()
        }
    
    # Simulación de un usuario en periodo de prueba
    if user_id == "maria-lopez-456":
         return {
            "plan": "basic",
            "status": "trial",
            "next_billing_at": (current_time + timedelta(days=5)).isoformat() # Usamos next_billing_at para indicar fin de prueba
        }

    # Si el usuario no existe en la simulación
    raise HTTPException(status_code=404, detail="Suscripción no encontrada para este ID.")

# Requerimos el token y esperamos una lista de objetos Subscription en el cuerpo
@app.post("/calculate-billing-actions", response_model=List[BillingAction], dependencies=[Depends(verify_api_key)])
async def calculate_billing_actions(subscriptions: List[Subscription]):
    """
    Recibe todas las suscripciones y calcula las acciones a tomar hoy 
    (recordatorios, conversiones, renovaciones).
    """
    actions = []
    
    # Las comparaciones de facturación siempre deben hacerse a nivel de día (ignorando la hora)
    today = date.today() 
    three_days_out = today + timedelta(days=3)

    for sub in subscriptions:
        action = None
        
        # Convertir los timestamps de Pydantic a objetos date, si existen
        # Esto nos permite ignorar la hora y comparar solo la fecha
        trial_end_date = sub.trial_ends_at.date() if sub.trial_ends_at else None
        next_billing_date = sub.next_billing_at.date() if sub.next_billing_at else None
        
        # --- Lógica de Negocio ---
        
        if sub.status == 'trial':
            # Caso 1: Prueba termina en 3 días
            if trial_end_date == three_days_out:
                action = 'send_trial_reminder'
            # Caso 2: Prueba termina hoy (conversión)
            elif trial_end_date == today:
                action = 'process_trial_conversion'
        
        elif sub.status == 'active':
            # Caso 3: Renovación es hoy
            if next_billing_date == today:
                action = 'process_renewal_payment'
                
        elif sub.status == 'past_due':
            # Caso 4 (Opcional): Manejo de pago fallido (Dunning)
            action = 'send_dunning_email' 
            
        # Si se determinó una acción, la añadimos a la lista de salida
        if action:
            actions.append(
                BillingAction(
                    action=action, 
                    user_id=sub.user_id, 
                    email=sub.email
                )
            )

    return actions