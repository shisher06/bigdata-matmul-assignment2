# Resumen de resultados - Parte B (dispersas)

Entradas: `data_sparse/`, no-ceros con posiciones uniformes e independientes (densidad = % de no-ceros), valores en (0, 1]. Mismas matrices lógicas (mismo fichero) para todos los métodos. Mediana de las repeticiones. «csr» = solo el producto CSR x CSR (la conversión denso -> CSR de A y B se mide aparte); «csr + conv.» = producto + conversión.

## n = 4000

| densidad (%) | nnz(A) | nnz(C) | densidad C (%) | esperada (%) | csr | conversión | csr + conv. | blocked ikj (64) | blocked / csr | blocked / (csr + conv.) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 16029 | 63693 | 0.398 | 0.401 | 2.14 ms | 40.8 ms | 42.9 ms | 21.85 s | 1.02e+04x | 509x |
| 1 | 159986 | 5263056 | 32.9 | 33 | 91.8 ms | 46.3 ms | 138 ms | 21.62 s | 236x | 157x |

- Densidad de cruce csr = blocked (interpolación log-log): solo producto **- %**; con conversión **- %** («-» = no hay cruce en el rango medido).

## Memoria (MB)

«estructuras» = bytes de los datos del método: densos 3·8n²; csr = CSR de A, B y C (12 B por no-cero + 8(n+1) B). «WS tras multiplicar» = working set actual del proceso justo después del producto (en csr, las densas de entrada ya liberadas). «pico» = pico del working set del proceso (incluye la lectura de los ficheros densos).

| n | densidad (%) | csr: estructuras | csr: WS tras multiplicar | csr: pico | denso: estructuras | denso: WS tras multiplicar | denso: pico |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 | 0.1 | 1.246 | 6.111 | 260.8 | 384 | 388.4 | 388.5 |
| 4000 | 1 | 67.09 | 71.47 | 264.3 | 384 | 388.4 | 388.5 |

## Corrección

- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos en 2 de 2 casos comparables: 4000/0.1%, 4000/1%.
- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): 3.75e-16 (tolerancia rtol = 1e-9).
- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.

## blocked ikj (64) - `blocked`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | densidad (%) | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 | 0.1 | 5 | 21.85 s | 21.73 s | 21.93 s | 0.901 | 0.3414 | 1 | 1x64 | 388.5 | 388.4 | 384 |
| 4000 | 1 | 5 | 21.62 s | 21.61 s | 21.67 s | 0.307 | 0.3378 | 1 | 1x64 | 388.5 | 388.4 | 384 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **4000**
- Mayor tamaño intentado: **4000**
- Sin timeouts ni fallos de memoria.

## CSR (Gustavson) - `csr`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | densidad (%) | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | conversión | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4000 | 0.1 | 5 | 2.14 ms | 2.13 ms | 2.17 ms | 1.64 | 3.349e-05 | 38 | 2x64 | 40.8 ms | 260.8 | 6.111 | 1.246 |
| 4000 | 1 | 5 | 91.8 ms | 91.3 ms | 92.4 ms | 1.19 | 0.001434 | 2 | 2x64 | 46.3 ms | 264.3 | 71.47 | 67.09 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **4000**
- Mayor tamaño intentado: **4000**
- Sin timeouts ni fallos de memoria.
