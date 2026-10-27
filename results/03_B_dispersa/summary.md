# Resumen de resultados - Parte B (dispersas)

Entradas: `data_sparse/`, no-ceros con posiciones uniformes e independientes (densidad = % de no-ceros), valores en (0, 1]. Mismas matrices lógicas (mismo fichero) para todos los métodos. Mediana de las repeticiones. «csr» = solo el producto CSR x CSR (la conversión denso -> CSR de A y B se mide aparte); «csr + conv.» = producto + conversión.

## n = 1000

| densidad (%) | nnz(A) | nnz(C) | densidad C (%) | esperada (%) | csr | conversión | csr + conv. | ijk (baseline, A1) | blocked ikj (64) | blocked / csr | blocked / (csr + conv.) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 969 | 1067 | 0.107 | 0.0939 | 26.1 µs | 2.58 ms | 2.61 ms | 934 ms | 321 ms | 1.23e+04x | 123x |
| 0.5 | 4957 | 23757 | 2.38 | 2.43 | 983 µs | 2.79 ms | 3.78 ms | 925 ms | 317 ms | 322x | 83.8x |
| 1 | 9964 | 94450 | 9.45 | 9.45 | 3.88 ms | 2.98 ms | 6.87 ms | 935 ms | 316 ms | 81.5x | 46.1x |
| 2 | 19707 | 328371 | 32.8 | 32.2 | 5.74 ms | 3.31 ms | 9.05 ms | 934 ms | 315 ms | 54.9x | 34.8x |
| 5 | 49850 | 918407 | 91.8 | 91.7 | 14.5 ms | 4.15 ms | 18.6 ms | 929 ms | 315 ms | 21.8x | 16.9x |
| 10 | 99757 | 999966 | 100 | 100 | 22 ms | 5.5 ms | 27.5 ms | 927 ms | 314 ms | 14.3x | 11.4x |
| 20 | 199650 | 1000000 | 100 | 100 | 52.3 ms | 8.73 ms | 61.1 ms | 923 ms | 315 ms | 6.03x | 5.16x |
| 30 | 299945 | 1000000 | 100 | 100 | 99.2 ms | 12.3 ms | 111 ms | 924 ms | 316 ms | 3.19x | 2.84x |
| 50 | 500386 | 1000000 | 100 | 100 | 280 ms | 17.3 ms | 297 ms | 921 ms | 316 ms | 1.13x | 1.06x |

- Densidad de cruce csr = blocked (interpolación log-log): solo producto **- %**; con conversión **- %** («-» = no hay cruce en el rango medido).

## n = 2000

| densidad (%) | nnz(A) | nnz(C) | densidad C (%) | esperada (%) | csr | conversión | csr + conv. | ijk (baseline, A1) | blocked ikj (64) | blocked / csr | blocked / (csr + conv.) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 4035 | 8009 | 0.2 | 0.203 | 238 µs | 10.4 ms | 10.7 ms | 13.52 s | 2.611 s | 1.1e+04x | 245x |
| 0.5 | 19654 | 189927 | 4.75 | 4.71 | 9.27 ms | 11.1 ms | 20.4 ms | 13.97 s | 2.58 s | 278x | 126x |
| 1 | 39982 | 723977 | 18.1 | 18.1 | 13.4 ms | 12 ms | 25.4 ms | 15 s | 2.593 s | 193x | 102x |
| 2 | 79890 | 2200118 | 55 | 55 | 34.5 ms | 12.9 ms | 47.4 ms | 14.46 s | 2.576 s | 74.6x | 54.3x |
| 5 | 200753 | 3973984 | 99.3 | 99.4 | 70.9 ms | 16.3 ms | 87.3 ms | 15.28 s | 2.574 s | 36.3x | 29.5x |
| 10 | 400039 | 4000000 | 100 | 100 | 147 ms | 21.7 ms | 169 ms | 15.25 s | 2.573 s | 17.5x | 15.3x |
| 20 | 800612 | 4000000 | 100 | 100 | 456 ms | 34.1 ms | 490 ms | 16.05 s | 2.611 s | 5.73x | 5.33x |
| 30 | 1200871 | 4000000 | 100 | 100 | 922 ms | 49.1 ms | 971 ms | 15.42 s | 2.583 s | 2.8x | 2.66x |
| 50 | 1999895 | 4000000 | 100 | 100 | 2.279 s | 69.5 ms | 2.348 s | 13.91 s | 2.582 s | 1.13x | 1.1x |

