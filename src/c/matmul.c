/*
 * Kernels de la Práctica 2 (C) y *worker* que hace UNA medición.
 *
 * Es el worker de C de la Práctica 1 (mismo protocolo, misma E/S, mismo temporizador,
 * mismo checksum y misma salida JSON) ampliado con --method para elegir el kernel:
 *
 *   ijk      BASELINE: el kernel de la Práctica 1 sin ningún cambio.
 *                for i: for j: for k: C[i][j] += A[i][k] * B[k][j]
 *   ikj      Reordenación de bucles. B y C se recorren por FILAS (posiciones contiguas)
 *            en lugar de recorrer B por columnas (saltos de 8n bytes).
 *                for i: for k: a = A[i][k]; for j: C[i][j] += a * B[k][j]
 *   blocked  ikj por bloques (cache blocking / tiling) de --block x --block: trabaja con
 *            trozos de A, B y C que caben en la caché antes de pasar al siguiente.
 *   csr      Matrices dispersas: A y B en formato CSR (Compressed Sparse Row) y producto
 *            CSR x CSR con el algoritmo de Gustavson (fila a fila, acumulador denso).
 *            Resultado también en CSR, con las columnas de cada fila ordenadas.
 *
 * Los cuatro kernels hacen, para cada C[i][j], las sumas en el MISMO orden (k creciente,
 * partiendo de 0.0) y sin FMA (-ffp-contract=off), así que el resultado es idéntico bit a
 * bit al de la Práctica 1. En csr se omiten los productos con un factor cero: sumar +0.0
 * no cambia un double, así que tampoco cambia el resultado.
 *
 * Sin BLAS ni ninguna multiplicación de librería: todo el código de los kernels es propio.
 * Estructura densa: UN bloque contiguo de n·n doubles por matriz, orden por filas
 * (row-major), accedido como matriz 2-D con un puntero a array de longitud variable (C99).
 *
 * Qué cronometra el worker (medición del *kernel*), igual que en la Práctica 1:
 *   DENTRO: la llamada al kernel (reserva C y la inicializa / construye el CSR de C).
 *   FUERA:  lectura de ficheros, conversión denso -> CSR de A y B (se mide APARTE, en
 *           convert_ns), calentamiento, calibración, checksum, volcado de C.
 *   Temporizador monótono: QueryPerformanceCounter (Windows) o
 *   clock_gettime(CLOCK_MONOTONIC) (POSIX).
 *
 * Calentamiento: --warmup-runs ejecuciones del kernel sobre una submatriz de
 * --warmup-n x --warmup-n (o de n si es menor). Nunca forman parte de la muestra.
 *
 * Tareas muy cortas: si el coste estimado de una multiplicación es menor que
 * --batch-target-ms se hace una ejecución de calibración (se descarta y cuenta como
 * un calentamiento más) y se mide un LOTE dentro de una sola región cronometrada.
 * time_ns es siempre el tiempo POR multiplicación (time_total_ns / batch). En csr el coste
 * no es cúbico (depende de los no-ceros), así que la calibración se hace siempre.
 *
 * Memoria: pico del working set del proceso (PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize,
 * el mismo contador que psutil llama peak_wset) en Windows; VmHWM en Linux; ru_maxrss
 * en otros Unix. Se lee justo después de multiplicar. Además wset_after_bytes es el
 * working set ACTUAL en ese momento: en csr las matrices densas de entrada ya se han
 * liberado, así que refleja la memoria de las estructuras CSR (el pico no, porque incluye
 * la lectura de los ficheros densos).
 *
 * Checksum: suma correctamente redondeada de todos los elementos de C (algoritmo de
 * Shewchuk, el mismo que math.fsum de CPython). Es exacta, así que no depende del orden
 * ni de los ceros: coincide entre kernels si C coincide.
 *
 * Salida: la última línea de stdout es un objeto JSON. Códigos de salida:
 * 0 = OK, 2 = error de entrada/salida o de argumentos, 3 = memoria insuficiente.
 *
 * Compilación (la hace scripts/build.py):
 *   gcc -std=c11 -O2 -ffp-contract=off -o build/c/matmul.exe src/c/matmul.c -lpsapi
 *
 * Uso:
 *   build/c/matmul.exe --method blocked --block 64 --n 200 --a data/A_200.bin --b data/B_200.bin
 */

