import duckdb

# Conectar a la base de datos DuckDB (archivo persistente)
duckdb_path = 'maestro_calles.duckdb'
conn = duckdb.connect(duckdb_path)

# Ruta al archivo CSV
csv_path = './csv_data/MAESTROCALLES_CHILE_INE2024.csv'

# Crear una tabla y cargar los datos del CSV
conn.execute(f"""
    CREATE TABLE IF NOT EXISTS maestro_calles AS
    SELECT * FROM read_csv_auto('{csv_path}');
""")
conn.close()

print("¡CSV convertido exitosamente a DuckDB!")