- Densidad de cruce csr = blocked (interpolación log-log): solo producto **- %**; con conversión **- %** («-» = no hay cruce en el rango medido).

## Memoria (MB)

«estructuras» = bytes de los datos del método: densos 3·8n²; csr = CSR de A, B y C (12 B por no-cero + 8(n+1) B). «WS tras multiplicar» = working set actual del proceso justo después del producto (en csr, las densas de entrada ya liberadas). «pico» = pico del working set del proceso (incluye la lectura de los ficheros densos).

| n | densidad (%) | csr: estructuras | csr: WS tras multiplicar | csr: pico | denso: estructuras | denso: WS tras multiplicar | denso: pico |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 0.1 | 0.06114 | 4.698 | 20.44 | 24 | 28.44 | 28.48 |
| 1000 | 0.5 | 0.427 | 5.095 | 20.54 | 24 | 28.44 | 28.48 |
| 1000 | 1 | 1.397 | 6.451 | 20.66 | 24 | 28.44 | 28.48 |
| 1000 | 2 | 4.443 | 8.831 | 20.9 | 24 | 28.44 | 28.48 |
| 1000 | 5 | 12.25 | 16.66 | 34.39 | 24 | 28.44 | 28.48 |
| 1000 | 10 | 14.42 | 19.73 | 35.81 | 24 | 28.44 | 28.48 |
| 1000 | 20 | 16.82 | 21.32 | 37.38 | 24 | 28.44 | 28.48 |
| 1000 | 30 | 19.22 | 23.62 | 31.62 | 24 | 28.44 | 28.48 |
| 1000 | 50 | 24.02 | 28.44 | 36.46 | 24 | 28.44 | 28.48 |
| 2000 | 0.1 | 0.2407 | 4.579 | 68.53 | 96 | 100.4 | 100.5 |
| 2000 | 0.5 | 2.8 | 7.254 | 68.91 | 96 | 100.4 | 100.5 |
| 2000 | 1 | 9.694 | 14.08 | 69.4 | 96 | 100.4 | 100.5 |
| 2000 | 2 | 28.37 | 33.49 | 70.37 | 96 | 100.4 | 100.5 |
| 2000 | 5 | 52.55 | 57.02 | 121.3 | 96 | 100.4 | 100.5 |
| 2000 | 10 | 57.65 | 62.06 | 94.06 | 96 | 100.4 | 100.5 |
| 2000 | 20 | 67.27 | 71.66 | 103.7 | 96 | 100.4 | 100.5 |
| 2000 | 30 | 76.88 | 81.3 | 113.3 | 96 | 100.4 | 100.5 |
| 2000 | 50 | 96.03 | 100.4 | 132.5 | 96 | 100.4 | 100.5 |

## Corrección

- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos en 18 de 18 casos comparables: 1000/0.1%, 1000/0.5%, 1000/1%, 1000/2%, 1000/5%, 1000/10%, 1000/20%, 1000/30%, 1000/50%, 2000/0.1%, 2000/0.5%, 2000/1%, 2000/2%, 2000/5%, 2000/10%, 2000/20%, 2000/30%, 2000/50%.
- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): 2.94e-15 (tolerancia rtol = 1e-9).
- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.

