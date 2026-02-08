# ElectroGalindez Desktop (Electron + Python)

## 📌 Descripción del proyecto
ElectroGalindez es una aplicación de contabilidad construida en Python (Streamlit) y empaquetada como ejecutable standalone. Este repositorio incluye un wrapper en Electron que lanza el ejecutable, espera el servidor local y muestra la interfaz en una ventana de escritorio para Windows y macOS.

## ✅ Requisitos
- **Python 3.11** (para generar el ejecutable con PyInstaller)
- **Node.js 18+** y **npm** (para Electron)
- **PyInstaller** (para empaquetar la app Python)
- **Git** (opcional)

## 🔐 Variables de entorno (desarrollo y producción)
Este proyecto usa variables de entorno para credenciales (por ejemplo, Twilio). Para desarrollo:
1. Copia `.env.example` a `.env`.
2. Completa los valores reales en `.env`.

Variables esperadas (ver `.env.example`):
- `TWILIO_ACCOUNT_SID`: SID de la cuenta de Twilio.
- `TWILIO_AUTH_TOKEN`: token de autenticación de Twilio.
- `TWILIO_WHATSAPP_FROM`: número de WhatsApp de salida en formato `whatsapp:+1234567890`.
- `TWILIO_WHATSAPP_TO`: número de WhatsApp de destino en formato `whatsapp:+1098765432`.

En producción, define estas variables directamente en el entorno del sistema o en el servicio de despliegue.
**No subas archivos `.env` ni credenciales al repositorio.**

## ▶️ Ejecutar localmente
1. Instala dependencias de Electron:
   ```bash
   npm install
   ```
2. Inicia Electron:
   ```bash
   npm start
   ```

> Asegúrate de que el ejecutable de Python exista en `./dist/` antes de iniciar Electron.

## 📦 Empaquetar la app Python (standalone)
Desde tu entorno virtual de **Python 3.11**, ejecuta:

### Windows
```bash
pyinstaller --onefile --noconsole --name ElectroGalindez \
  --add-data "backend;backend" \
  --add-data "ui;ui" \
  --add-data "pages;pages" \
  --add-data "assets;assets" \
  run_app.py
```

### macOS
```bash
pyinstaller --onefile --windowed --name ElectroGalindez \
  --add-data "backend:backend" \
  --add-data "ui:ui" \
  --add-data "pages:pages" \
  --add-data "assets:assets" \
  run_app.py
```

Esto generará el ejecutable en `./dist/`.

## 🧱 Empaquetar la app Electron (instaladores)
Para generar instaladores multiplataforma:
```bash
npm run build
```
Esto usará `electron-builder` para crear:
- **Windows**: instalador **NSIS**
- **macOS**: imagen **DMG**

## 📂 Usar la app portable
Puedes copiar la carpeta generada en `dist/` a otra computadora del mismo sistema operativo y ejecutar:
- **Windows**: `ElectroGalindez.exe`
- **macOS**: `ElectroGalindez`

No requiere instalación adicional si el ejecutable fue generado correctamente.

## 🗄️ Base de datos local (SQLite + CSV)
La app ahora trabaja con una base de datos **SQLite local** (`local.db`) y puede importar datos desde CSVs exportados de Neon.

### 📁 Estructura recomendada
Coloca los CSVs en:
```
data/csv/
  usuarios.csv
  productos.csv
  categorias.csv
  clientes.csv
  ventas.csv
  deudas.csv
  deudas_detalle.csv
  logs.csv
  auditoria.csv
  notas.csv
```

### ⚙️ Bootstrap automático
Cada vez que la app pide una conexión, se asegura de:
1. Crear el esquema si no existe.
2. Importar CSVs **solo si la base está vacía**.

### ✅ Ejemplos de uso en la app
```python
from data.db import ensure_bootstrap, fetch_all, insert_row

# 1) Inicializar y cargar CSVs si la base está vacía
ensure_bootstrap()

# 2) Leer datos para mostrarlos en Streamlit
clientes = fetch_all(\"SELECT * FROM clientes ORDER BY nombre\")

# 3) Insertar datos
nuevo_id = insert_row(\n    \"clientes\",\n    {\"nombre\": \"Cliente Demo\", \"telefono\": \"555-123\", \"deuda_total\": 0},\n)\n```

### 🔎 Consultas filtradas básicas
```python
from data.db import fetch_all

ventas_pendientes = fetch_all(\n    \"SELECT * FROM ventas WHERE saldo > ? ORDER BY fecha DESC\",\n    [0],\n)\n```

### 🧩 Script de importación manual
Para cargar los CSVs manualmente:
```bash
python scripts/load_data.py --csv-dir data/csv
```
Si necesitas reimportar datos en una base ya poblada:
```bash
python scripts/load_data.py --csv-dir data/csv --force
```

## 🛠️ Solución de problemas comunes
**1. El ejecutable no abre o se cierra inmediatamente**
- Asegúrate de generar el ejecutable con Python 3.11 y todas las dependencias instaladas.
- Verifica que `./dist/` contenga el archivo correcto.

**2. Electron se abre en blanco**
- El backend de Streamlit puede no haberse iniciado. Revisa la consola.
- Verifica que `http://localhost:8501` responda.

**3. Error al empaquetar con PyInstaller**
- Asegúrate de que todos los módulos internos estén incluidos con `--add-data`.
- Reinstala dependencias en un venv limpio.

**4. Problemas de permisos en macOS**
- Ejecuta: `chmod +x dist/ElectroGalindez`
- Si Gatekeeper bloquea la app, permite su ejecución en Ajustes de Seguridad.
