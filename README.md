# Redistribución Demográfica y Migratoria en México hacia 2035 (INEGI)

[![.github/workflows/latex.yml](https://github.com/saulcanalee-art/Proyecto-Doctorado/actions/workflows/latex.yml/badge.svg?branch=main)](https://github.com/saulcanalee-art/Proyecto-Doctorado/actions/workflows/latex.yml)

**Curso:** Cómputo Científico- (FCFM - UANL)  
**Autor:** Saúl Ángel Sánchez González (`Saul Sanchez`)

---

## Propósito y Pregunta Científica
Este proyecto analiza la dinámica demográfica histórica (1910–2025) y los saldos migratorios internos de las 32 entidades federativas de México mediante la API del Banco de Indicadores del INEGI (BISE v2.0), con el objetivo de proyectar la redistribución poblacional hacia **2035** y cuantificar la presión adicional sobre la infraestructura en los estados receptores mediante un modelo matemático.

* **Pregunta Científica:** *¿Cómo modificará el flujo migratorio interno ($\mu$) la trayectoria del modelo logístico en las entidades de México hacia 2035?*
* **Gran Idea:** *Hacia 2035, México sumará 10.6 millones de habitantes hasta alcanzar 141.5 millones, concentrando la presión de infraestructura en polos industriales receptores como Nuevo León (+115 mil habitantes extra solo por migración interna) mientras las entidades expulsoras se desaceleran cerca de su capacidad de carga ($K$).*

---

### 1. Datos

#### Fuente y cobertura

Se utilizan datos de las 32 entidades federativas de México,
obtenidos mediante la API del Banco de Indicadores del INEGI
(BISE v2.0).

Los indicadores tienen distinta cobertura temporal. La serie de
población utilizada abarca de 1910 a 2025; para ajustar el modelo
logístico se seleccionan los registros desde 1930.

El último dato disponible en los archivos descargados del indicador
de saldo migratorio corresponde a 2010. Por lo tanto, el flujo
empleado en las proyecciones no representa una medición de la
migración en 2025.

| Indicador | Variable | Unidad |
|---|---|---|
| 1002000001 | Poblacion_Total | Habitantes |
| 3105001001 | Densidad_Pob | Habitantes/km² |
| 6207140303 | Pob_15_a_64 | Habitantes de 15 a 64 años |
| 6200205262 | Saldo_Migratorio_Interno | Habitantes, saldo neto |

#### Archivos y transformación

- `data/raw/`: contiene los 32 archivos JSON utilizados como
  respuestas originales y caché de consulta.
- `data/processed/demografia_inegi_estatal.parquet`: contiene
  los datos organizados por entidad, año y tipo de dato.

Las claves de entidad se conservan como texto para mantener sus
ceros iniciales. Los años, fechas y variables numéricas se guardan
con tipos apropiados.

Los valores faltantes se conservan como nulos, no como ceros:
las series no contienen observaciones para todos los mismos años.

#### Datos de origen y proyecciones

La columna `Tipo_Dato` distingue tres categorías:

- `Histórico Censal`: etiqueta utilizada por el código para las
  observaciones procedentes de la API.
- `Proyección (Con Migración)`: resultados del escenario así
  denominado en el modelo.
- `Proyección (Sin Migración)`: resultados del escenario alternativo.

Las proyecciones de 2030 y 2035 son cálculos del proyecto,
no cifras oficiales del INEGI. Ambos escenarios incluyen 2025
como punto inicial para conectarse con la serie de origen.

#### Procedencia y uso

El Parquet incorpora metadatos de fuente, identificadores de
indicadores, modelo matemático, autor, licencia y fecha de
procesamiento en UTC.

La fecha de procesamiento indica cuándo se generó el Parquet;
no equivale necesariamente a la fecha de descarga de los JSON.

Los datos se atribuyen al INEGI y se utilizan conforme a sus
términos de libre uso. La licencia del código se encuentra
en el archivo `LICENSE`.

### 2. Modelo Logístico con Flujo Migratorio Interno ($\mu$)
Se ajusta la serie de tiempo histórica (1930–2025) mediante mínimos cuadrados (`scipy.optimize.curve_fit`) para estimar la tasa intrínseca $r$ y la capacidad de carga $K$ de cada entidad. Posteriormente, se integra numéricamente (`scipy.integrate.solve_ivp`) la ecuación diferencial entre 2025 y 2035 comparando el escenario con migración activa frente al escenario sin migración ($\mu = 0$):

$$\frac{dP}{dt} = rP\left(1 - \frac{P}{K}\right) + \mu$$

donde $\mu$ $[\text{hab/año}]$ representa el flujo migratorio anualizado de cada estado:

* $\mu > 0$ representa un estado receptor de migración.
* $\mu < 0$ representa un estado emisor migratorio.
* $\mu = 0$ representa un estado sin flujo migratorio.

$\mu$ se calcula en base a los datos migratorios de inegi de los ultimos 5 años: $ \[
\mu=\frac{\text{inmigrantes del periodo}-\text{emigrantes del periodo}}{5}
\quad [\text{habitantes/año}]$. Cabe aclarar que estos datos el ultimo año es el 2010.
\]
---

## Validación de Medidas (Pandas vs. Power BI)
Para garantizar la integridad del **Modelo en Estrella** (`Fact_Demografia`, `Dim_Entidad`, `Dim_Calendario`)[cite: 10, 12, 13], las medidas explícitas en **DAX** fueron contrastadas contra el cálculo directo en `pandas`:

| Medida Explícita | Resultado en Pandas (Python) | Resultado en DAX (Power BI) | Estado |
| :--- | :--- | :--- | :--- |
| **Poblacion 2025** | 130,911,314 hab | 130,911,314.00 hab[cite: 13] | ✅ Validado |
| **Densidad Promedio 2025** | 314.84 hab/km² | 314.84 hab/km²[cite: 13] | ✅ Validado |
| **Poblacion Proyectada 2035** | 141,531,185 hab | 141,531,185.00 hab[cite: 13] | ✅ Validado |

---

## Estructura de Carpetas
La organización del repositorio sigue el estándar reproducible del proyecto:
* `src/`: Pipeline automatizado `etl_inegi.py` (Extracción API, ajuste EDO y exportación a Parquet con metadatos).
* `data/raw/`: Caché local de las respuestas JSON crudas por entidad federativa.
* `data/processed/`: Archivo columnar `demografia_inegi_estatal.parquet` tipificado y con metadatos incrustados[cite: 8, 9].
* `reportes/`: Proyecto de Power BI en formato controlable por Git (`.pbip`), modelo semántico en estrella y medidas DAX.
* `notebook/`: Cuadernos de Jupyter con la exploración matemática y pruebas de las curvas logísticas.
* `docs/`: Reporte ejecutivo exportado en PDF, diapositivas de defensa y documentación en LaTeX.
* `ideas/`: Notas preliminares y planteamientos iniciales del proyecto.

---

## Cómo reproducir el proyecto

### Requisitos previos

- Python 3.12.
- Git para clonar el repositorio.
- Power BI Desktop para abrir el proyecto `.pbip`.

Los siguientes comandos se ejecutan en PowerShell, en Windows.

### 1. Obtener el proyecto

```powershell
git clone https://github.com/saulcanalee-art/Proyecto-Doctorado.git
cd Proyecto-Doctorado
```

Si ya tienes el repositorio descargado, abre PowerShell en su carpeta.

### 2. Preparar el entorno

Crear un entorno virtual e instalar las dependencias con las versiones
especificadas:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Datos guardados y acceso a la API

El repositorio incluye los JSON de las 32 entidades en `data/raw/`.
El script reutiliza esos archivos cuando están disponibles.

Si falta el JSON de una entidad, intenta obtenerlo desde la API del INEGI.
Para utilizar un token propio, configurar la variable de entorno antes
de ejecutar el flujo:

```powershell
$env:INEGI_TOKEN = "TU_TOKEN_INEGI"
```

Configurar el token no fuerza una descarga nueva: los JSON existentes
siguen utilizándose como caché.

### 4. Ejecutar el flujo completo

Desde la raíz del repositorio, ejecutar:

```powershell
.\.venv\Scripts\python.exe src/etl_inegi.py
```

El flujo procesa los datos de las 32 entidades, ajusta el modelo
logístico, calcula los escenarios y genera o reemplaza:

`data/processed/demografia_inegi_estatal.parquet`

El Parquet incluye tipos de datos y metadatos de procedencia.
La fecha de procesamiento se actualiza en cada ejecución.

### 5. Comprobar los resultados

Con los JSON incluidos en esta versión, la consola debe mostrar:

| Comprobación | Resultado esperado |
|---|---:|
| Población nacional 2025 | 130,911,314 habitantes |
| Promedio de densidades estatales 2025 | 314.84 hab/km² |
| Población proyectada 2035, escenario con migración | 141,531,185 habitantes |

Estos resultados corresponden a los datos guardados y al modelo
implementado en esta versión.
