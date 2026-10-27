"""Referencias en Python puro para los tests (no se miden).

``matmul_ijk`` y ``checksum_fsum`` son las funciones del kernel de Python de la Práctica 1
(``practica1/src/python/matmul.py``), copiadas sin cambios. Como hacen las sumas en el mismo
orden que los kernels de C y sin FMA, sirven para comprobar que el resultado de C es
idéntico BIT A BIT.

``count_nonzeros`` y ``csr_model_bytes`` reproducen lo que el worker de C informa sobre los
no-ceros y la memoria de las estructuras CSR.
"""

from __future__ import annotations

import math


def matmul_ijk(A: list[list[float]], B: list[list[float]], n: int) -> list[list[float]]:
    """C = A x B (matrices n x n), triple bucle i-j-k, ``C`` inicializada con 0.0."""
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C


def checksum_fsum(C: list[list[float]]) -> float:
    """Suma correctamente redondeada de todos los elementos (math.fsum)."""
    return math.fsum(x for row in C for x in row)


def count_nonzeros(M: list[list[float]]) -> int:
    return sum(1 for row in M for x in row if x != 0.0)


def csr_model_bytes(nnz: int, n: int) -> int:
    """Bytes de una matriz CSR: 8 (valor) + 4 (columna) por no-cero + 8 (n + 1) de row_ptr."""
    return 12 * nnz + 8 * (n + 1)