#if !defined(_WIN32) && !defined(_POSIX_C_SOURCE)
#define _POSIX_C_SOURCE 200809L
#endif

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#include <time.h>
#endif

#define LANGUAGE "c"
#define DTYPE "float64"

enum { M_IJK, M_IKJ, M_BLOCKED, M_CSR, M_COUNT };
static const char *METHOD_ARG[M_COUNT] = {"ijk", "ikj", "blocked", "csr"};
static const char *METHOD_NAME[M_COUNT] = {"triple_loop_ijk", "loop_order_ikj", "blocked_ikj",
                                           "csr_gustavson"};

#ifndef BUILD_FLAGS
#define BUILD_FLAGS "desconocidos"
#endif

#define EXIT_IO 2
#define EXIT_OOM 3

/* ------------------------------------------------------------------------- */
/* Temporizador monótono y memoria                                           */
/* ------------------------------------------------------------------------- */
static int64_t now_ns(void) {
#ifdef _WIN32
    static LARGE_INTEGER freq;
    LARGE_INTEGER t;
    if (freq.QuadPart == 0) QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&t);
    int64_t q = t.QuadPart, f = freq.QuadPart;
    return (q / f) * 1000000000LL + (q % f) * 1000000000LL / f;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + ts.tv_nsec;
#endif
}

/* Pico de memoria residente del proceso, en bytes; *metric recibe el nombre de la fuente. */
static int64_t peak_rss_bytes(const char **metric) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof pmc)) {
        *metric = "peak_wset";
        return (int64_t)pmc.PeakWorkingSetSize;
    }
#else
    FILE *fh = fopen("/proc/self/status", "r");
    if (fh) {
        char line[256];
        long long kb = -1;
        while (fgets(line, sizeof line, fh)) {
            if (strncmp(line, "VmHWM:", 6) == 0) {
                kb = atoll(line + 6);
                break;
            }
        }
        fclose(fh);
        if (kb >= 0) {
            *metric = "VmHWM";
            return (int64_t)kb * 1024;
        }
    }
    struct rusage ru;
    if (getrusage(RUSAGE_SELF, &ru) == 0) {
        *metric = "ru_maxrss";
#ifdef __APPLE__
        return (int64_t)ru.ru_maxrss;
#else
        return (int64_t)ru.ru_maxrss * 1024;
#endif
    }
#endif
    *metric = "unavailable";
    return -1;
}

/* Working set ACTUAL del proceso, en bytes (Windows: WorkingSetSize; Linux: VmRSS). */
static int64_t current_rss_bytes(void) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof pmc)) return (int64_t)pmc.WorkingSetSize;
#else
    FILE *fh = fopen("/proc/self/status", "r");
    if (fh) {
        char line[256];
        long long kb = -1;
        while (fgets(line, sizeof line, fh)) {
            if (strncmp(line, "VmRSS:", 6) == 0) {
                kb = atoll(line + 6);
                break;
            }
        }
        fclose(fh);
        if (kb >= 0) return (int64_t)kb * 1024;
    }
#endif
    return -1;
}

/* ------------------------------------------------------------------------- */
/* Kernels densos                                                             */
/* ------------------------------------------------------------------------- */
/* C = A x B (n x n), triple bucle i-j-k. Reserva C y la inicializa a 0.0.
 * noinline: el kernel queda como una función real (como en Python y Java) y el
 * compilador no puede fusionarlo con el código que lo rodea. */
__attribute__((noinline)) static double *matmul_ijk(const double *a_, const double *b_, int n) {
    double *c_ = malloc(sizeof(double) * (size_t)n * (size_t)n);
    if (c_ == NULL) return NULL;
    const double (*A)[n] = (const double (*)[n])a_;
    const double (*B)[n] = (const double (*)[n])b_;
    double (*C)[n] = (double (*)[n])c_;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = 0.0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
                C[i][j] += A[i][k] * B[k][j];
    return c_;
}

/* Optimización 1: reordenación de bucles i-k-j. Mismas n³ multiplicaciones y sumas que
 * ijk, pero el bucle interno recorre una FILA de B y una FILA de C (posiciones contiguas):
 * cada línea de caché de 64 B traída de memoria aporta 8 doubles útiles, mientras que en
 * ijk cada B[k][j] está en una línea distinta. A[i][k] es constante en el bucle interno. */
