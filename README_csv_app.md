# Flask CSV App (estructura base)

Este módulo incluye una estructura básica de una aplicación Flask que carga CSV desde `data/csv` al iniciar y expone rutas simples.

## Estructura
- `main.py`: punto de entrada de la app.
- `data/csv/*.csv`: archivos CSV de ejemplo/base.

## Rutas
- `GET /`: estado básico y lista de archivos cargados.
- `GET /data`: devuelve los datos en memoria.

## Ejecución
```bash
python main.py
```

## Notas
- Para añadir datos iniciales, coloca más CSV en `data/csv`.
- Si el puerto está ocupado, ejecuta `FLASK_RUN_PORT=5001 python main.py`.
