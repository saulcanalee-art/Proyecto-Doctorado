# Cómputo Científico - Doctorado Materia que se lleva a cabo en la FCFM
[![.github/workflows/latex.yml](https://github.com/saulcanalee-art/Proyecto-Doctorado/actions/workflows/latex.yml/badge.svg?branch=main)](https://github.com/saulcanalee-art/Proyecto-Doctorado/actions/workflows/latex.yml)
## Descripción del proyecto
# Redistribución Demográfica y Migratoria en México (INEGI)

## Propósito
Este proyecto analiza la dinámica demográfica y los saldos migratorios internos de los 32 estados de México para proyectar cómo se distribuirá la población hacia el 2035 y anticipar las necesidades de infraestructura en los estados receptores.

## Cómo reproducir
El flujo de extracción y procesamiento de datos está automatizado en un solo script de Python. Para reproducirlo desde la raíz del repositorio, ejecuta:

```bash
pip install -r requirements.txt
python src/etl_inegi.py
> **Saul Sanchez** (2026). *Cómputo Científico - Doctorado*. Facultad de Ciencias Físico Matemáticas, Universidad Autónoma de Nuevo León (UANL).

## Estructura de carpetas
La organización del repositorio es la siguiente:
* `src/`: Scripts de código fuente y algoritmos.
* `data/`: Datos de entrada y resultados generados.
* `docs/`: Documentos de investigación, reportes y archivos de LaTeX.
* `notebook/`: Cuadernos de experimentación.
* `ideas/:` Carpeta donde se suben ideas nuevas para el proyecto.



## Validación de Medidas (Pandas vs Power BI)
Para garantizar la integridad del modelo en estrella en Power BI, las 3 medidas DAX explícitas fueron contrastadas contra el cálculo directo en `pandas`:

| Medida Explícita | Resultado en Pandas (Python) | Resultado en DAX (Power BI) | Estado |
| :--- | :--- | :--- | :--- |
| **Poblacion 2025** | 130,911,314 hab | 130,911,314.00 hab | ✅ Validado |
| **Densidad Promedio 2025** | 314.84 hab/km² | 314.84 hab/km² | ✅ Validado |
| **Poblacion Proyectada 2035** | 141,531,185 hab | 141,531,185.00 hab | ✅ Validado |


## Cómo reproducirlo
1. Clona este repositorio localmente usando: `git clone https://github.com/saulcanalee-art/Proyecto-Doctorado.git`
2. Navega al directorio del proyecto: `cd Proyecto-Doctorado`
3. Ejecuta los scripts o revisa la documentación en sus respectivas carpetas (`src/`, `docs/`).

## Cómo citar

Si utilizas este software o los algoritmos de este repositorio en tu investigación, por favor utiliza el botón **"Cite this repository"** (ubicado en el menú lateral derecho de la página principal) para obtener el formato de citación adecuado generado automáticamente desde nuestro archivo `CITATION.cff`.

