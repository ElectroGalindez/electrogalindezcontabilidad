import os
import sqlite3
import pandas as pd
from core.paths import get_data_dir

# Carpeta de CSV
csv_dir = "/Users/vicent/Library/Application Support/tu_app/csv"

# Ruta de la DB que la app va a usar
db_path = os.path.join(get_data_dir(), "db.sqlite")

# Conexión a SQLite
conn = sqlite3.connect(db_path)

# Cargar todos los CSV
for file in os.listdir(csv_dir):
    if file.endswith(".csv"):
        table_name = os.path.splitext(file)[0]
        df = pd.read_csv(os.path.join(csv_dir, file))
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✅ Tabla '{table_name}' cargada desde '{file}'")

conn.close()
print("🎉 Bootstrap de DB completado, todas las tablas creadas correctamente.")
