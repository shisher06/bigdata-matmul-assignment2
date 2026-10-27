# Resumen de resultados - Parte A (densas)

Estadísticos sobre las ejecuciones con `status = OK`: mediana y rango intercuartílico (IQR = Q3 - Q1). Tiempos por multiplicación. Memoria en MB decimales (10⁶ B). Cada ejecución es un proceso nuevo. Mismas entradas que la Práctica 1.

## Comparación entre métodos (mediana del tiempo por multiplicación)

| n | ijk (baseline, A1) | ikj (loop order) | blocked ikj (64) | speedup ikj vs ijk | speedup blocked vs ijk |
|---:|---:|---:|---:|---:|---:|
| 10 | 0.418 µs | 0.788 µs | 0.439 µs | 0.53x | 0.951x |
| 25 | 6.69 µs | 8.62 µs | 5.21 µs | 0.776x | 1.28x |
| 50 | 61.5 µs | 66.5 µs | 39.5 µs | 0.924x | 1.56x |
| 100 | 627 µs | 605 µs | 320 µs | 1.04x | 1.96x |
| 200 | 5.28 ms | 4.64 ms | 2.53 ms | 1.14x | 2.09x |
| 300 | 19.4 ms | 14.9 ms | 8.7 ms | 1.3x | 2.23x |
| 400 | 45.8 ms | 34.1 ms | 20.8 ms | 1.34x | 2.2x |
| 500 | 89.9 ms | 67 ms | 40.7 ms | 1.34x | 2.21x |
| 512 | 739 ms | 71.9 ms | 43 ms | 10.3x | 17.2x |
| 600 | 160 ms | 116 ms | 70 ms | 1.39x | 2.29x |
| 800 | 511 ms | 312 ms | 164 ms | 1.64x | 3.13x |
| 1000 | 960 ms | 627 ms | 329 ms | 1.53x | 2.92x |
| 1024 | 6.747 s | 667 ms | 366 ms | 10.1x | 18.4x |
| 1200 | 1.692 s | 1.068 s | 554 ms | 1.58x | 3.06x |
| 1500 | 5.093 s | 2.071 s | 1.096 s | 2.46x | 4.65x |
| 1536 | 23.19 s | 2.238 s | 1.154 s | 10.4x | 20.1x |
| 2000 | 15.05 s | 5.024 s | 2.626 s | 2.99x | 5.73x |
| 2048 | 138.2 s | 5.361 s | 3.704 s | 25.8x | 37.3x |
| 2500 | 61.49 s | 9.968 s | 5.382 s | 6.17x | 11.4x |
| 3000 | 148.1 s | 19.69 s | 9.923 s | 7.52x | 14.9x |
| 4000 | - | 40.03 s | 22.51 s | - | - |

«-» = sin medida válida para ese tamaño (ver *Límites*).

## Coste por iteración interna (ns = tiempo / n³)

| n | ijk (baseline, A1) | ikj (loop order) | blocked ikj (64) |
|---:|---:|---:|---:|
| 10 | 0.418 | 0.788 | 0.439 |
| 25 | 0.428 | 0.552 | 0.333 |
| 50 | 0.492 | 0.532 | 0.316 |
| 100 | 0.627 | 0.605 | 0.32 |
| 200 | 0.66 | 0.58 | 0.317 |
| 300 | 0.718 | 0.551 | 0.322 |
| 400 | 0.716 | 0.533 | 0.325 |
| 500 | 0.719 | 0.536 | 0.326 |
| 512 | 5.51 | 0.536 | 0.32 |
| 600 | 0.742 | 0.535 | 0.324 |
| 800 | 0.999 | 0.609 | 0.319 |
| 1000 | 0.96 | 0.627 | 0.329 |
| 1024 | 6.28 | 0.621 | 0.341 |
| 1200 | 0.979 | 0.618 | 0.32 |
| 1500 | 1.51 | 0.614 | 0.325 |
| 1536 | 6.4 | 0.617 | 0.318 |
| 2000 | 1.88 | 0.628 | 0.328 |
| 2048 | 16.1 | 0.624 | 0.431 |
| 2500 | 3.94 | 0.638 | 0.344 |
| 3000 | 5.48 | 0.729 | 0.368 |
| 4000 | - | 0.625 | 0.352 |

## Baseline: reproducción de la medida de la Práctica 1

El baseline `ijk` es el mismo código, flags y entradas que «C (-O2)» de la Práctica 1 (campaña `04_comparativa_3_lenguajes`), medido de nuevo hoy.

