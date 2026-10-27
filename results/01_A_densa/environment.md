# Entorno de ejecución

- Fecha (UTC): 2026-10-27T15:24:14+00:00
- Sistema operativo: Windows 11 Home 26H2 (build 26300.9711) (platform: Windows-10-10.0.26300-SP0)
- CPU: AMD Ryzen 7 4800H with Radeon Graphics
- Núcleos físicos / lógicos: 8 / 16
- RAM total: 15.4 GiB
- Python: CPython 3.11.9 (MSC v.1938 64 bit (AMD64))
- GIL activado: None
- Temporizador: time.perf_counter_ns (monótono=True, resolución=1e-07 s)
- C: gcc.EXE (GCC) 11.2.0 (x86_64-w64-mingw32); flags: `-std=c11 -Wall -Wextra -ffp-contract=off -O2` (los cuatro métodos en el mismo binario)
- numpy (solo verificación y análisis): 2.4.6
- matplotlib (solo gráficas): 3.11.2
- psutil (opcional): 7.2.2
- Variables de hilos en el shell: ninguna definida
- battery_percent: 100
- power_plugged: True
- cpu_freq_mhz_current: 2900.0
- cpu_freq_mhz_max: 2900.0

## Campaña

- Tamaños: [10, 25, 50, 100, 200, 300, 400, 500, 512, 600, 800, 1000, 1024, 1200, 1500, 1536, 2000, 2048, 2500, 3000, 4000]; repeticiones: 5; límite de tiempo: 300 s por proceso; presupuesto de memoria: 4096 MB por proceso
- `ijk`: `build/c/matmul.exe --method ijk`
- `ikj`: `build/c/matmul.exe --method ikj`
- `blocked`: `build/c/matmul.exe --method blocked --block 64`

> Todos los kernels (ijk, ikj, blocked, csr) son secuenciales: un solo hilo (threads = 1); el número de hilos del SO de cada proceso queda en os_threads_max.
> El runner fija OMP/OPENBLAS/MKL_NUM_THREADS=1 en los procesos hijo; NumPy solo se usa para verificar, fuera del cronómetro.
