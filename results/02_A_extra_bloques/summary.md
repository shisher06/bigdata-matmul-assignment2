# Resumen - experimento aparte: tamaño de bloque de `blocked`

Mediana del tiempo por multiplicación (IQR/mediana entre paréntesis) y ns por iteración interna. El mejor bloque de cada n en negrita.

| n | block 16 | block 32 | block 64 | block 128 | block 256 |
|---:|---:|---:|---:|---:|---:|
| 500 | 45.5 ms (4.8 %), 0.364 ns | **41.6 ms (1.2e+02 %), 0.333 ns** | 42.3 ms (51 %), 0.338 ns | 54.5 ms (15 %), 0.436 ns | 55.2 ms (3 %), 0.441 ns |
| 512 | 52.5 ms (3 %), 0.391 ns | 46.3 ms (4.2 %), 0.345 ns | **43.5 ms (3.6 %), 0.324 ns** | 56.6 ms (0.97 %), 0.421 ns | 55.8 ms (3.9 %), 0.415 ns |
| 1000 | 356 ms (1.9 %), 0.356 ns | 334 ms (3.1 %), 0.334 ns | **327 ms (2.5 %), 0.327 ns** | 413 ms (2.9 %), 0.413 ns | 419 ms (1.6 %), 0.419 ns |
| 1024 | 416 ms (1.2 %), 0.387 ns | **360 ms (1.6 %), 0.335 ns** | 369 ms (4.3 %), 0.344 ns | 507 ms (1.8 %), 0.472 ns | 448 ms (4.1 %), 0.417 ns |
| 2000 | 2.843 s (1.5 %), 0.355 ns | 2.638 s (0.45 %), 0.330 ns | **2.631 s (0.22 %), 0.329 ns** | 3.306 s (0.48 %), 0.413 ns | 3.373 s (0.56 %), 0.422 ns |

## Corrección

- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos en 5 de 5 casos comparables: 500, 512, 1000, 1024, 2000.
- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): 5.56e-15 (tolerancia rtol = 1e-9).
- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.

## block 16 - `blocked-16`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 5 | 45.5 ms | 44.8 ms | 47 ms | 4.85 | 0.364 | 3 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 52.5 ms | 51.9 ms | 53.5 ms | 3.05 | 0.3909 | 2 | 2x64 | 12.83 | 10.73 | 6.291 |
| 1000 | 5 | 356 ms | 353 ms | 360 ms | 1.88 | 0.3557 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 416 ms | 413 ms | 418 ms | 1.18 | 0.3871 | 1 | 1x64 | 29.65 | 29.6 | 25.17 |
| 2000 | 5 | 2.843 s | 2.836 s | 2.88 s | 1.55 | 0.3554 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## block 32 - `blocked-32`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 5 | 41.6 ms | 41.1 ms | 89.5 ms | 116 | 0.3326 | 3 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 46.3 ms | 45.7 ms | 47.7 ms | 4.22 | 0.3452 | 3 | 2x64 | 12.83 | 10.73 | 6.291 |
| 1000 | 5 | 334 ms | 330 ms | 340 ms | 3.05 | 0.3345 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 360 ms | 357 ms | 363 ms | 1.58 | 0.3351 | 1 | 1x64 | 29.65 | 29.61 | 25.17 |
| 2000 | 5 | 2.638 s | 2.635 s | 2.647 s | 0.448 | 0.3298 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## block 64 - `blocked-64`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 5 | 42.3 ms | 40.9 ms | 62.4 ms | 50.8 | 0.3383 | 3 | 1x64 | 12.45 | 10.44 | 6 |
| 512 | 5 | 43.5 ms | 43.4 ms | 45 ms | 3.62 | 0.3239 | 3 | 2x64 | 12.83 | 10.73 | 6.291 |
| 1000 | 5 | 327 ms | 320 ms | 329 ms | 2.46 | 0.3268 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 369 ms | 357 ms | 373 ms | 4.35 | 0.3435 | 1 | 1x64 | 29.65 | 29.6 | 25.17 |
| 2000 | 5 | 2.631 s | 2.629 s | 2.635 s | 0.218 | 0.3288 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## block 128 - `blocked-128`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 5 | 54.5 ms | 53.1 ms | 61.2 ms | 14.8 | 0.4357 | 2 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 56.6 ms | 56.1 ms | 56.6 ms | 0.968 | 0.4215 | 2 | 2x64 | 12.83 | 10.73 | 6.291 |
| 1000 | 5 | 413 ms | 413 ms | 425 ms | 2.92 | 0.4134 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 507 ms | 501 ms | 510 ms | 1.79 | 0.4724 | 1 | 1x64 | 29.65 | 29.6 | 25.17 |
| 2000 | 5 | 3.306 s | 3.3 s | 3.316 s | 0.476 | 0.4133 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## block 256 - `blocked-256`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 5 | 55.2 ms | 53.7 ms | 55.3 ms | 2.98 | 0.4414 | 2 | 2x64 | 12.44 | 10.44 | 6 |
| 512 | 5 | 55.8 ms | 55.4 ms | 57.5 ms | 3.88 | 0.4155 | 2 | 2x64 | 12.83 | 10.73 | 6.291 |
| 1000 | 5 | 419 ms | 418 ms | 425 ms | 1.59 | 0.4189 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1024 | 5 | 448 ms | 440 ms | 458 ms | 4.06 | 0.4171 | 1 | 1x64 | 29.65 | 29.61 | 25.17 |
| 2000 | 5 | 3.373 s | 3.367 s | 3.385 s | 0.558 | 0.4216 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.