| n | Práctica 1 (mediana) | Práctica 2 (mediana) | P2 / P1 |
|---:|---:|---:|---:|
| 10 | 0.441 µs | 0.418 µs | 0.947 |
| 25 | 6.34 µs | 6.69 µs | 1.06 |
| 50 | 59.5 µs | 61.5 µs | 1.03 |
| 100 | 599 µs | 627 µs | 1.05 |
| 200 | 5.28 ms | 5.28 ms | 1 |
| 300 | 18.6 ms | 19.4 ms | 1.05 |
| 400 | 45.1 ms | 45.8 ms | 1.02 |
| 500 | 89.3 ms | 89.9 ms | 1.01 |
| 600 | 156 ms | 160 ms | 1.03 |
| 800 | 472 ms | 511 ms | 1.08 |
| 1000 | 934 ms | 960 ms | 1.03 |
| 1200 | 1.613 s | 1.692 s | 1.05 |
| 1500 | 4.597 s | 5.093 s | 1.11 |
| 2000 | 10.81 s | 15.05 s | 1.39 |

## Memoria: pico del working set del proceso completo (MB)

Medido por el runner con `GetProcessMemoryInfo` sobre el proceso hijo al terminar (la misma métrica que en la Práctica 1).

| n | ijk (baseline, A1) | ikj (loop order) | blocked ikj (64) | modelo 3·8n² |
|---:|---:|---:|---:|---:|
| 10 | 4.506 | 4.506 | 4.506 | 0.0024 |
| 25 | 4.575 | 4.575 | 4.575 | 0.015 |
| 50 | 4.538 | 4.534 | 4.534 | 0.06 |
| 100 | 4.813 | 4.813 | 4.813 | 0.24 |
| 200 | 5.816 | 5.816 | 5.816 | 0.96 |
| 300 | 7.262 | 7.262 | 7.262 | 2.16 |
| 400 | 9.556 | 9.56 | 9.56 | 3.84 |
| 500 | 12.44 | 12.44 | 12.44 | 6 |
| 512 | 10.77 | 12.83 | 12.83 | 6.291 |
| 600 | 13.12 | 13.12 | 15.96 | 8.64 |
| 800 | 19.84 | 19.84 | 19.84 | 15.36 |
| 1000 | 28.48 | 28.48 | 28.48 | 24 |
| 1024 | 29.65 | 29.65 | 29.65 | 25.17 |
| 1200 | 39.04 | 39.04 | 39.04 | 34.56 |
| 1500 | 58.48 | 58.48 | 58.48 | 54 |
| 1536 | 61.1 | 61.1 | 61.1 | 56.62 |
| 2000 | 100.5 | 100.5 | 100.5 | 96 |
| 2048 | 105.1 | 105.1 | 105.1 | 100.7 |
| 2500 | 154.5 | 154.5 | 154.5 | 150 |
| 3000 | 220.5 | 220.5 | 220.5 | 216 |
| 4000 | - | 388.5 | 388.5 | 384 |

## Corrección

- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos en 21 de 21 casos comparables: 10, 25, 50, 100, 200, 300, 400, 500, 512, 600, 800, 1000, 1024, 1200, 1500, 1536, 2000, 2048, 2500, 3000, 4000.
- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): 8.27e-15 (tolerancia rtol = 1e-9).
- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.

