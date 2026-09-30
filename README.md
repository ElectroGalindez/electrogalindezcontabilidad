# 📊 Sistema de Contabilidad del Almacén

Aplicación de escritorio en Python + Streamlit sobre PostgreSQL en Neon.

Permite:
- Ver inventario
- Registrar ventas
- Registrar pagos de clientes
- Generar reportes con gráficas

## 🚀 Cómo ejecutarlo

### 1. Clona el repositorio
```bash
git clone https://github.com/ElectroGalindez/electrogalindezcontabilidad.git
cd electrogalindezcontabilidad
```

### 2. Crea el archivo de credenciales
Las credenciales **no** van en GitHub. Copia la plantilla y rellénala:
```bash
cp .env.example .env
```
Edita `.env` y pon tu URL de Neon:
```
NEON_DATABASE_URL=postgresql+psycopg2://USUARIO:CONTRASENA@ep-TU-PROYECTO-pooler.REGION.aws.neon.tech/neondb?sslmode=require
```
La encuentras en Neon → tu proyecto → **Connection Details**. En Neon 2026 es *Connect* y luego *Session pooler*.

### 3. Instala las dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Arranca la app
```bash
streamlit run ElectroGalindez.py
```
Se abre en http://localhost:8501

## ☁️ Despliegue en Streamlit Community Cloud
No necesita `.env`: en **Settings → Secrets** añade:
```toml
NEON_DATABASE_URL = "postgresql+psycopg2://USUARIO:CONTRASENA@HOST/neondb?sslmode=require"
```

## 🔌 Comprobar la conexión
```bash
python testconexion.py     # conexión directa con psycopg2
python backend/db.py      # conexión a través de SQLAlchemy
```

## 🔐 Seguridad
- `.env` está en `.gitignore` y **no debe subirse nunca**.
- Si una contraseña se sube por error, **cámbiala en Neon**: aunque borres el archivo o reescribas el historial, la clave queda expuesta en un repo público.
- `.env.example` sí se versiona: es la plantilla sin credenciales.
