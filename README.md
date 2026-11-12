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

## Metodología Matemática y Fuente de Datos

### 1. Indicadores Oficiales (API INEGI BISE v2.0)
Los datos se extraen automáticamente bajo los **Términos de Libre Uso MX (INEGI)**:
* **`1002000001` (`Poblacion_Total`):** Población total censal e intercensal (Habitantes).
* **`3105001001` (`Densidad_Pob`):** Densidad de población estatal (Habitantes / $\text{km}^2$)[cite: 8, 9].
* **`6207140303` (`Pob_15_a_64`):** Población en edad laboral de 15 a 64 años (Habitantes)[cite: 8, 9].
* **`6200205262` (`Saldo_Migratorio_Interno`):** Saldo neto migratorio quinquenal (Habitantes)[cite: 8].

### 2. Modelo Logístico con Flujo Migratorio Externo ($\mu$)
Se ajusta la serie histórica post-revolucionaria (1930–2025) mediante mínimos cuadrados no lineales ponderados (`scipy.optimize.curve_fit`) para estimar la tasa intrínseca $r$ y la capacidad de carga $K$ de cada entidad[cite: 5, 6]. Posteriormente, se integra numéricamente (`scipy.integrate.solve_ivp`) la ecuación diferencial entre 2025 y 2035 comparando el escenario con migración activa frente al escenario sin migración ($\mu = 0$)[cite: 7, 14]:

$$\frac{dP}{dt} = rP\left(1 - \frac{P}{K}\right) + \mu$$

donde $\mu$ $[\text{hab/año}]$ representa el flujo migratorio anualizado de cada estado.

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

## Cómo Reproducir el Proyecto

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/saulcanalee-art/Proyecto-Doctorado.git
   cd Proyecto-Doctorado