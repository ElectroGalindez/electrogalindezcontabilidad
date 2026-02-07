# 📊 Sistema de Contabilidad del Almacén

Este proyecto permite:
- Ver inventario
- Registrar ventas
- Registrar pagos de clientes
- Generar reportes con gráficas

## 🚀 Cómo ejecutarlo localmente
1. Clona el repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/almacen_contabilidad.git
   cd almacen_contabilidad
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la app (modo web local):
   ```bash
   streamlit run ElectroGalindez.py
   ```

## 💾 Persistencia local (SQLite)
La aplicación usa SQLite local (archivo `data/electrogalindez.sqlite`) mediante el módulo nativo `sqlite3`,
lo que garantiza funcionamiento 100% offline sin necesidad de servicios externos.

## 🖥️ Ejecutar como aplicación de escritorio (sin internet)
Este proyecto ya incluye un lanzador de escritorio usando **pywebview**.

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Inicia la app de escritorio:
   ```bash
   python desktop_app.py
   ```

Esto abre una ventana nativa que corre el Streamlit localmente, sin conexión.

## 🧭 Aplicación de escritorio (PySide6)
También puedes ejecutar una interfaz 100% nativa (sin navegador) basada en **PySide6**:

```bash
python desktop_app_pyside6.py
```

La base de datos SQLite se crea de forma automática en una ruta local del sistema:
- Windows: `%LOCALAPPDATA%\\tu_app\\db.sqlite`
- macOS: `~/Library/Application Support/tu_app/db.sqlite`
- Linux/otros: `./data/db.sqlite`

Con esa base local, los CRUDs de Usuarios, Ventas, Inventario y Notas funcionan 100% offline.

## 📦 Empaquetar como ejecutable
Puedes generar un ejecutable local con **PyInstaller**:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole desktop_app.py
```

## 📦 Empaquetado PySide6 (PyInstaller)
Sigue estos pasos para empaquetar la app nativa de escritorio sin consola:

### ✅ Windows (.exe)
1. Instala PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Genera el ejecutable:
   ```bash
   pyinstaller --noconsole --windowed --name tu_app desktop_app_pyside6.py
   ```
3. El .exe final estará en `dist/tu_app/tu_app.exe`.
4. Al ejecutarlo, SQLite se creará en:
   `%LOCALAPPDATA%\\tu_app\\db.sqlite`.

### ✅ macOS (.app)
1. Instala PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Genera la app:
   ```bash
   pyinstaller --windowed --name tu_app desktop_app_pyside6.py
   ```
3. La app final estará en `dist/tu_app.app`.
4. Al ejecutarla, SQLite se creará en:
   `~/Library/Application Support/tu_app/db.sqlite`.
