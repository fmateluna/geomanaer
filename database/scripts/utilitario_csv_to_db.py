import pandas as pd
import sqlite3

# Cargar el archivo CSV
df = pd.read_csv("csv_data/MAESTROCALLES_CHILE_INE2024.csv")

# Crear una conexión SQLite
conn = sqlite3.connect('maestro_calles.db')  # Nombre de la base de datos SQLite

# Guardar el DataFrame en la base de datos SQLite
df.to_sql('maestro_calles', conn, if_exists='replace', index=False)

# Cerrar la conexión
conn.close()
