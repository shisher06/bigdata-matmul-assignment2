# Resumen de resultados - Parte A (densas)

Estadísticos sobre las ejecuciones con `status = OK`: mediana y rango intercuartílico (IQR = Q3 - Q1). Tiempos por multiplicación. Memoria en MB decimales (10⁶ B). Cada ejecución es un proceso nuevo. Mismas entradas que la Práctica 1.

## Comparación entre métodos (mediana del tiempo por multiplicación)

| n | ikj (loop order) | ikj, loops aligned to 32 B | blocked, one tile (no tiling) | blocked ikj (64) |
|---:|---:|---:|---:|---:|
| 50 | 63.2 µs | 61.5 µs | 37.8 µs | 37.9 µs |
| 100 | 591 µs | 414 µs | 407 µs | 311 µs |
| 200 | 4.55 ms | 2.82 ms | 3.19 ms | 2.5 ms |
| 500 | 69 ms | 42.7 ms | 42.3 ms | 40.1 ms |
| 1000 | 595 ms | 461 ms | 458 ms | 319 ms |
| 2000 | 4.81 s | 3.827 s | 3.837 s | 2.631 s |

«-» = sin medida válida para ese tamaño (ver *Límites*).

## Coste por iteración interna (ns = tiempo / n³)

| n | ikj (loop order) | ikj, loops aligned to 32 B | blocked, one tile (no tiling) | blocked ikj (64) |
|---:|---:|---:|---:|---:|
| 50 | 0.505 | 0.492 | 0.302 | 0.303 |
| 100 | 0.591 | 0.414 | 0.407 | 0.311 |
| 200 | 0.569 | 0.353 | 0.399 | 0.313 |
| 500 | 0.552 | 0.342 | 0.338 | 0.321 |
| 1000 | 0.595 | 0.461 | 0.458 | 0.319 |
| 2000 | 0.601 | 0.478 | 0.48 | 0.329 |

## Memoria: pico del working set del proceso completo (MB)

Medido por el runner con `GetProcessMemoryInfo` sobre el proceso hijo al terminar (la misma métrica que en la Práctica 1).

| n | ikj (loop order) | ikj, loops aligned to 32 B | blocked, one tile (no tiling) | blocked ikj (64) | modelo 3·8n² |
|---:|---:|---:|---:|---:|---:|
| 50 | 4.538 | 4.542 | 4.534 | 4.538 | 0.06 |
| 100 | 4.813 | 4.817 | 4.813 | 4.813 | 0.24 |
| 200 | 5.816 | 5.82 | 5.816 | 5.816 | 0.96 |
| 500 | 12.44 | 12.45 | 12.44 | 12.44 | 6 |
| 1000 | 28.48 | 28.49 | 28.48 | 28.48 | 24 |
| 2000 | 100.5 | 100.5 | 100.5 | 100.5 | 96 |

## Corrección

- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos en 6 de 6 casos comparables: 50, 100, 200, 500, 1000, 2000.
- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): 5.56e-15 (tolerancia rtol = 1e-9).
- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.

## ikj (loop order) - `ikj`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 5 | 63.2 µs | 63 µs | 63.5 µs | 0.882 | 0.5052 | 1409 | 2x50 | 4.538 | 4.415 | 0.06 |
| 100 | 5 | 591 µs | 587 µs | 599 µs | 2.11 | 0.5915 | 171 | 2x64 | 4.813 | 4.649 | 0.24 |
| 200 | 5 | 4.55 ms | 4.53 ms | 4.59 ms | 1.47 | 0.5689 | 23 | 2x64 | 5.816 | 5.657 | 0.96 |
| 500 | 5 | 69 ms | 65.9 ms | 72.8 ms | 9.99 | 0.5519 | 2 | 2x64 | 12.44 | 10.44 | 6 |
| 1000 | 5 | 595 ms | 592 ms | 598 ms | 0.991 | 0.595 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 2000 | 5 | 4.81 s | 4.809 s | 4.819 s | 0.205 | 0.6013 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 5 tamaños): **3.009** +- 0.016 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.009**.

## ikj, loops aligned to 32 B - `ikj-align32`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2 -falign-loops=32`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 5 | 61.5 µs | 61.4 µs | 61.5 µs | 0.149 | 0.4917 | 1637 | 2x50 | 4.542 | 4.42 | 0.06 |
| 100 | 5 | 414 µs | 411 µs | 418 µs | 1.72 | 0.414 | 236 | 2x64 | 4.817 | 4.653 | 0.24 |
| 200 | 5 | 2.82 ms | 2.82 ms | 2.87 ms | 1.87 | 0.3529 | 31 | 2x64 | 5.82 | 5.661 | 0.96 |
| 500 | 5 | 42.7 ms | 41.7 ms | 43 ms | 3.02 | 0.3419 | 3 | 2x64 | 12.45 | 10.44 | 6 |
| 1000 | 5 | 461 ms | 457 ms | 468 ms | 2.22 | 0.4608 | 1 | 1x64 | 28.49 | 28.45 | 24 |
| 2000 | 5 | 3.827 s | 3.806 s | 3.829 s | 0.59 | 0.4784 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 5 tamaños): **3.071** +- 0.060 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.071**.

## blocked, one tile (no tiling) - `blocked-notile`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 5 | 37.8 µs | 37.4 µs | 37.8 µs | 1.04 | 0.3021 | 2370 | 2x50 | 4.534 | 4.415 | 0.06 |
| 100 | 5 | 407 µs | 404 µs | 407 µs | 0.861 | 0.4066 | 244 | 2x64 | 4.813 | 4.653 | 0.24 |
| 200 | 5 | 3.19 ms | 3.06 ms | 3.25 ms | 5.93 | 0.399 | 33 | 2x64 | 5.816 | 5.657 | 0.96 |
| 500 | 5 | 42.3 ms | 42 ms | 42.8 ms | 2.1 | 0.3382 | 3 | 2x64 | 12.44 | 10.44 | 6 |
| 1000 | 5 | 458 ms | 458 ms | 473 ms | 3.4 | 0.4579 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 2000 | 5 | 3.837 s | 3.796 s | 3.837 s | 1.08 | 0.4796 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 5 tamaños): **3.058** +- 0.056 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.058**.

## blocked ikj (64) - `blocked`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 5 | 37.9 µs | 37.8 µs | 38.2 µs | 1.08 | 0.3029 | 1491 | 2x50 | 4.538 | 4.411 | 0.06 |
| 100 | 5 | 311 µs | 308 µs | 317 µs | 2.59 | 0.3112 | 305 | 2x64 | 4.813 | 4.653 | 0.24 |
| 200 | 5 | 2.5 ms | 2.48 ms | 2.51 ms | 0.958 | 0.3127 | 41 | 2x64 | 5.816 | 5.657 | 0.96 |
| 500 | 5 | 40.1 ms | 39.7 ms | 40.7 ms | 2.48 | 0.3208 | 3 | 2x64 | 12.44 | 10.44 | 6 |
| 1000 | 5 | 319 ms | 316 ms | 319 ms | 0.924 | 0.3189 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 2000 | 5 | 2.631 s | 2.585 s | 2.649 s | 2.42 | 0.3289 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

### Crecimiento frente al modelo cúbico

- Pendiente log-log de la mediana (n >= 100, 5 tamaños): **3.017** +- 0.004 (error estándar); el modelo algorítmico predice 3.
- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): **3.017**.
