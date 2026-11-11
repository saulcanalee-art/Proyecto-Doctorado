import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# 1. Configuración de rutas relativas al repositorio
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Token desde variable de entorno (o fallback local para pruebas)
TOKEN = os.getenv("INEGI_TOKEN", "14c78d4c-82c9-24d8-19de-334e4cdba525")
INDICADORES = "1002000001,3105001001,6207140303,6200205262"

NOMBRES_COLUMNAS = {
    "1002000001": "Poblacion_Total",
    "3105001001": "Densidad_Pob",
    "6207140303": "Pob_15_a_64",
    "6200205262": "Saldo_Migratorio_Interno"
}

CATALOGO_ESTADOS = {
    "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
    "04": "Campeche", "05": "Coahuila", "06": "Colima", "07": "Chiapas",
    "08": "Chihuahua", "09": "Ciudad de México", "10": "Durango",
    "11": "Guanajuato", "12": "Guerrero", "13": "Hidalgo", "14": "Jalisco",
    "15": "México", "16": "Michoacán", "17": "Morelos", "18": "Nayarit",
    "19": "Nuevo León", "20": "Oaxaca", "21": "Puebla", "22": "Querétaro",
    "23": "Quintana Roo", "24": "San Luis Potosí", "25": "Sinloa",
    "26": "Sonora", "27": "Tabasco", "28": "Tamaulipas", "29": "Tlaxcala",
    "30": "Veracruz", "31": "Yucatán", "32": "Zacatecas"
}

def extraer_json_estado(cve_entidad: str, usar_cache: bool = False) -> dict:
    """Consulta la API del INEGI y guarda el JSON crudo en data/raw/."""
    ruta_raw = RAW_DIR / f"inegi_entidad_{cve_entidad}.json"
    
    # Si activas usar_cache=True o falla la red en la presentación, lee de data/raw/
    if usar_cache and ruta_raw.exists():
        with open(ruta_raw, "r", encoding="utf-8") as f:
            return json.load(f)

    url = (
        f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/"
        f"INDICATOR/{INDICADORES}/es/{cve_entidad}/false/BISE/2.0/{TOKEN}?type=json"
    )
    
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    datos = response.json()
    
    # Guardar JSON crudo en data/raw/ para inspección posterior
    with open(ruta_raw, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    return datos

def procesar_entidad(datos: dict, cve_entidad: str) -> pd.DataFrame:
    """Transforma el JSON crudo de una entidad en un DataFrame limpio."""
    lista_series = []
    for serie in datos.get("Series", []):
        id_ind = serie.get("INDICADOR")
        nombre_col = NOMBRES_COLUMNAS.get(id_ind, f"Ind_{id_ind}")
        obs = serie.get("OBSERVATIONS", [])
        
        if not obs:
            continue
            
        df_temp = pd.DataFrame(obs)[["TIME_PERIOD", "OBS_VALUE"]].rename(
            columns={"TIME_PERIOD": "Anio", "OBS_VALUE": nombre_col}
        )
        df_temp["Anio"] = pd.to_numeric(df_temp["Anio"], errors="coerce")
        df_temp[nombre_col] = pd.to_numeric(df_temp[nombre_col], errors="coerce")
        df_temp = df_temp.dropna(subset=["Anio"]).set_index("Anio")
        lista_series.append(df_temp)
        
    if not lista_series:
        return pd.DataFrame()
        
    df_entidad = pd.concat(lista_series, axis=1).reset_index()
    df_entidad["CVE_ENT"] = cve_entidad
    df_entidad["Entidad"] = CATALOGO_ESTADOS.get(cve_entidad, "Desconocido")
    return df_entidad

def guardar_parquet_con_metadatos(df: pd.DataFrame, ruta_salida: Path):
    """Tipifica columnas e incrusta metadatos de procedencia en el archivo Parquet."""
    # Asegurar que existan todas las columnas esperadas
    for col in NOMBRES_COLUMNAS.values():
        if col not in df.columns:
            df[col] = pd.NA

    # Tipos explícitos para compatibilidad con Power BI y PyArrow
    df["Anio"] = df["Anio"].astype("int32")
    # Columna Fecha indispensable para la Tabla de Fechas marcada en Power BI
    df["Fecha"] = pd.to_datetime(df["Anio"].astype(str) + "-01-01")
    df["CVE_ENT"] = df["CVE_ENT"].astype("string")
    df["Entidad"] = df["Entidad"].astype("string")
    
    for col in NOMBRES_COLUMNAS.values():
        df[col] = df[col].astype("float64")

    tabla_arrow = pa.Table.from_pandas(df, preserve_index=False)
    
    # Metadatos de procedencia obligatorios en el esquema Parquet
    metadatos_pia = {
        b"fuente": "INEGI - API Banco de Indicadores (BISE v2.0)".encode("utf-8"),
        b"indicadores": INDICADORES.encode("utf-8"),
        b"fecha_descarga_utc": datetime.now(timezone.utc).isoformat().encode("utf-8"),
        b"licencia": "Libre Uso MX (INEGI)".encode("utf-8"),
        b"autor": "Saul Angel Sanchez Gonzalez - D06 Computo Cientifico FCFM UANL".encode("utf-8")
    }
    
    metadatos_combinados = {**(tabla_arrow.schema.metadata or {}), **metadatos_pia}
    tabla_arrow = tabla_arrow.replace_schema_metadata(metadatos_combinados)
    
    pq.write_table(tabla_arrow, ruta_salida, compression="snappy")

def main():
    print("Iniciando flujo de datos INEGI -> data/raw/ -> data/processed/...")
    frames = []
    
    for cve_ent, nombre in CATALOGO_ESTADOS.items():
        try:
            print(f"[{cve_ent}/32] Extrayendo {nombre}...")
            datos_raw = extraer_json_estado(cve_ent, usar_cache=False)
            df_est = procesar_entidad(datos_raw, cve_ent)
            if not df_est.empty:
                frames.append(df_est)
            time.sleep(0.4)
        except Exception as e:
            print(f"Advertencia en entidad {cve_ent}: {e}")
            
    df_final = pd.concat(frames, ignore_index=True).sort_values(["CVE_ENT", "Anio"])
    
    ruta_parquet = PROCESSED_DIR / "demografia_inegi_estatal.parquet"
    guardar_parquet_con_metadatos(df_final, ruta_parquet)
    print(f"\nParquet generado con éxito en: {ruta_parquet}")
    
    # Validaciones con pandas para documentar en el README
    print("\n--- VALIDACIÓN CON PANDAS (Para contrastar con medidas DAX en el README) ---")
    df_2025 = df_final[df_final["Anio"] == 2025]
    print(f"1. Población Nacional 2025 (Suma de estados): {df_2025['Poblacion_Total'].sum():,.0f}")
    print(f"2. Densidad Promedio Estatal 2025: {df_2025['Densidad_Pob'].mean():,.2f} hab/km²")
    print(f"3. Proporción Pob 15-64 años en Nuevo León (2025): "
          f"{(df_2025.loc[df_2025['CVE_ENT']=='19', 'Pob_15_a_64'].values[0] / df_2025.loc[df_2025['CVE_ENT']=='19', 'Poblacion_Total'].values[0])*100:.2f}%")

if __name__ == "__main__":
    main()