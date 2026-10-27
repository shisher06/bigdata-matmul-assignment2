# Assignment 2 - Optimised dense matrix multiplication and sparse matrices

Big Data, Grado en Ciencia e Ingeniería de Datos (ULPGC), 2026-2027 - Guillermo Oltra Rodriguez.

Empirical study in two parts, built on the validated C implementation of Assignment 1:

- **Part A (dense optimisation):** the Assignment 1 triple loop `i-j-k` (baseline) against two
  optimised versions, **loop reordering `i-k-j`** and **cache blocking (tiled `i-k-j`)**, on the
  same input files, the same numeric type (`float64`), the same compiler flags and the same timing
  boundary. All runs are sequential (one thread).
- **Part B (sparse matrices):** an own **CSR x CSR (Gustavson)** multiplication against the dense
  methods on matrices with 9 declared densities (0.1 % to 50 % nonzeros), with the dense to CSR
  conversion timed separately and the input/output nonzero counts reported.

**Research questions.** (A) How much do loop reordering and cache blocking reduce the runtime of
the Assignment 1 triple loop, and do they remove the cache effects found there (growth faster
than n³ and the slowdowns at n = 512, 1024, 1536)? (B) For which tested densities and sizes is the
CSR multiplication faster than the best dense method, and how do the conversion and the output
fill-in reduce that advantage?

- **Report (English):** [`informe/informe.md`](informe/informe.md) and PDF
  `informe/Assignment02_OltraRodriguez_Report.pdf`.
- Source-code comments, the per-campaign summaries (`summary.md`) and `results/LEEME.md` are in
  Spanish, as in Assignment 1.

## 0. What is reused from Assignment 1

Assignment 1 repository: `bigdata-matmul-assignment1`, commit `e947d18` (2026-10-16), folder
`practica1/`. Everything below was **copied into this folder** (so this repository is
self-contained) and changed only where stated.

| Assignment 1 file | Here | Changes |
|---|---|---|
| `src/c/matmul.c` (C worker) | `src/c/matmul.c` | `matmul_ijk` (the kernel) is **unchanged** and is the baseline. Added `--method ijk\|ikj\|blocked\|csr` and `--block`, the two optimised kernels, CSR structures, the conversion timing and new JSON fields. Timer, file I/O, warm-up, batching, `fsum` checksum and memory reading are the same code. |
| `data/manifest.json` + `src/python/datagen.py` | same | **Same input files** (same generator and seed 2026; same SHA-256, checked by a test). Added the sparse generator (`--densities`) and new sizes. |
| `src/python/matrix_io.py`, `src/python/verify.py` | same | No changes (same tolerances `rtol = 1e-9`, `atol = 1e-12`). |
| `matmul_ijk`/`checksum_fsum` of `src/python/matmul.py` | `src/python/reference.py` | Copied without changes; used only by the tests as the bit-exact reference. |
| `scripts/run_benchmarks.py` | same | Same protocol (fresh process, interleaved order, verification, budgets, `--resume`); configurations are now methods instead of languages; cases are `(n)` or `(n, density)`. |
| `scripts/build.py`, `scripts/env_info.py` | same | Only the C `-O2` build (the Assignment 1 main C configuration); Java removed. |
| `scripts/analyze.py` | same | Same statistics and plot style; new tables and figures for Parts A and B. |
| `tests/test_workers.py` | `tests/test_workers.py` + `tests/test_data.py` | Same black-box tests applied to every method, plus sparse tests. |
| `informe/build_pdf.py` | same | Only the output file name. |

## 1. Requirements

| Tool | Version used | Purpose |
|---|---|---|
| CPython | 3.11.9 | runner, data generation, tests and analysis |
| GCC (MinGW-w64) | 11.2.0, `x86_64-w64-mingw32` | build the C worker |
| numpy, matplotlib, psutil | 2.4.6, 3.11.2, 7.2.2 | verification, plots, thread sampling |
| markdown + Chrome/Edge | 3.x | only to build the PDF report |

```bash
py -3.11 -m pip install -r requirements.txt      # Linux/macOS: python3 -m pip ...
```

`gcc` must be on the `PATH`. On Windows use `py -3.11`; on Linux/macOS, `python3`.

## 2. Reproducing the whole study

From the `practica2/` folder:

```bash
# 1) Separate experiment: block size of the blocked method (justifies BLOCK = 64)
py -3.11 scripts/run_benchmarks.py --configs blocked-16 blocked-32 blocked-64 blocked-128 blocked-256 \
    --sizes 500 512 1000 1024 2000 --out results/02_A_extra_bloques/raw.csv

# 2) Part A: baseline vs the two optimised dense methods (n = 10 ... 4000)
py -3.11 scripts/run_benchmarks.py --configs ijk ikj blocked --out results/01_A_densa/raw.csv

# 3) Part B: CSR vs dense methods on sparse inputs (n = 1000, 2000; 9 densities)
py -3.11 scripts/run_benchmarks.py --configs csr blocked ijk --sizes 1000 2000 \
    --densities 0.1 0.5 1 2 5 10 20 30 50 --out results/03_B_dispersa/raw.csv

# 4) Part B, larger size: CSR vs blocked at n = 4000 (low densities)
py -3.11 scripts/run_benchmarks.py --configs csr blocked --sizes 4000 --densities 0.1 1 \
    --out results/04_B_dispersa_n4000/raw.csv

# 4b) Separate experiment (added after Part B): high densities, to find the CSR/dense crossover
py -3.11 scripts/run_benchmarks.py --configs csr blocked --sizes 1000 2000 --densities 60 70 85 100 \
    --out results/05_B_extra_densidades_altas/raw.csv

# 4c) Separate experiment (added after Part A): code alignment vs tiling
py -3.11 scripts/run_benchmarks.py --configs ikj ikj-align32 blocked-notile blocked \
    --sizes 50 100 200 500 1000 2000 --out results/06_A_extra_alineacion/raw.csv

# 5) Tables and plots
py -3.11 scripts/analyze.py --csv results/01_A_densa/raw.csv --out-dir results/01_A_densa \
    --p1-summary ../practica1/results/04_comparativa_3_lenguajes/summary.csv
py -3.11 scripts/analyze.py --csv results/02_A_extra_bloques/raw.csv --out-dir results/02_A_extra_bloques
py -3.11 scripts/analyze.py --csv results/03_B_dispersa/raw.csv --out-dir results/03_B_dispersa
py -3.11 scripts/analyze.py --csv results/04_B_dispersa_n4000/raw.csv --out-dir results/04_B_dispersa_n4000
py -3.11 scripts/analyze.py --csv results/03_B_dispersa/raw.csv results/05_B_extra_densidades_altas/raw.csv \
    --out-dir results/05_B_extra_densidades_altas          # Part B, all densities together
py -3.11 scripts/analyze.py --csv results/06_A_extra_alineacion/raw.csv --out-dir results/06_A_extra_alineacion --kind dense

# 6) PDF report (optional)
py -3.11 informe/build_pdf.py
```

`run_benchmarks.py` does everything in order: records the environment, **builds** the C worker
(`scripts/build.py`), **runs all tests before measuring**, generates/verifies the input matrices
and launches the repetitions. Each measurement is appended to the CSV as soon as it finishes; an
interrupted campaign resumes without duplicating rows (`--resume`). It never overwrites an
existing CSV. The `--p1-summary` option is optional (it only adds the comparison of the baseline
with the Assignment 1 measurement).

Individual steps:

```bash
py -3.11 scripts/build.py                          # builds build/c/matmul.exe (-O2) and the
                                                   # alignment-experiment variant matmul_O2align32.exe
py -3.11 -m unittest discover -s tests -v          # 24 tests (worker, data, runner)
py -3.11 src/python/datagen.py                     # dense inputs data/A_n.bin, data/B_n.bin
py -3.11 src/python/datagen.py --sizes 1000 2000 --densities 0.1 0.5 1 2 5 10 20 30 50
py -3.11 src/python/datagen.py --verify            # checks the SHA-256 of both manifests
```

Running the worker by hand (one JSON line on stdout):

```bash
build/c/matmul.exe --method ijk     --n 1000 --a data/A_1000.bin --b data/B_1000.bin
build/c/matmul.exe --method ikj     --n 1000 --a data/A_1000.bin --b data/B_1000.bin
build/c/matmul.exe --method blocked --block 64 --n 1000 --a data/A_1000.bin --b data/B_1000.bin
build/c/matmul.exe --method csr     --n 1000 --a data_sparse/A_1000_d1.bin --b data_sparse/B_1000_d1.bin
```

## 3. Layout

```
practica2/
├── README.md, requirements.txt
├── data/manifest.json             dense inputs (same files as Assignment 1) - .bin not versioned
├── data_sparse/manifest.json      sparse inputs: seed, density, nnz and SHA-256 of every file
├── src/
│   ├── c/matmul.c                 the four kernels + worker performing ONE measurement
│   └── python/
│       ├── datagen.py             deterministic generator (dense and sparse)
│       ├── matrix_io.py           I/O of the shared binary format
│       ├── verify.py              comparison with NumPy (verification only)
│       └── reference.py           Assignment 1 Python kernel, bit-exact reference for tests
├── build/build_info.json          exact compiler version and flags
├── scripts/
│   ├── build.py                   builds the C worker
│   ├── run_benchmarks.py          campaign: build -> tests -> data -> measurements -> CSV
│   ├── env_info.py                CPU, cores, RAM, OS, versions, flags, threads, power
│   └── analyze.py                 summary.csv/.md and plots/*.png
├── tests/
│   ├── test_workers.py            worker: every method, known answers, bit identity, sparse
│   └── test_data.py               inputs (same as Assignment 1), sparse generator, I/O, verifier
├── results/                       one folder per campaign (see results/LEEME.md)
└── informe/                       report (informe.md), build_pdf.py and the PDF
```

