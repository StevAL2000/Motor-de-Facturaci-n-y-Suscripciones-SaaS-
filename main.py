import os
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv



# Cargar variables de entorno (como API_SECRET_KEY) desde un archivo .env
load_dotenv()
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "tu-clave-secreta-de-prueba") 
app = FastAPI()

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
    
    # La clave real debe venir de una variable de entorno para producción
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
    # En una implementación real, aquí se usaría un ORM como SQLAlchemy o un conector 
    # puro para consultar la tabla 'subscriptions' en Supabase/Neon.
    
    # Ejemplo de datos de simulación
    if user_id == "juan-perez-123":
        return {
            "plan": "pro",
            "status": "active",
            "next_billing_at": (datetime.now() + timedelta(days=20)).isoformat()
        }
    
    # Simulación de un usuario en periodo de prueba
    if user_id == "maria-lopez-456":
         return {
            "plan": "basic",
            "status": "trial",
            "next_billing_at": (datetime.now() + timedelta(days=5)).isoformat()
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
            # Podrías añadir lógica aquí para reintentos basados en last_payment_attempt
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