## ijk (baseline, A1) - `ijk`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5 | 0.418 µs | 0.416 µs | 0.428 µs | 2.91 | 0.4178 | 200000 | 2x10 | 4.506 | 4.342 | 0.0024 |
| 25 | 5 | 6.69 µs | 6.56 µs | 6.7 µs | 2.09 | 0.4282 | 6803 | 2x25 | 4.575 | 4.415 | 0.015 |
| 50 | 5 | 61.5 µs | 61.2 µs | 61.5 µs | 0.523 | 0.4917 | 1532 | 2x50 | 4.538 | 4.415 | 0.06 |
| 100 | 5 | 627 µs | 617 µs | 634 µs | 2.63 | 0.6274 | 165 | 2x64 | 4.813 | 4.653 | 0.24 |
| 200 | 5 | 5.28 ms | 5.28 ms | 5.35 ms | 1.22 | 0.6605 | 19 | 2x64 | 5.816 | 5.657 | 0.96 |
| 300 | 5 | 19.4 ms | 18.9 ms | 19.4 ms | 2.88 | 0.7182 | 6 | 2x64 | 7.262 | 7.221 | 2.16 |
| 400 | 5 | 45.8 ms | 45.8 ms | 46 ms | 0.448 | 0.7158 | 3 | 2x64 | 9.556 | 8.274 | 3.84 |
| 500 | 5 | 89.9 ms | 89.7 ms | 90.3 ms | 0.657 | 0.7194 | 2 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 739 ms | 737 ms | 740 ms | 0.434 | 5.505 | 1 | 1x64 | 10.77 | 10.73 | 6.291 |
| 600 | 5 | 160 ms | 160 ms | 170 ms | 6.58 | 0.7423 | 1 | 1x64 | 13.12 | 13.08 | 8.64 |
| 800 | 5 | 511 ms | 509 ms | 518 ms | 1.87 | 0.999 | 1 | 1x64 | 19.84 | 19.8 | 15.36 |
| 1000 | 5 | 960 ms | 958 ms | 1.023 s | 6.79 | 0.9601 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 6.747 s | 6.724 s | 6.788 s | 0.961 | 6.283 | 1 | 1x64 | 29.65 | 29.6 | 25.17 |
| 1200 | 5 | 1.692 s | 1.689 s | 1.709 s | 1.19 | 0.9793 | 1 | 1x64 | 39.04 | 39 | 34.56 |
| 1500 | 5 | 5.093 s | 5.071 s | 5.316 s | 4.82 | 1.509 | 1 | 1x64 | 58.48 | 58.43 | 54 |
| 1536 | 5 | 23.19 s | 22.98 s | 24.15 s | 5.03 | 6.399 | 1 | 1x64 | 61.1 | 61.06 | 56.62 |
| 2000 | 5 | 15.05 s | 15.04 s | 15.87 s | 5.5 | 1.881 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2048 | 3 (!) | 138.2 s | 137.7 s | 138.4 s | 0.459 | 16.09 | 1 | 1x64 | 105.1 | 105.1 | 100.7 |
| 2500 | 5 | 61.49 s | 61.4 s | 61.61 s | 0.342 | 3.935 | 1 | 1x64 | 154.5 | 154.4 | 150 |
| 3000 | 3 (!) | 148.1 s | 141.8 s | 149 s | 4.9 | 5.483 | 1 | 1x64 | 220.5 | 220.4 | 216 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **3000**
- Mayor tamaño intentado: **4000**
- n = 4000, repetición 1: **timeout** (cancelado a los 300 s); límite de tiempo 300 s, presupuesto de memoria 4096 MB. Sin tiempo asignado.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 17 tamaños): **3.741** +- 0.217 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.579**.

## ikj (loop order) - `ikj`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5 | 0.788 µs | 0.778 µs | 0.796 µs | 2.32 | 0.7876 | 111112 | 2x10 | 4.506 | 4.342 | 0.0024 |
| 25 | 5 | 8.62 µs | 8.56 µs | 8.65 µs | 1.03 | 0.552 | 11765 | 2x25 | 4.575 | 4.415 | 0.015 |
| 50 | 5 | 66.5 µs | 64.3 µs | 68.4 µs | 6.08 | 0.532 | 1409 | 2x50 | 4.534 | 4.415 | 0.06 |
| 100 | 5 | 605 µs | 604 µs | 621 µs | 2.78 | 0.6054 | 166 | 2x64 | 4.813 | 4.653 | 0.24 |
| 200 | 5 | 4.64 ms | 4.57 ms | 4.66 ms | 2.06 | 0.5801 | 22 | 2x64 | 5.816 | 5.657 | 0.96 |
| 300 | 5 | 14.9 ms | 14.7 ms | 14.9 ms | 1.68 | 0.5511 | 7 | 2x64 | 7.262 | 7.221 | 2.16 |
| 400 | 5 | 34.1 ms | 34.1 ms | 34.9 ms | 2.45 | 0.5334 | 3 | 2x64 | 9.56 | 8.278 | 3.84 |
| 500 | 5 | 67 ms | 67 ms | 67.2 ms | 0.242 | 0.5364 | 2 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 71.9 ms | 71.1 ms | 73.6 ms | 3.43 | 0.5357 | 2 | 2x64 | 12.83 | 10.73 | 6.291 |
| 600 | 5 | 116 ms | 115 ms | 118 ms | 2.58 | 0.5349 | 1 | 1x64 | 13.12 | 13.08 | 8.64 |
| 800 | 5 | 312 ms | 311 ms | 313 ms | 0.5 | 0.6094 | 1 | 1x64 | 19.84 | 19.8 | 15.36 |
| 1000 | 5 | 627 ms | 622 ms | 661 ms | 6.21 | 0.6266 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 667 ms | 662 ms | 671 ms | 1.38 | 0.6214 | 1 | 1x64 | 29.65 | 29.6 | 25.17 |
| 1200 | 5 | 1.068 s | 1.066 s | 1.069 s | 0.268 | 0.6183 | 1 | 1x64 | 39.04 | 39 | 34.56 |
| 1500 | 5 | 2.071 s | 2.065 s | 2.113 s | 2.33 | 0.6136 | 1 | 1x64 | 58.48 | 58.44 | 54 |
| 1536 | 5 | 2.238 s | 2.218 s | 2.251 s | 1.48 | 0.6175 | 1 | 1x64 | 61.1 | 61.06 | 56.62 |
| 2000 | 5 | 5.024 s | 4.969 s | 5.035 s | 1.31 | 0.628 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2048 | 5 | 5.361 s | 5.312 s | 5.396 s | 1.56 | 0.6241 | 1 | 1x64 | 105.1 | 105.1 | 100.7 |
| 2500 | 5 | 9.968 s | 9.959 s | 10.22 s | 2.59 | 0.638 | 1 | 1x64 | 154.5 | 154.4 | 150 |
| 3000 | 5 | 19.69 s | 17.54 s | 19.76 s | 11.3 | 0.7292 | 1 | 1x64 | 220.5 | 220.4 | 216 |
| 4000 | 5 | 40.03 s | 39.01 s | 42.85 s | 9.6 | 0.6254 | 1 | 1x64 | 388.5 | 388.4 | 384 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **4000**
- Mayor tamaño intentado: **4000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 18 tamaños): **3.053** +- 0.016 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.050**.