## ijk (baseline, A1) - `ijk`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | densidad (%) | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 0.1 | 5 | 934 ms | 933 ms | 934 ms | 0.115 | 0.9337 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 0.5 | 5 | 925 ms | 923 ms | 926 ms | 0.334 | 0.9253 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 1 | 5 | 935 ms | 922 ms | 940 ms | 1.86 | 0.9352 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 2 | 5 | 934 ms | 924 ms | 935 ms | 1.17 | 0.9338 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 5 | 5 | 929 ms | 927 ms | 932 ms | 0.562 | 0.9289 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 10 | 5 | 927 ms | 924 ms | 927 ms | 0.311 | 0.9268 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 20 | 5 | 923 ms | 922 ms | 924 ms | 0.183 | 0.9229 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 30 | 5 | 924 ms | 921 ms | 926 ms | 0.477 | 0.9241 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 50 | 5 | 921 ms | 919 ms | 924 ms | 0.471 | 0.9205 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 2000 | 0.1 | 5 | 13.52 s | 12.83 s | 13.65 s | 6.02 | 1.69 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 0.5 | 5 | 13.97 s | 13.68 s | 14.17 s | 3.49 | 1.746 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 1 | 5 | 15 s | 14.62 s | 15.4 s | 5.19 | 1.875 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 2 | 5 | 14.46 s | 14.01 s | 14.52 s | 3.52 | 1.808 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 5 | 5 | 15.28 s | 15.04 s | 15.7 s | 4.28 | 1.91 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 10 | 5 | 15.25 s | 14.94 s | 15.42 s | 3.16 | 1.907 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 20 | 5 | 16.05 s | 15.46 s | 16.12 s | 4.12 | 2.007 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 30 | 5 | 15.42 s | 15.18 s | 15.53 s | 2.28 | 1.928 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 50 | 5 | 13.91 s | 13.69 s | 13.93 s | 1.69 | 1.739 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## blocked ikj (64) - `blocked`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | densidad (%) | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 0.1 | 5 | 321 ms | 317 ms | 322 ms | 1.43 | 0.3206 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 0.5 | 5 | 317 ms | 315 ms | 328 ms | 3.93 | 0.3165 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 1 | 5 | 316 ms | 315 ms | 318 ms | 0.922 | 0.3163 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 2 | 5 | 315 ms | 313 ms | 317 ms | 1.17 | 0.3153 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 5 | 5 | 315 ms | 315 ms | 315 ms | 0.222 | 0.3153 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 10 | 5 | 314 ms | 312 ms | 317 ms | 1.5 | 0.3143 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 20 | 5 | 315 ms | 314 ms | 317 ms | 1.04 | 0.3154 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 30 | 5 | 316 ms | 316 ms | 316 ms | 0.145 | 0.3163 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 1000 | 50 | 5 | 316 ms | 315 ms | 316 ms | 0.563 | 0.3157 | 1 | 1x64 | 28.48 | 28.44 | 24 |
| 2000 | 0.1 | 5 | 2.611 s | 2.6 s | 2.613 s | 0.517 | 0.3263 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 0.5 | 5 | 2.58 s | 2.573 s | 2.584 s | 0.444 | 0.3226 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 1 | 5 | 2.593 s | 2.588 s | 2.596 s | 0.312 | 0.3242 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 2 | 5 | 2.576 s | 2.565 s | 2.584 s | 0.732 | 0.322 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 5 | 5 | 2.574 s | 2.57 s | 2.58 s | 0.413 | 0.3217 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 10 | 5 | 2.573 s | 2.567 s | 2.573 s | 0.233 | 0.3216 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 20 | 5 | 2.611 s | 2.556 s | 2.656 s | 3.84 | 0.3264 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 30 | 5 | 2.583 s | 2.563 s | 2.601 s | 1.49 | 0.3229 | 1 | 1x64 | 100.5 | 100.4 | 96 |
| 2000 | 50 | 5 | 2.582 s | 2.568 s | 2.587 s | 0.729 | 0.3228 | 1 | 1x64 | 100.5 | 100.4 | 96 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.

## CSR (Gustavson) - `csr`

