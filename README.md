# Control de Inventario

App simple para controlar stock de productos con botones + / - y SCRUD completo (Search, Create, Read, Update, Delete). Backend en Flask, base de datos SQLite, frontend en HTML/JS.

## Probar localmente

1. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Correr la app:
   ```
   python app.py
   ```
3. Abrir en el navegador: http://localhost:5000

## Subir a GitHub (paso previo a Render)

1. Crea un repositorio nuevo en GitHub (puede ser privado).
2. Sube esta carpeta completa (`app.py`, `templates/`, `static/`, `requirements.txt`).

## Desplegar en Render (gratis)

1. Entra a https://render.com y crea una cuenta (con GitHub es lo más rápido).
2. Clic en **New +** → **Web Service**.
3. Conecta tu repositorio de GitHub del proyecto.
4. Configura:
   - **Name**: el que quieras (ej. `control-inventario`)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
5. Clic en **Create Web Service**.
6. Espera unos minutos a que compile. Render te dará un link tipo:
   `https://control-inventario.onrender.com`
7. Comparte ese link con la persona que va a usar la app. No necesita instalar nada.

## Configurar Turso (base de datos persistente)

Este proyecto puede correr de dos formas:

- **Local, sin configurar nada**: usa un archivo SQLite normal (`inventario.db`), tal como antes.
- **En Render, con Turso**: si configuras las variables de entorno `TURSO_DATABASE_URL` y `TURSO_AUTH_TOKEN`, la app se conecta automáticamente a Turso en vez de usar el archivo local. Así los datos nunca se pierden, aunque Render reinicie el servicio.

### Pasos:

1. Crea tu cuenta en https://turso.tech y crea una base de datos (botón "Create Database").
2. Copia la **URL** (empieza con `libsql://...`) y genera un **Auth Token**.
3. En Render, ve a tu servicio → pestaña **Environment** → **Add Environment Variable**, y agrega:
   - `TURSO_DATABASE_URL` → pega la URL de tu base de datos
   - `TURSO_AUTH_TOKEN` → pega el token generado
4. Guarda los cambios. Render va a reiniciar el servicio automáticamente con las nuevas variables.
5. Listo — a partir de ahora, todos los datos se guardan en Turso, no en el disco de Render.

**Nota:** no necesitas crear las tablas manualmente en Turso — la app las crea automáticamente la primera vez que arranca (`init_db()` en `app.py`).

## Notas importantes

- La primera vez que se abre el link después de estar inactivo (15 min), tarda 30-60 segundos en "despertar". Es normal en el plan gratuito.
- Los datos se guardan en un archivo SQLite (`inventario.db`) dentro del propio servicio — no depende de una base de datos externa con fecha de caducidad.
- Nota sobre Render free tier: el sistema de archivos no es 100% persistente entre despliegues (si vuelves a subir cambios de código, el archivo `inventario.db` podría reiniciarse). Para uso normal (sin subir cambios de código constantemente), los datos persisten bien entre sesiones y reinicios por inactividad.