__attribute__((noinline)) static double *matmul_ikj(const double *a_, const double *b_, int n) {
    double *c_ = malloc(sizeof(double) * (size_t)n * (size_t)n);
    if (c_ == NULL) return NULL;
    const double (*A)[n] = (const double (*)[n])a_;
    const double (*B)[n] = (const double (*)[n])b_;
    double (*C)[n] = (double (*)[n])c_;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = 0.0;
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            const double a = A[i][k];
            for (int j = 0; j < n; j++)
                C[i][j] += a * B[k][j];
        }
    return c_;
}

/* Optimización 2: ikj por bloques (tiling) de bs x bs. Para cada bloque de filas de C
 * (ii) y cada bloque de k (kk) se recorre B por bloques de columnas (jj): el bloque
 * bs x bs de B y el trozo de fila de C se reutilizan mientras siguen en la caché, en vez
 * de recorrer B entera (8n² bytes) para cada fila i. Los bloques de los bordes pueden ser
 * más pequeños (n no tiene por qué ser múltiplo de bs). Para un C[i][j] fijo, k recorre
 * kk = 0, bs, 2bs... y dentro de cada bloque k crece: mismo orden de sumas que ijk. */
__attribute__((noinline)) static double *matmul_blocked(const double *a_, const double *b_, int n,
                                                        int bs) {
    double *c_ = malloc(sizeof(double) * (size_t)n * (size_t)n);
    if (c_ == NULL) return NULL;
    const double (*A)[n] = (const double (*)[n])a_;
    const double (*B)[n] = (const double (*)[n])b_;
    double (*C)[n] = (double (*)[n])c_;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++)
            C[i][j] = 0.0;
    for (int ii = 0; ii < n; ii += bs) {
        const int iend = ii + bs < n ? ii + bs : n;
        for (int kk = 0; kk < n; kk += bs) {
            const int kend = kk + bs < n ? kk + bs : n;
            for (int jj = 0; jj < n; jj += bs) {
                const int jend = jj + bs < n ? jj + bs : n;
                for (int i = ii; i < iend; i++)
                    for (int k = kk; k < kend; k++) {
                        const double a = A[i][k];
                        for (int j = jj; j < jend; j++)
                            C[i][j] += a * B[k][j];
                    }
            }
        }
    }
    return c_;
}

/* ------------------------------------------------------------------------- */
/* Matrices dispersas: formato CSR y producto de Gustavson                    */
/* ------------------------------------------------------------------------- */
/* CSR (Compressed Sparse Row): los no-ceros de la fila i son val[row_ptr[i] .. row_ptr[i+1]-1]
 * y sus columnas col[...], en orden creciente. Memoria: 12 B por no-cero (8 del valor +
 * 4 del índice de columna) + 8 (n+1) B de row_ptr. */
typedef struct {
    int n;
    int64_t nnz;
    int64_t *row_ptr; /* n + 1 */
    int32_t *col;     /* nnz */
    double *val;      /* nnz */
} csr_t;

static void csr_free(csr_t *m) {
    if (!m) return;
    free(m->row_ptr);
    free(m->col);
    free(m->val);
    free(m);
}

static int64_t csr_bytes(const csr_t *m) {
    return m->nnz * (int64_t)(sizeof(double) + sizeof(int32_t)) +
           (int64_t)(m->n + 1) * (int64_t)sizeof(int64_t);
}

/* Conversión denso (row-major) -> CSR en dos pasadas: contar no-ceros y rellenar. */
static csr_t *csr_from_dense(const double *d, int n) {
    int64_t nnz = 0;
    size_t count = (size_t)n * (size_t)n;
    for (size_t idx = 0; idx < count; idx++)
        if (d[idx] != 0.0) nnz++;
    csr_t *m = calloc(1, sizeof *m);
    if (!m) return NULL;
    m->n = n;
    m->nnz = nnz;
    m->row_ptr = malloc(sizeof(int64_t) * (size_t)(n + 1));
    m->col = malloc(sizeof(int32_t) * (size_t)(nnz > 0 ? nnz : 1));
    m->val = malloc(sizeof(double) * (size_t)(nnz > 0 ? nnz : 1));
    if (!m->row_ptr || !m->col || !m->val) {
        csr_free(m);
        return NULL;
    }
    int64_t p = 0;
    m->row_ptr[0] = 0;
    for (int i = 0; i < n; i++) {
        const double *row = d + (size_t)i * n;
        for (int j = 0; j < n; j++)
            if (row[j] != 0.0) {
                m->col[p] = j;
                m->val[p] = row[j];
                p++;
            }
        m->row_ptr[i + 1] = p;
    }
    return m;
}