## blocked ikj (64) - `blocked`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5 | 0.439 µs | 0.427 µs | 0.441 µs | 3.24 | 0.4393 | 200000 | 2x10 | 4.506 | 4.342 | 0.0024 |
| 25 | 5 | 5.21 µs | 5.18 µs | 5.32 µs | 2.7 | 0.3332 | 19608 | 2x25 | 4.575 | 4.411 | 0.015 |
| 50 | 5 | 39.5 µs | 39.2 µs | 40.1 µs | 2.19 | 0.3158 | 2253 | 2x50 | 4.534 | 4.415 | 0.06 |
| 100 | 5 | 320 µs | 319 µs | 321 µs | 0.634 | 0.3203 | 305 | 2x64 | 4.813 | 4.653 | 0.24 |
| 200 | 5 | 2.53 ms | 2.52 ms | 2.55 ms | 1.17 | 0.3166 | 32 | 2x64 | 5.816 | 5.652 | 0.96 |
| 300 | 5 | 8.7 ms | 8.54 ms | 8.7 ms | 1.92 | 0.322 | 12 | 2x64 | 7.262 | 7.221 | 2.16 |
| 400 | 5 | 20.8 ms | 20.3 ms | 20.9 ms | 2.7 | 0.3255 | 5 | 2x64 | 9.56 | 8.278 | 3.84 |
| 500 | 5 | 40.7 ms | 40.3 ms | 40.8 ms | 1.26 | 0.3258 | 3 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 43 ms | 42.4 ms | 43.5 ms | 2.35 | 0.3203 | 3 | 2x64 | 12.83 | 10.73 | 6.291 |
| 600 | 5 | 70 ms | 69.7 ms | 70.2 ms | 0.616 | 0.3238 | 2 | 2x64 | 15.96 | 13.08 | 8.64 |
| 800 | 5 | 164 ms | 164 ms | 165 ms | 0.743 | 0.3195 | 1 | 1x64 | 19.84 | 19.8 | 15.36 |
| 1000 | 5 | 329 ms | 326 ms | 330 ms | 1.34 | 0.3286 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 366 ms | 359 ms | 367 ms | 2.02 | 0.3408 | 1 | 1x64 | 29.65 | 29.61 | 25.17 |
| 1200 | 5 | 554 ms | 553 ms | 558 ms | 0.793 | 0.3204 | 1 | 1x64 | 39.04 | 39 | 34.56 |
| 1500 | 5 | 1.096 s | 1.089 s | 1.11 s | 1.85 | 0.3247 | 1 | 1x64 | 58.48 | 58.44 | 54 |
| 1536 | 5 | 1.154 s | 1.153 s | 1.163 s | 0.828 | 0.3184 | 1 | 1x64 | 61.1 | 61.06 | 56.62 |
| 2000 | 5 | 2.626 s | 2.626 s | 2.635 s | 0.36 | 0.3283 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2048 | 5 | 3.704 s | 3.69 s | 3.704 s | 0.386 | 0.4312 | 1 | 1x64 | 105.1 | 105.1 | 100.7 |
| 2500 | 5 | 5.382 s | 5.349 s | 5.384 s | 0.641 | 0.3444 | 1 | 1x64 | 154.5 | 154.4 | 150 |
| 3000 | 5 | 9.923 s | 9.626 s | 10.11 s | 4.91 | 0.3675 | 1 | 1x64 | 220.5 | 220.4 | 216 |
| 4000 | 5 | 22.51 s | 21.79 s | 22.68 s | 3.93 | 0.3518 | 1 | 1x64 | 388.5 | 388.4 | 384 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **4000**
- Mayor tamaño intentado: **4000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 18 tamaños): **3.040** +- 0.016 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.029**.