## 4. Methods

| Config | Kernel (`src/c/matmul.c`) | Storage | Idea |
|---|---|---|---|
| `ijk` | `matmul_ijk` (Assignment 1, unchanged) | dense row-major | baseline: inner loop walks `B` by **columns** (stride 8n bytes) |
| `ikj` | `matmul_ikj` | dense row-major | loop reordering: inner loop walks rows of `B` and `C` (stride 8 bytes) |
| `blocked` | `matmul_blocked`, `--block 64` | dense row-major | `i-k-j` on 64 x 64 tiles so that the data reused by the inner loops stay in cache |
| `csr` | `matmul_csr` (Gustavson) | CSR: `row_ptr` (int64), `col` (int32), `val` (float64) | only the nonzero products; dense accumulator row + column marker; output in CSR with sorted columns |

Separate experiments only: `blocked-16` ... `blocked-256` (block size), `blocked-notile` (one single
tile, i.e. the operations of `ikj` without tiling) and `ikj-align32` (same source built with
`-O2 -falign-loops=32`, so that the inner loop does not cross a 32-byte boundary).

All kernels and the CSR code are own code (no BLAS, no sparse library). **Every method adds the
products of each `C[i][j]` in the same order (k increasing, starting from 0.0) and without FMA,
so all four produce exactly the same bits as the Assignment 1 baseline** (checked by the SHA-256
of the result in every case). In `csr` the skipped products are exact zeros, and adding `+0.0`
does not change a double.

## 5. Measurement decisions (same as Assignment 1 unless stated)

| Aspect | Decision |
|---|---|
| Numeric type | `float64`. Dense inputs uniform in [0, 1); sparse nonzeros uniform in (0, 1]. |
| Dense inputs | Assignment 1 files: base seed 2026, `A_n`: `2026 * 1000003 + 2n`, `B_n`: +1, CPython `random.Random`. |
| Sparse inputs | Same binary format (dense, zeros stored) so every method reads the same logical matrices. Each cell is nonzero independently with probability `d` (uniform positions). Seed `A`: `(2026 * 1000003 + 2n) * 10^6 + 2 * round(1000 * pct)`, `B`: +1. The real nnz is in `data_sparse/manifest.json`. |
| Densities (Part B) | 0.1, 0.5, 1, 2, 5, 10, 20, 30, 50 % (sparsity = 100 - density). |
| Timer | Monotonic `QueryPerformanceCounter` (Windows) / `clock_gettime(CLOCK_MONOTONIC)`. |
| Timer boundary | **Kernel only**: the call that allocates `C` (and initialises it / builds the CSR of `C`) and runs the loops. File reading, warm-up, checksum and dump are outside. |
| Conversion (csr) | Dense to CSR of `A` and `B` is timed **separately** (`convert_ns`, one conversion per process). The report shows "product only" and "product + conversion". The output stays in CSR (CSR to dense is only for the dump, untimed). |
| Process | A **fresh process per repetition** and configuration. |
| Order | Interleaved: for each case and repetition all configurations run, rotating the order. |
| Repetitions | 5 per case. If the first takes > 120 s, 3 in total (`reps_planned`). |
| Very short tasks | Batch of multiplications in one timed region if one takes < 100 ms; time per multiplication = total / batch. For `csr` the calibration run is always done (its cost is not cubic). |
| Warm-up | 1 run on the 64 x 64 corner (or n x n if n < 64), never part of the sample. |
| Threads | One thread in all kernels; `OMP/OPENBLAS/MKL_NUM_THREADS=1` in the children. |
| Compiler | `gcc -std=c11 -O2 -ffp-contract=off` (Assignment 1 main configuration). gcc 11 does **not** auto-vectorise at `-O2`, so the differences come from memory access, not SIMD. |
| Statistics | Median and inter-quartile range (IQR). All raw measurements are kept. |

## 6. Correctness

**Before measuring**, 24 tests (`tests/`) with every method (`ijk`, `ikj`, `blocked` with block 64
and with block 5, which does not divide n, and `csr`): known answers (1x1, 2x2, 3x3 by hand,
identity, zero), non-commutativity, exact integers, NumPy comparison, **bit identity with the
Assignment 1 Python kernel** and its `fsum` checksum, sparse inputs (0 %, 100 % and random), nnz
counts, the CSR memory model, batching and input errors; and for the data: regeneration of the
Assignment 1 files with the same SHA-256, the sparse generator (determinism, real density, range,
manifest, corruption).