Compilador: gcc 11.2.0; flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2`. «calent.» = ejecuciones x tamaño del calentamiento (incluye la calibración del lote).

| n | densidad (%) | reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | conversión | pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 0.1 | 5 | 26.1 µs | 25.5 µs | 26.7 µs | 4.46 | 2.608e-05 | 1780 | 2x64 | 2.58 ms | 20.44 | 4.698 | 0.06114 |
| 1000 | 0.5 | 5 | 983 µs | 979 µs | 996 µs | 1.79 | 0.000983 | 104 | 2x64 | 2.79 ms | 20.54 | 5.095 | 0.427 |
| 1000 | 1 | 5 | 3.88 ms | 3.87 ms | 3.89 ms | 0.512 | 0.003883 | 26 | 2x64 | 2.98 ms | 20.66 | 6.451 | 1.397 |
| 1000 | 2 | 5 | 5.74 ms | 5.68 ms | 5.74 ms | 1.08 | 0.00574 | 18 | 2x64 | 3.31 ms | 20.9 | 8.831 | 4.443 |
| 1000 | 5 | 5 | 14.5 ms | 14.4 ms | 14.6 ms | 1.39 | 0.01446 | 8 | 2x64 | 4.15 ms | 34.39 | 16.66 | 12.25 |
| 1000 | 10 | 5 | 22 ms | 22 ms | 22.1 ms | 0.571 | 0.02202 | 5 | 2x64 | 5.5 ms | 35.81 | 19.73 | 14.42 |
| 1000 | 20 | 5 | 52.3 ms | 51.4 ms | 52.4 ms | 2.02 | 0.05233 | 3 | 2x64 | 8.73 ms | 37.38 | 21.32 | 16.82 |
| 1000 | 30 | 5 | 99.2 ms | 98.7 ms | 99.4 ms | 0.696 | 0.09917 | 1 | 2x64 | 12.3 ms | 31.62 | 23.62 | 19.22 |
| 1000 | 50 | 5 | 280 ms | 280 ms | 280 ms | 0.316 | 0.2797 | 1 | 2x64 | 17.3 ms | 36.46 | 28.44 | 24.02 |
| 2000 | 0.1 | 5 | 238 µs | 237 µs | 245 µs | 3.19 | 2.972e-05 | 358 | 2x64 | 10.4 ms | 68.53 | 4.579 | 0.2407 |
| 2000 | 0.5 | 5 | 9.27 ms | 9.15 ms | 9.35 ms | 2.13 | 0.001159 | 11 | 2x64 | 11.1 ms | 68.91 | 7.254 | 2.8 |
| 2000 | 1 | 5 | 13.4 ms | 13.4 ms | 13.4 ms | 0.0337 | 0.00168 | 8 | 2x64 | 12 ms | 69.4 | 14.08 | 9.694 |
| 2000 | 2 | 5 | 34.5 ms | 34.4 ms | 35.2 ms | 2.28 | 0.004316 | 3 | 2x64 | 12.9 ms | 70.37 | 33.49 | 28.37 |
| 2000 | 5 | 5 | 70.9 ms | 70.3 ms | 71.3 ms | 1.3 | 0.008868 | 2 | 2x64 | 16.3 ms | 121.3 | 57.02 | 52.55 |
| 2000 | 10 | 5 | 147 ms | 145 ms | 147 ms | 1.46 | 0.01837 | 1 | 2x64 | 21.7 ms | 94.06 | 62.06 | 57.65 |
| 2000 | 20 | 5 | 456 ms | 455 ms | 456 ms | 0.289 | 0.05694 | 1 | 2x64 | 34.1 ms | 103.7 | 71.66 | 67.27 |
| 2000 | 30 | 5 | 922 ms | 918 ms | 926 ms | 0.922 | 0.1152 | 1 | 2x64 | 49.1 ms | 113.3 | 81.3 | 76.88 |
| 2000 | 50 | 5 | 2.279 s | 2.26 s | 2.296 s | 1.6 | 0.2848 | 1 | 2x64 | 69.5 ms | 132.5 | 100.4 | 96.03 |

(!) = menos de 5 repeticiones (justificado por coste; ver el informe).

### Límites

- Mayor tamaño probado dentro de los límites: **2000**
- Mayor tamaño intentado: **2000**
- Sin timeouts ni fallos de memoria.
