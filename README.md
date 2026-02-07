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

## 📦 Empaquetar como ejecutable
Puedes generar un ejecutable local con **PyInstaller**:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole desktop_app.py
```