**During the campaign**, as in Assignment 1: on repetition 1 of each (configuration, case) the
worker dumps `C` and a separate process compares it with NumPy's `A @ B` (`rtol = 1e-9`,
`atol = 1e-12`); the SHA-256 of the dump must be the same for all methods. Later repetitions must
give the same checksum. Any failure aborts the campaign.

## 7. Memory

- **`proc_peak_wset_bytes`** (same metric as Assignment 1): peak working set of the whole process,
  read by the runner with `GetProcessMemoryInfo`. For `csr` it **includes reading the dense input
  files**, so it does not show the CSR saving by itself.
- **`wset_after_bytes`** (new): current working set right after the timed region. In `csr` the dense
  inputs have already been freed, so it reflects the CSR structures plus the runtime.
- **`object_model_bytes`**: exact bytes of the data structures of the method: dense `3 x 8 x n²`;
  CSR `12 x nnz + 8 x (n + 1)` per matrix (A, B and C).

## 8. Sizes and budgets (declared before measuring)

- Part A sizes: `10 25 50 100 200 300 400 500 512 600 800 1000 1024 1200 1500 1536 2000 2048 2500 3000 4000`
  (the Assignment 1 sizes plus the powers of two where Assignment 1 found slowdowns and larger
  sizes to look for the limits).
- Part B: n = 1000 and 2000 with all densities; n = 4000 with 0.1 % and 1 % (csr and blocked only;
  the `ijk` baseline at n = 4000 is measured in Part A). Densities 60, 70, 85 and 100 % were added
  afterwards as a separate experiment (`05_B_extra_densidades_altas`) because CSR still won at 50 %.
- **300 s** wall-clock per process and **4096 MB** per process (as in Assignment 1). A timeout,
  OOM or error is recorded as a **result** (no invented time) and that configuration does not try
  larger cases.
- The dense data at n >= 2500 and the sparse files at n = 4000 are large (128 MB per matrix at
  n = 4000); they are not versioned and are regenerated deterministically.

## 9. CSV schema (`raw.csv`)

One row per run (process). Same columns as Assignment 1 (without the Java ones) plus:

| Column | Meaning |
|---|---|
| `config`, `method`, `block` | Configuration name (`ijk`, `ikj`, `blocked`, `csr`, `blocked-<bs>`), kernel and block size |
| `input_set`, `density_pct` | `dense` (data/) or `sparse` (data_sparse/) and the declared density in % |
| `convert_ns` | csr only: time to convert A and B from dense to CSR (outside `time_ns`) |
| `nnz_a`, `nnz_b`, `nnz_c` | Nonzeros of the inputs and of the result |
| `wset_after_bytes` | Working set right after the multiplication (Section 7) |
| `object_model_bytes` | Bytes of the data structures of the method (Section 7) |

The other columns (`time_ns`, `batch`, `status`, `proc_peak_wset_bytes`, `checksum`, `verified`,
`c_sha256`, `max_rel_err`, ...) have the same meaning as in Assignment 1.

## 10. Results

See [`results/LEEME.md`](results/LEEME.md) (Spanish) and the report. In short:

- **Part A:** all methods give the same bits. `ikj` removes the Assignment 1 slowdowns at powers of two
  (slope 3.05 instead of 3.74); `blocked` is the fastest dense method (~0.33 ns per inner iteration up
  to n = 4000; 5.7x the baseline at n = 2000, 15x at n = 3000). The baseline times out at n = 4000.
- **Alignment control:** part of the `blocked` vs `ikj` gap at small n is code placement; tiling itself
  gives ~1.45x for n >= 1000.
- **Part B:** CSR beats `blocked` up to 50 % density (from ~10 000x at 0.1 % to 1.13x at 50 %); the
  crossover is at ~53 % for n = 1000 and 2000. The conversion (up to 100x the product at 0.1 %) and the
  output fill-in (C almost dense from 5 %) reduce the advantage.

## 11. Known limitations

- One machine (AMD Ryzen 7 4800H laptop, Windows 11, plugged in); conclusions are limited to these
  implementations, settings, inputs and hardware.
- Only uniformly random sparsity patterns were tested; real sparse matrices (banded, power-law
  rows...) can behave differently.
- The sparse inputs are stored in the dense format so that all methods read the same files; this
  makes the peak memory of `csr` include the dense inputs (hence `wset_after_bytes`).
- No hardware counters: cache explanations are inferred from times and data sizes.

## 12. Use of generative AI

A generative AI assistant (Claude Code, Anthropic) was used to help with the code, the analysis
scripts and the writing of the report; see the disclosure in the report. The author is
responsible for the work.