/* CSR -> denso (solo para el volcado y la verificación, fuera del cronómetro). */
static double *csr_to_dense(const csr_t *m) {
    int n = m->n;
    double *d = calloc((size_t)n * (size_t)n, sizeof(double));
    if (!d) return NULL;
    for (int i = 0; i < n; i++)
        for (int64_t p = m->row_ptr[i]; p < m->row_ptr[i + 1]; p++) d[(size_t)i * n + m->col[p]] = m->val[p];
    return d;
}

static int cmp_int32(const void *x, const void *y) {
    int32_t a = *(const int32_t *)x, b = *(const int32_t *)y;
    return (a > b) - (a < b);
}

/* C = A x B con A y B en CSR, algoritmo de Gustavson: la fila i de C es la combinación
 * de las filas k de B, con k en los no-ceros de la fila i de A (en orden creciente):
 *
 *     para cada no-cero A[i][k]:  para cada no-cero B[k][j]:  acc[j] += A[i][k] * B[k][j]
 *
 * acc es un acumulador denso de n doubles; mark[j] == i indica que la columna j ya
 * apareció en la fila i (entonces acc[j] es válido) y touched guarda esas columnas. Al
 * terminar la fila se ordenan las columnas (qsort si son pocas; si son muchas, más de
 * n/8, es más barato recorrer mark entero) y se copian a C. Trabajo: proporcional al
 * número de productos útiles (≈ n³·d² para densidad d uniforme) más O(n) por fila.
 * C crece duplicando su capacidad (no se conoce su nnz de antemano). */
__attribute__((noinline)) static csr_t *matmul_csr(const csr_t *A, const csr_t *B) {
    const int n = A->n;
    csr_t *C = calloc(1, sizeof *C);
    double *acc = malloc(sizeof(double) * (size_t)n);
    int32_t *mark = malloc(sizeof(int32_t) * (size_t)n);
    int32_t *touched = malloc(sizeof(int32_t) * (size_t)n);
    int64_t cap = A->nnz + B->nnz > n ? A->nnz + B->nnz : n;
    if (C) {
        C->n = n;
        C->row_ptr = malloc(sizeof(int64_t) * (size_t)(n + 1));
        C->col = malloc(sizeof(int32_t) * (size_t)cap);
        C->val = malloc(sizeof(double) * (size_t)cap);
    }
    if (!C || !acc || !mark || !touched || !C->row_ptr || !C->col || !C->val) goto oom;
    for (int j = 0; j < n; j++) mark[j] = -1;

    int64_t nnz = 0;
    C->row_ptr[0] = 0;
    for (int i = 0; i < n; i++) {
        int cnt = 0;
        for (int64_t p = A->row_ptr[i]; p < A->row_ptr[i + 1]; p++) {
            const int k = A->col[p];
            const double a = A->val[p];
            for (int64_t q = B->row_ptr[k]; q < B->row_ptr[k + 1]; q++) {
                const int j = B->col[q];
                if (mark[j] != i) { /* primera aparición de la columna j en esta fila */
                    mark[j] = i;
                    acc[j] = 0.0; /* C[i][j] parte de 0.0, como en los kernels densos */
                    touched[cnt++] = j;
                }
                acc[j] += a * B->val[q];
            }
        }
        if (nnz + cnt > cap) {
            while (nnz + cnt > cap) cap *= 2;
            int32_t *nc = realloc(C->col, sizeof(int32_t) * (size_t)cap);
            if (nc) C->col = nc;
            double *nv = realloc(C->val, sizeof(double) * (size_t)cap);
            if (nv) C->val = nv;
            if (!nc || !nv) goto oom;
        }
        if (cnt > n / 8) {
            for (int j = 0; j < n; j++)
                if (mark[j] == i) {
                    C->col[nnz] = j;
                    C->val[nnz] = acc[j];
                    nnz++;
                }
        } else {
            qsort(touched, (size_t)cnt, sizeof(int32_t), cmp_int32);
            for (int t = 0; t < cnt; t++) {
                C->col[nnz] = touched[t];
                C->val[nnz] = acc[touched[t]];
                nnz++;
            }
        }
        C->row_ptr[i + 1] = nnz;
    }
    C->nnz = nnz;
    free(acc);
    free(mark);
    free(touched);
    return C;
oom:
    free(acc);
    free(mark);
    free(touched);
    csr_free(C);
    return NULL;
}

