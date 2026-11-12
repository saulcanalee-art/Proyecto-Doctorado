import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.optimize import curve_fit
from scipy.integrate import solve_ivp

# 1. Configuración de rutas relativas (compatible con terminal y Jupyter Notebook)
try:
    BASE_DIR = Path(__file__).resolve().parent.parent
except NameError:
    BASE_DIR = Path.cwd().parent if Path.cwd().name == "notebook" else Path.cwd()

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

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
    "23": "Quintana Roo", "24": "San Luis Potosí", "25": "Sinaloa",
    "26": "Sonora", "27": "Tabasco", "28": "Tamaulipas", "29": "Tlaxcala",
    "30": "Veracruz", "31": "Yucatán", "32": "Zacatecas"
}

def extraer_json_estado(cve_entidad: str, usar_cache: bool = True) -> dict:
    """Consulta la API del INEGI y guarda el JSON crudo en data/raw/."""
    ruta_raw = RAW_DIR / f"inegi_entidad_{cve_entidad}.json"
    
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
    
    with open(ruta_raw, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    time.sleep(0.4)
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
    df_entidad["Tipo_Dato"] = "Histórico Censal"
    return df_entidad

def modelo_logistico(t, K, r, P0, t0):
    """Ecuación logística con P0 libre para absorber ruido histórico inicial."""
    return K / (1.0 + ((K - P0) / P0) * np.exp(-r * (t - t0)))

def proyectar_estado_edo(df_estado: pd.DataFrame, anios_futuros=[2025, 2030, 2035]) -> pd.DataFrame:
    """
    Ajusta modelo logístico y simula EDO con y sin migración.
    Incluye 2025 en anios_futuros para que las líneas en Power BI se conecten sin huecos.
    """
    df_val = df_estado[df_estado["Anio"] >= 1930].dropna(subset=["Poblacion_Total"]).sort_values("Anio")
    
    t_data = df_val["Anio"].values.astype(float)
    p_data = df_val["Poblacion_Total"].values.astype(float)
    
    t0 = t_data[0]
    p_min = p_data[0]
    p_max = p_data.max()
    
    def func_ajuste(t, K, r, P0):
        return modelo_logistico(t, K, r, P0, t0)
    
    sigma_pesos = np.where(t_data >= 2000, 0.25, 1.0)
    p0_guess = [p_max * 1.5, 0.03, p_min]
    bounds = ([p_max * 1.02, 0.005, p_min * 0.3], [p_max * 4.5, 0.10, p_min * 1.8])
    
    popt, _ = curve_fit(
        func_ajuste, t_data, p_data, p0=p0_guess, 
        sigma=sigma_pesos, bounds=bounds, maxfev=20000
    )
    K_opt, r_opt, _ = popt
    
    fila_2025 = df_val[df_val["Anio"] == 2025].iloc[0]
    pob_2025 = float(fila_2025["Poblacion_Total"])
    superficie_km2 = pob_2025 / float(fila_2025["Densidad_Pob"])
    prop_15_64 = float(fila_2025["Pob_15_a_64"]) / pob_2025
    
    saldos = df_estado.sort_values("Anio")["Saldo_Migratorio_Interno"].dropna()
    saldo_quinquenal = float(saldos.iloc[-1]) if not saldos.empty else 0.0
    mu_anual = saldo_quinquenal / 5.0
    
    # Asignar parámetros del modelo a las filas históricas del estado
    df_estado = df_estado.copy()
    df_estado["K_Capacidad"] = round(K_opt, 0)
    df_estado["r_Tasa"] = round(r_opt, 5)
    df_estado["mu_Migracion_Anual"] = round(mu_anual, 2)
    
    def edo_poblacion(t, P, delta_mu):
        P_actual = max(P[0], 1.0)
        dP_base = r_opt * P_actual * (1.0 - P_actual / K_opt)
        return [dP_base + delta_mu]

    sol_con_mig = solve_ivp(edo_poblacion, [2025, max(anios_futuros)], [pob_2025], args=(0.0,), t_eval=anios_futuros)
    sol_sin_mig = solve_ivp(edo_poblacion, [2025, max(anios_futuros)], [pob_2025], args=(-mu_anual,), t_eval=anios_futuros)
    
    nuevas_filas = []
    for idx, anio in enumerate(anios_futuros):
        for etiqueta, sol in [
            ("Proyección (Con Migración)", sol_con_mig),
            ("Proyección (Sin Migración)", sol_sin_mig)
        ]:
            pob_proy = float(sol.y[0][idx])
            nuevas_filas.append({
                "Anio": int(anio),
                "CVE_ENT": fila_2025["CVE_ENT"],
                "Entidad": fila_2025["Entidad"],
                "Poblacion_Total": round(pob_proy, 0),
                "Densidad_Pob": round(pob_proy / superficie_km2, 4),
                "Pob_15_a_64": round(pob_proy * prop_15_64, 0),
                "Saldo_Migratorio_Interno": np.nan,
                "Tipo_Dato": etiqueta,
                "K_Capacidad": round(K_opt, 0),
                "r_Tasa": round(r_opt, 5),
                "mu_Migracion_Anual": round(mu_anual if "Con" in etiqueta else 0.0, 2)
            })
            
    return pd.concat([df_estado, pd.DataFrame(nuevas_filas)], ignore_index=True)

def guardar_parquet_con_metadatos(df: pd.DataFrame, ruta_salida: Path):
    """Tipifica columnas e incrusta metadatos de procedencia en el archivo Parquet."""
    df["Anio"] = df["Anio"].astype("int32")
    df["Fecha"] = pd.to_datetime(df["Anio"].astype(str) + "-01-01")
    df["CVE_ENT"] = df["CVE_ENT"].astype("string")
    df["Entidad"] = df["Entidad"].astype("string")
    df["Tipo_Dato"] = df["Tipo_Dato"].astype("string")
    
    cols_float = list(NOMBRES_COLUMNAS.values()) + ["K_Capacidad", "r_Tasa", "mu_Migracion_Anual"]
    for col in cols_float:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

    tabla_arrow = pa.Table.from_pandas(df, preserve_index=False)
    
    metadatos_pia = {
        b"fuente": "INEGI - API Banco de Indicadores (BISE v2.0)".encode("utf-8"),
        b"indicadores": INDICADORES.encode("utf-8"),
        b"modelo_matematico": "EDO Logistica con termino de flujo migratorio neto (mu)".encode("utf-8"),
        b"fecha_procesamiento_utc": datetime.now(timezone.utc).isoformat().encode("utf-8"),
        b"licencia": "Libre Uso MX (INEGI)".encode("utf-8"),
        b"autor": "Saul Angel Sanchez Gonzalez - D06 Computo Cientifico FCFM UANL".encode("utf-8")
    }
    
    metadatos_combinados = {**(tabla_arrow.schema.metadata or {}), **metadatos_pia}
    tabla_arrow = tabla_arrow.replace_schema_metadata(metadatos_combinados)
    
    pq.write_table(tabla_arrow, ruta_salida, compression="snappy")

def main():
    print("Iniciando ETL + Proyección EDO Logística (2025-2035)...")
    frames = []
    
    for cve_ent, nombre in CATALOGO_ESTADOS.items():
        datos_raw = extraer_json_estado(cve_ent, usar_cache=True)
        df_est = procesar_entidad(datos_raw, cve_ent)
        if not df_est.empty:
            df_est_proy = proyectar_estado_edo(df_est, anios_futuros=[2025, 2030, 2035])
            frames.append(df_est_proy)
            print(f"[{cve_ent}/32] {nombre} procesado y proyectado a 2035.")
            
    df_final = pd.concat(frames, ignore_index=True).sort_values(["CVE_ENT", "Anio", "Tipo_Dato"])
    
    ruta_parquet = PROCESSED_DIR / "demografia_inegi_estatal.parquet"
    guardar_parquet_con_metadatos(df_final, ruta_parquet)
    print(f"\nParquet actualizado con éxito en: {ruta_parquet}")
    
    # Validaciones con pandas para documentar en el README (Criterio 3)
    df_2025 = df_final[(df_final["Anio"] == 2025) & (df_final["Tipo_Dato"] == "Histórico Censal")]
    df_2035_mig = df_final[(df_final["Anio"] == 2035) & (df_final["Tipo_Dato"] == "Proyección (Con Migración)")]
    
    print("\n--- VALIDACIÓN CON PANDAS (Para el README) ---")
    print(f"1. Población Nacional 2025 (Histórico): {df_2025['Poblacion_Total'].sum():,.0f}")
    print(f"2. Densidad Promedio Estatal 2025: {df_2025['Densidad_Pob'].mean():,.2f} hab/km²")
    print(f"3. Población Nacional Proyectada 2035 (Con Migración): {df_2035_mig['Poblacion_Total'].sum():,.0f}")

if __name__ == "__main__":
    main()