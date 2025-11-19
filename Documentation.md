Diagrama de Arquitectura: Automatización de Facturación y Suscripciones SaaS

El siguiente diagrama visualiza el flujo de datos y las responsabilidades separadas de los cuatro componentes principales (Frontend, Backend, Orquestador y Base de Datos) en el ciclo de vida de la suscripción.

1. Flujo de Datos del Portal de Cliente (Sincrónico/Bajo Demanda)

Componente

Descripción

Interacción

Portal de Cliente (HTML/JS)

Interfaz web que simula la sesión del usuario.

Solicita estado

Microservicio (FastAPI)

Backend asegurado que verifica el token y accede a los datos.

Responde estado

Base de Datos (Neon/Supabase)

Fuente única de verdad que almacena la tabla subscriptions.

Microservicio Lee

Flujo:

USUARIO ingresa user_id en el Portal.

El Portal envía GET /subscription-status/{user_id}.

Headers: Incluye el Bearer Token.

El Microservicio valida el Token (403 Forbidden si falla).

El Microservicio consulta la Base de Datos (tabla subscriptions).

El Microservicio devuelve el JSON de estado al Portal.

El Portal muestra Plan, Estado y Próximo Cobro.

2. Flujo de Lógica de Facturación (Asíncrono/CRON)

Componente

Descripción

Interacción

n8n (Workflow Principal)

Orquestador y disparador de acciones. Inicia con un nodo CRON diario.

Controla el flujo

Base de Datos (Neon/Supabase)

Almacena los datos y es actualizado con las nuevas fechas de facturación.

n8n Lee y Escribe

Microservicio (FastAPI)

Contiene la lógica compleja de negocio (calculate-billing-actions).

n8n POSTea la data

n8n (Sub-Workflow)

Flujo reutilizable de notificación (ej. Envío de Email/SMS).

Llamado por el Workflow Principal

Flujo:

A. Ejecución Diaria

n8n (CRON Trigger) se ejecuta a la 1 AM.

n8n (BD) lee todas las suscripciones activas (SELECT * FROM subscriptions WHERE status != 'canceled').

n8n (Microservicio) envía la lista de suscripciones: POST /calculate-billing-actions.

Microservicio aplica la lógica de negocio (recordatorio a 3 días, conversión hoy, renovación hoy) y devuelve el array de Acciones ([{action: 'send_reminder', user_id: X}, ...]).

B. Enrutamiento y Ejecución

n8n (Loop y Switch) itera sobre cada acción recibida:

CASO 'send_trial_reminder': Llama a n8n (Sub-Workflow) con template_name='trial_reminder'.

CASO 'process_renewal_payment' / 'process_trial_conversion':
a. Llama a n8n (Sub-Workflow) (template_name='payment_success').
b. n8n (BD) ejecuta UPDATE subscriptions para avanzar next_billing_at al próximo mes (Gestión Transaccional).
i. Si el UPDATE falla: Llama a la ruta de manejo de errores, que ejecuta un INSERT en la tabla automation_logs.

3. Diagrama de Conexión (Representación Visual)

Leyenda del Flujo Asíncrono (CRON):

Inicio: CRON Trigger (n8n).

Decisión/Lógica: Microservicio y Nodo Switch (n8n).

Efecto: Notificaciones (Sub-Workflow) y Actualización de BD.

Manejo de Errores: Sub-flujo de BD Log.