/* Suma correctamente redondeada (Shewchuk), traducción de math.fsum de CPython
 * para valores finitos. */
static double checksum_fsum(const double *x, size_t len) {
    double p[128];
    int np = 0;
    for (size_t idx = 0; idx < len; idx++) {
        double v = x[idx];
        int i = 0;
        for (int j = 0; j < np; j++) {
            double y = p[j];
            if (fabs(v) < fabs(y)) {
                double t = v;
                v = y;
                y = t;
            }
            double hi = v + y;
            double lo = y - (hi - v);
            if (lo != 0.0) p[i++] = lo;
            v = hi;
        }
        np = i;
        if (v != 0.0) {
            if (np >= (int)(sizeof p / sizeof p[0])) return NAN; /* imposible con doubles finitos */
            p[np++] = v;
        }
    }
    double hi = 0.0, lo = 0.0;
    if (np > 0) {
        hi = p[--np];
        while (np > 0) {
            double v = hi, y = p[--np];
            hi = v + y;
            lo = y - (hi - v);
            if (lo != 0.0) break;
        }
        if (np > 0 && ((lo < 0.0 && p[np - 1] < 0.0) || (lo > 0.0 && p[np - 1] > 0.0))) {
            double y = lo * 2.0;
            double v = hi + y;
            if (y == v - hi) hi = v;
        }
    }
    return hi;
}

/* ------------------------------------------------------------------------- */
/* E/S en el formato compartido (float64 little-endian, row-major, sin cabecera) */
/* ------------------------------------------------------------------------- */
static int host_is_little_endian(void) {
    const uint16_t one = 1;
    return *(const uint8_t *)&one == 1;
}

static void byteswap_all(double *v, size_t count) {
    for (size_t i = 0; i < count; i++) {
        uint8_t *b = (uint8_t *)&v[i];
        for (int k = 0; k < 4; k++) {
            uint8_t t = b[k];
            b[k] = b[7 - k];
            b[7 - k] = t;
        }
    }
}

/* Devuelve 0 si va bien; en caso de error escribe el motivo en err. */
static int read_matrix(const char *path, int n, double **out, char *err, size_t errlen) {
    size_t count = (size_t)n * (size_t)n;
    FILE *fh = fopen(path, "rb");
    if (!fh) {
        snprintf(err, errlen, "no se puede abrir %s", path);
        return EXIT_IO;
    }
#ifdef _WIN32
    _fseeki64(fh, 0, SEEK_END);
    long long size = (long long)_ftelli64(fh);
    _fseeki64(fh, 0, SEEK_SET);
#else
    fseek(fh, 0, SEEK_END);
    long long size = (long long)ftell(fh);
    fseek(fh, 0, SEEK_SET);
#endif
    if (size != (long long)(8 * count)) {
        snprintf(err, errlen, "%s tiene %lld bytes; para n=%d se esperaban %lld", path, size, n,
                 (long long)(8 * count));
        fclose(fh);
        return EXIT_IO;
    }
    double *m = malloc(sizeof(double) * count);
    if (!m) {
        fclose(fh);
        snprintf(err, errlen, "sin memoria al leer %s", path);
        return EXIT_OOM;
    }
    size_t got = fread(m, sizeof(double), count, fh);
    fclose(fh);
    if (got != count) {
        free(m);
        snprintf(err, errlen, "lectura incompleta de %s", path);
        return EXIT_IO;
    }
    if (!host_is_little_endian()) byteswap_all(m, count);
    *out = m;
    return 0;
}

