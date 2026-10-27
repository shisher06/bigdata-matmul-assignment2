# Carpetas de resultados

| Carpeta | Qué es | Uso |
|---|---|---|
| `01_A_densa` | **Parte A, campaña principal.** `ijk` (baseline = kernel de C de la Práctica 1), `ikj` y `blocked` (bloque 64), n = 10 a 4000 (tamaños de la P1 + 512, 1024, 1536, 2048, 2500, 3000, 4000), 5 repeticiones (3 si la 1.ª pasa de 120 s), un proceso por repetición, métodos intercalados. Mismas entradas que la Práctica 1. | **Resultados del informe (Parte A).** |
| `02_A_extra_bloques` | Experimento aparte: `blocked` con bloques de 16, 32, 64, 128 y 256 en n = 500, 512, 1000, 1024 y 2000, 5 repeticiones. | Justifica el bloque 64 de la campaña principal. **No se mezcla** con ella. |
| `03_B_dispersa` | **Parte B.** `csr`, `blocked` e `ijk` sobre matrices dispersas de `data_sparse/` con n = 1000 y 2000 y densidades 0.1, 0.5, 1, 2, 5, 10, 20, 30 y 50 %, 5 repeticiones. | **Resultados del informe (Parte B).** |
| `04_B_dispersa_n4000` | Parte B con un tamaño mayor: `csr` y `blocked` con n = 4000 y densidades 0.1 y 1 %. | Tamaño mayor de la Parte B. |
| `05_B_extra_densidades_altas` | Experimento aparte, **añadido después** de `03` porque csr seguía ganando al 50 %: `csr` y `blocked` con n = 1000 y 2000 y densidades 60, 70, 85 y 100 %. Su `summary.md` y `plots/` se generan con `03` + `05` juntos (todas las densidades). | Localiza el cruce csr = blocked (~53 %). Figuras de la Parte B del informe. |
| `06_A_extra_alineacion` | Experimento aparte, **añadido después** de `01`: `ikj`, `ikj-align32` (mismo código compilado con `-falign-loops=32`), `blocked-notile` (un único bloque = operaciones de ikj sin tiling) y `blocked`, n = 50 a 2000. | Separa el efecto de la colocación del código del efecto del tiling (informe, apartado 4.4). |

Cada carpeta tiene su `raw.csv` (medidas en bruto, una fila por proceso), `campaign.log` (salida de la
campaña), `environment.md/.json` (máquina, versiones, flags) y, una vez analizada, `summary.csv`,
`summary.md` y `plots/`. Para volver a generar tablas y gráficas:

```
py -3.11 scripts/analyze.py --csv results/01_A_densa/raw.csv --out-dir results/01_A_densa --p1-summary ../practica1/results/04_comparativa_3_lenguajes/summary.csv
py -3.11 scripts/analyze.py --csv results/02_A_extra_bloques/raw.csv --out-dir results/02_A_extra_bloques
py -3.11 scripts/analyze.py --csv results/03_B_dispersa/raw.csv --out-dir results/03_B_dispersa
py -3.11 scripts/analyze.py --csv results/04_B_dispersa_n4000/raw.csv --out-dir results/04_B_dispersa_n4000
py -3.11 scripts/analyze.py --csv results/03_B_dispersa/raw.csv results/05_B_extra_densidades_altas/raw.csv --out-dir results/05_B_extra_densidades_altas
py -3.11 scripts/analyze.py --csv results/06_A_extra_alineacion/raw.csv --out-dir results/06_A_extra_alineacion --kind dense
```

Nota sobre `02_A_extra_bloques`: las dos primeras repeticiones de n = 500 (bloques 32 y 64) son más
lentas que las demás (86-103 ms frente a unos 41 ms) probablemente porque coincidieron con otra actividad
en el portátil al principio de la sesión (se estaban editando ficheros y ejecutando un análisis de
prueba). No se ha eliminado ninguna medida;
la mediana no cambia el orden de los bloques.