static int write_matrix(const char *path, const double *m, int n) {
    size_t count = (size_t)n * (size_t)n;
    FILE *fh = fopen(path, "wb");
    if (!fh) return EXIT_IO;
    size_t put;
    if (host_is_little_endian()) {
        put = fwrite(m, sizeof(double), count, fh);
    } else { /* fila a fila, para no duplicar la matriz en memoria */
        put = 0;
        double *row = malloc(sizeof(double) * (size_t)n);
        if (!row) {
            fclose(fh);
            return EXIT_OOM;
        }
        for (int i = 0; i < n; i++) {
            memcpy(row, m + (size_t)i * n, sizeof(double) * (size_t)n);
            byteswap_all(row, (size_t)n);
            put += fwrite(row, sizeof(double), (size_t)n, fh);
        }
        free(row);
    }
    int bad = fclose(fh) != 0 || put != count;
    return bad ? EXIT_IO : 0;
}

/* ------------------------------------------------------------------------- */
/* Worker                                                                     */
/* ------------------------------------------------------------------------- */
static volatile double sink; /* consume un elemento de cada resultado del lote */

/* Un problema concreto: kernel elegido + entradas (densas o CSR, según el kernel). */
typedef struct {
    int method, n, block;
    const double *A, *B;   /* kernels densos */
    const csr_t *As, *Bs;  /* csr */
} problem_t;

/* Ejecuta el kernel. Devuelve double* (densos) o csr_t* (csr); NULL si no hay memoria. */
static void *run_kernel(const problem_t *p) {
    switch (p->method) {
    case M_IJK: return matmul_ijk(p->A, p->B, p->n);
    case M_IKJ: return matmul_ikj(p->A, p->B, p->n);
    case M_BLOCKED: return matmul_blocked(p->A, p->B, p->n, p->block);
    default: return matmul_csr(p->As, p->Bs);
    }
}

static void free_result(const problem_t *p, void *r) {
    if (p->method == M_CSR) csr_free((csr_t *)r);
    else free(r);
}

static double probe(const problem_t *p, const void *r) {
    if (p->method == M_CSR) {
        const csr_t *c = r;
        return c->nnz > 0 ? c->val[0] : 0.0;
    }
    return ((const double *)r)[0];
}

static int64_t count_nonzeros(const double *d, int n) {
    int64_t nnz = 0;
    size_t count = (size_t)n * (size_t)n;
    for (size_t idx = 0; idx < count; idx++)
        if (d[idx] != 0.0) nnz++;
    return nnz;
}

static int emit_error(const char *status, int n, const char *note, int code) {
    fprintf(stderr, "%s: %s\n", status, note);
    printf("{\"status\": \"%s\", \"n\": %d, \"note\": \"", status, n);
    for (const char *ch = note; *ch; ch++) { /* escapa \ y " (rutas de Windows) */
        if (*ch == '\\' || *ch == '"') putchar('\\');
        putchar(*ch);
    }
    printf("\"}\n");
    fflush(stdout);
    return code;
}

/* Copia la esquina m x m superior izquierda de una matriz n x n. */
static double *corner(const double *src, int n, int m) {
    double *dst = malloc(sizeof(double) * (size_t)m * (size_t)m);
    if (!dst) return NULL;
    for (int i = 0; i < m; i++) memcpy(dst + (size_t)i * m, src + (size_t)i * n, sizeof(double) * (size_t)m);
    return dst;
}

/* Región cronometrada: batch multiplicaciones. Devuelve C (la última) y el tiempo total. */
static void *timed(const problem_t *p, long batch, int64_t *elapsed) {
    void *C = NULL;
    int64_t t0 = now_ns();
    for (long r = 0; r < batch; r++) {
        void *next = run_kernel(p);
        if (next == NULL) {
            if (C) free_result(p, C);
            return NULL;
        }
        sink = probe(p, next);
        if (C) free_result(p, C);
        C = next;
    }
    *elapsed = now_ns() - t0;
    return C;
}

/* Calentamiento sobre la esquina m x m (en csr, convertida también a CSR). */
static int warm_up(const problem_t *full, const double *A, const double *B, int m, int runs,
                   int64_t *elapsed) {
    double *wa = corner(A, full->n, m), *wb = corner(B, full->n, m);
    csr_t *was = NULL, *wbs = NULL;
    if (!wa || !wb) goto oom;
    problem_t w = {full->method, m, full->block, wa, wb, NULL, NULL};
    if (full->method == M_CSR) {
        was = csr_from_dense(wa, m);
        wbs = csr_from_dense(wb, m);
        if (!was || !wbs) goto oom;
        w.As = was;
        w.Bs = wbs;
    }
    int64_t t0 = now_ns();
    for (int r = 0; r < runs; r++) {
        void *res = run_kernel(&w);
        if (!res) goto oom;
        sink = probe(&w, res);
        free_result(&w, res);
    }
    *elapsed = now_ns() - t0;
    free(wa);
    free(wb);
    csr_free(was);
    csr_free(wbs);
    return 0;
oom:
    free(wa);
    free(wb);
    csr_free(was);
    csr_free(wbs);
    return EXIT_OOM;
}

static void usage(void) {
    fprintf(stderr,
            "uso: matmul --n N --a A.bin --b B.bin [--method ijk|ikj|blocked|csr] [--block BS]\n"
            "            [--dump-c C.bin] [--warmup-runs R] [--warmup-n M] [--batch-target-ms MS]\n");
}

int main(int argc, char **argv) {
    int n = 0, warmup_runs_arg = 1, warmup_n = 64, method = M_IJK, block = 64;
    double batch_target_ms = 100.0;
    const char *a_path = NULL, *b_path = NULL, *dump_path = NULL;

    for (int i = 1; i < argc; i++) {
        const char *opt = argv[i];
        if (i + 1 >= argc) {
            usage();
            return EXIT_IO;
        }
        const char *val = argv[++i];
        if (strcmp(opt, "--n") == 0) n = atoi(val);
        else if (strcmp(opt, "--a") == 0) a_path = val;
        else if (strcmp(opt, "--b") == 0) b_path = val;
        else if (strcmp(opt, "--dump-c") == 0) dump_path = val;
        else if (strcmp(opt, "--warmup-runs") == 0) warmup_runs_arg = atoi(val);
        else if (strcmp(opt, "--warmup-n") == 0) warmup_n = atoi(val);
        else if (strcmp(opt, "--batch-target-ms") == 0) batch_target_ms = atof(val);
        else if (strcmp(opt, "--block") == 0) block = atoi(val);
        else if (strcmp(opt, "--method") == 0) {
            method = -1;
            for (int m = 0; m < M_COUNT; m++)
                if (strcmp(val, METHOD_ARG[m]) == 0) method = m;
            if (method < 0) {
                usage();
                return EXIT_IO;
            }
        } else {
            usage();
            return EXIT_IO;
        }
    }
    if (n < 1 || !a_path || !b_path || block < 1) {
        usage();
        return EXIT_IO;
    }

    const char *metric = "unavailable";
    int64_t baseline = peak_rss_bytes(&metric); /* proceso antes de cargar datos */

    char err[512];
    double *A = NULL, *B = NULL;
    int rc = read_matrix(a_path, n, &A, err, sizeof err);
    if (rc == 0) rc = read_matrix(b_path, n, &B, err, sizeof err);
    if (rc != 0) return emit_error(rc == EXIT_OOM ? "OOM" : "error", n, err, rc);

    /* No-ceros de las entradas (fuera del cronómetro; para todos los métodos). */
    int64_t nnz_a = count_nonzeros(A, n), nnz_b = count_nonzeros(B, n);
    problem_t prob = {method, n, block, A, B, NULL, NULL};

    /* csr: conversión denso -> CSR de A y B, cronometrada APARTE (una vez, sin lote). */
    int64_t convert_ns = -1;
    csr_t *As = NULL, *Bs = NULL;
    if (method == M_CSR) {
        int64_t t0 = now_ns();
        As = csr_from_dense(A, n);
        Bs = csr_from_dense(B, n);
        convert_ns = now_ns() - t0;
        if (!As || !Bs) return emit_error("OOM", n, "sin memoria al convertir a CSR", EXIT_OOM);
        prob.As = As;
        prob.Bs = Bs;
    }

    /* Calentamiento y, si la tarea es muy corta, calibración del lote. */
    long warmup_runs = 0, batch = 1;
    int warmup_size = 0;
    int64_t warm_ns = 0;
    if (warmup_runs_arg > 0) {
        int m = n < warmup_n ? n : warmup_n;
        if (m < 1) m = 1;
        if (warm_up(&prob, A, B, m, warmup_runs_arg, &warm_ns) != 0)
            return emit_error("OOM", n, "sin memoria en el calentamiento", EXIT_OOM);
        warmup_runs = warmup_runs_arg;
        warmup_size = m;
    }
    if (method == M_CSR) { /* las densas ya no hacen falta: el working set queda con el CSR */
        free(A);
        free(B);
        A = B = NULL;
        prob.A = prob.B = NULL;
    }
    if (batch_target_ms > 0) {
        int calibrate = 1;
        if (warmup_runs_arg > 0 && method != M_CSR) { /* densos: estimación cúbica */
            double ratio = (double)n / warmup_size;
            double est_ns = (double)warm_ns / warmup_runs_arg * ratio * ratio * ratio;
            calibrate = est_ns < batch_target_ms * 1e6;
        }
        if (calibrate) {
            int64_t cal_ns;
            void *cal = timed(&prob, 1, &cal_ns); /* calibración: se descarta */
            if (!cal) return emit_error("OOM", n, "MemoryError", EXIT_OOM);
            free_result(&prob, cal);
            warmup_runs += 1;
            if (cal_ns < batch_target_ms * 1e6) {
                double b = ceil(batch_target_ms * 1e6 / (double)(cal_ns > 0 ? cal_ns : 1));
                batch = b < 1 ? 1 : (long)b;
            }
        }
    }

    int64_t total_ns = 0;
    void *R = timed(&prob, batch, &total_ns);
    if (!R) return emit_error("OOM", n, "MemoryError", EXIT_OOM);
    int64_t peak = peak_rss_bytes(&metric); /* justo después de multiplicar */
    int64_t wset_after = current_rss_bytes();

    /* Resultado en denso (para checksum, nnz y volcado), fuera del cronómetro. */
    size_t count = (size_t)n * (size_t)n;
    double *Cd;
    int64_t nnz_c, struct_model;
    if (method == M_CSR) {
        csr_t *Cs = R;
        nnz_c = Cs->nnz; /* no-ceros estructurales (con datos >= 0 no hay cancelaciones) */
        struct_model = csr_bytes(As) + csr_bytes(Bs) + csr_bytes(Cs);
        Cd = csr_to_dense(Cs);
        if (!Cd) return emit_error("OOM", n, "sin memoria al volcar C", EXIT_OOM);
        csr_free(Cs);
    } else {
        Cd = R;
        nnz_c = count_nonzeros(Cd, n);
        struct_model = 3LL * 8LL * (long long)count;
    }
    double checksum = checksum_fsum(Cd, count);
    if (dump_path && write_matrix(dump_path, Cd, n) != 0)
        return emit_error("error", n, "no se pudo escribir el volcado de C", EXIT_IO);

    long long model = 3LL * 8LL * (long long)count;
    printf("{\"status\": \"OK\", \"language\": \"%s\", \"method\": \"%s\", \"method_arg\": \"%s\", "
           "\"block\": %d, \"n\": %d, \"dtype\": \"%s\", \"threads\": 1, \"batch\": %ld, "
           "\"time_total_ns\": %lld, \"time_ns\": %.17g, \"convert_ns\": %lld, "
           "\"warmup_runs\": %ld, \"warmup_n\": %d, "
           "\"nnz_a\": %lld, \"nnz_b\": %lld, \"nnz_c\": %lld, "
           "\"peak_rss_bytes\": %lld, \"baseline_rss_bytes\": %lld, \"wset_after_bytes\": %lld, "
           "\"memory_metric\": \"%s\", \"array_model_bytes\": %lld, \"object_model_bytes\": %lld, "
           "\"checksum\": \"%.17g\", \"runtime_version\": \"gcc %d.%d.%d\", \"runtime_flags\": \"%s\"}\n",
           LANGUAGE, METHOD_NAME[method], METHOD_ARG[method], method == M_BLOCKED ? block : 0, n,
           DTYPE, batch, (long long)total_ns, (double)total_ns / (double)batch, (long long)convert_ns,
           warmup_runs, warmup_size, (long long)nnz_a, (long long)nnz_b, (long long)nnz_c,
           (long long)peak, (long long)baseline, (long long)wset_after, metric, model,
           (long long)struct_model, checksum, __GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__,
           BUILD_FLAGS);
    fflush(stdout);
    free(A);
    free(B);
    free(Cd);
    csr_free(As);
    csr_free(Bs);
    return 0;
}
