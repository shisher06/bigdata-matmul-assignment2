"""Tests de corrección del worker de C (los cuatro métodos) y del runner.

Se ejecutan con:  python -m unittest discover -s tests -v
(antes hay que compilar: python scripts/build.py; si no hay binario, se omiten).

Adaptados de los tests de los workers de la Práctica 1: el worker se prueba como caja negra,
igual que se usa en la campaña (se escriben A y B en el formato binario compartido, se lanza
el worker y se lee el volcado de C). Se prueba CADA método: ijk (baseline), ikj, blocked (con
el bloque de la campaña y con un bloque pequeño que no divide a n, para cubrir los bloques de
los bordes) y csr. Cubren: casos con respuesta conocida (identidad, cero, 2x2 y 3x3 a mano),
no conmutatividad, enteros exactos, comparación con NumPy, igualdad BIT A BIT con el kernel de
Python de la Práctica 1, checksum idéntico al de math.fsum, matrices dispersas (0 %, 100 % y
aleatorias), recuento de no-ceros, modelo de memoria CSR, lotes para tareas cortas, errores
de entrada y la medición de memoria del runner.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "python"))
sys.path.insert(0, str(ROOT / "scripts"))

import matrix_io  # noqa: E402
import run_benchmarks  # noqa: E402
from reference import checksum_fsum, count_nonzeros, csr_model_bytes, matmul_ijk  # noqa: E402

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

TABLE = run_benchmarks.config_table()
EXE = TABLE["ijk"]["cmd"][0]
# Configuraciones probadas: las de la campaña + blocked con bloque 5 (no divide a n).
CONFIGS = {
    "ijk": TABLE["ijk"]["cmd"],
    "ikj": TABLE["ikj"]["cmd"],
    "blocked": TABLE["blocked"]["cmd"],
    "blocked-5": [EXE, "--method", "blocked", "--block", "5"],
    "csr": TABLE["csr"]["cmd"],
}
METHOD_NAMES = {"ijk": "triple_loop_ijk", "ikj": "loop_order_ikj", "blocked": "blocked_ikj",
                "blocked-5": "blocked_ikj", "csr": "csr_gustavson"}


def random_matrix(n, seed):
    rnd = random.Random(seed)
    return [[rnd.random() for _ in range(n)] for _ in range(n)]


def sparse_matrix(n, density, seed):
    rnd = random.Random(seed)
    return [[(1.0 - rnd.random()) if rnd.random() < density else 0.0 for _ in range(n)]
            for _ in range(n)]


def identity(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def zeros(n):
    return [[0.0] * n for _ in range(n)]


class WorkerCase(unittest.TestCase):
    """Utilidades comunes: ejecutar un worker con matrices dadas."""

    @classmethod
    def setUpClass(cls):
        if not Path(EXE).exists():
            raise unittest.SkipTest("no hay worker compilado: python scripts/build.py")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.counter = 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_worker(self, name, A, B, *extra, expect_ok=True):
        n = len(A)
        type(self).counter += 1
        tag = f"{name}_{type(self).counter}"
        a, b, c = (self.dir / f"{x}_{tag}.bin" for x in "ABC")
        matrix_io.write_matrix(a, A)
        matrix_io.write_matrix(b, B)
        cmd = [*CONFIGS[name], "--n", str(n), "--a", str(a), "--b", str(b),
               "--dump-c", str(c), *extra]
        if "--batch-target-ms" not in extra:
            cmd += ["--batch-target-ms", "0"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=ROOT)
        if not expect_ok:
            return proc
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        data = json.loads(proc.stdout.strip().splitlines()[-1])
        return data, matrix_io.read_matrix(c, n)


class TestKnownAnswers(WorkerCase):
    def test_1x1(self):
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, [[3.0]], [[4.0]])[1], [[12.0]])

    def test_2x2_by_hand(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        B = [[5.0, 6.0], [7.0, 8.0]]
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, A, B)[1], [[19.0, 22.0], [43.0, 50.0]])

    def test_3x3_by_hand_non_symmetric(self):
        A = [[2.0, 0.0, 1.0], [1.0, 3.0, 2.0], [0.0, 1.0, 4.0]]
        B = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 0.0, 1.0]]
        expected = [[7.0, 4.0, 7.0], [11.0, 5.0, 17.0], [20.0, 1.0, 8.0]]
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, A, B)[1], expected)

    def test_not_commutative(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        P = [[0.0, 1.0], [1.0, 0.0]]
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, A, P)[1], [[2.0, 1.0], [4.0, 3.0]])
                self.assertEqual(self.run_worker(name, P, A)[1], [[3.0, 4.0], [1.0, 2.0]])

    def test_identity_and_zero(self):
        n = 16
        A = random_matrix(n, seed=11)
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, A, identity(n))[1], A)
                self.assertEqual(self.run_worker(name, identity(n), A)[1], A)
                self.assertEqual(self.run_worker(name, A, zeros(n))[1], zeros(n))
                self.assertEqual(self.run_worker(name, zeros(n), A)[1], zeros(n))

    def test_integer_valued_floats_are_exact(self):
        rnd = random.Random(7)
        n = 12
        A = [[float(rnd.randint(-9, 9)) for _ in range(n)] for _ in range(n)]
        B = [[float(rnd.randint(-9, 9)) for _ in range(n)] for _ in range(n)]
        expected = [[float(sum(int(A[i][k]) * int(B[k][j]) for k in range(n))) for j in range(n)]
                    for i in range(n)]
        for name in CONFIGS:
            with self.subTest(config=name):
                self.assertEqual(self.run_worker(name, A, B)[1], expected)


class TestAgainstReferences(WorkerCase):
    @unittest.skipIf(np is None, "NumPy no instalado (solo se usa como referencia)")
    def test_against_numpy(self):
        for n in (7, 33, 64, 100):
            A, B = random_matrix(n, 30 + n), random_matrix(n, 40 + n)
            R = np.array(A) @ np.array(B)
            for name in CONFIGS:
                with self.subTest(config=name, n=n):
                    _, C = self.run_worker(name, A, B)
                    np.testing.assert_allclose(np.array(C), R, rtol=1e-9, atol=1e-12)

    def test_bit_identical_to_p1_python_kernel_and_same_checksum(self):
        """Mismo orden de sumas y sin FMA en todos los métodos: los bits deben coincidir."""
        for n in (40, 67):  # 67: no es múltiplo de ningún tamaño de bloque
            A, B = random_matrix(n, 1 + n), random_matrix(n, 2 + n)
            C_py = matmul_ijk(A, B, n)
            for name in CONFIGS:
                with self.subTest(config=name, n=n):
                    data, C = self.run_worker(name, A, B)
                    self.assertEqual(C, C_py)
                    self.assertEqual(float(data["checksum"]), checksum_fsum(C_py))


class TestSparseInputs(WorkerCase):
    def test_random_sparse_bit_identical_and_nnz(self):
        n = 60
        for density in (0.02, 0.1, 0.3):
            A, B = sparse_matrix(n, density, 5), sparse_matrix(n, density, 6)
            C_py = matmul_ijk(A, B, n)
            for name in CONFIGS:
                with self.subTest(config=name, density=density):
                    data, C = self.run_worker(name, A, B)
                    self.assertEqual(C, C_py)
                    self.assertEqual(data["nnz_a"], count_nonzeros(A))
                    self.assertEqual(data["nnz_b"], count_nonzeros(B))
                    self.assertEqual(data["nnz_c"], count_nonzeros(C_py))

    def test_empty_and_full_density(self):
        n = 20
        full = sparse_matrix(n, 1.0, 8)
        for name in CONFIGS:
            with self.subTest(config=name):
                data, C = self.run_worker(name, zeros(n), zeros(n))
                self.assertEqual(C, zeros(n))
                self.assertEqual((data["nnz_a"], data["nnz_b"], data["nnz_c"]), (0, 0, 0))
                data, C = self.run_worker(name, full, full)
                self.assertEqual(C, matmul_ijk(full, full, n))
                self.assertEqual(data["nnz_c"], n * n)

    def test_csr_memory_model_and_conversion_time(self):
        n = 50
        A, B = sparse_matrix(n, 0.05, 9), sparse_matrix(n, 0.05, 10)
        C_py = matmul_ijk(A, B, n)
        data, _ = self.run_worker("csr", A, B)
        expected = sum(csr_model_bytes(count_nonzeros(M), n) for M in (A, B, C_py))
        self.assertEqual(data["object_model_bytes"], expected)
        self.assertGreaterEqual(data["convert_ns"], 0)
        dense, _ = self.run_worker("ikj", A, B)
        self.assertEqual(dense["convert_ns"], -1)  # los densos no convierten
        self.assertEqual(dense["object_model_bytes"], 3 * 8 * n * n)


class TestWorkerProtocol(WorkerCase):
    def test_output_fields(self):
        n = 24
        A, B = random_matrix(n, 5), random_matrix(n, 6)
        for name in CONFIGS:
            with self.subTest(config=name):
                data, _ = self.run_worker(name, A, B)
                self.assertEqual(data["status"], "OK")
                self.assertEqual(data["language"], "c")
                self.assertEqual(data["method"], METHOD_NAMES[name])
                self.assertEqual(data["dtype"], "float64")
                self.assertEqual(data["threads"], 1)
                self.assertEqual(data["batch"], 1)
                self.assertGreater(data["time_ns"], 0)
                self.assertGreater(data["peak_rss_bytes"], 0)
                self.assertGreater(data["wset_after_bytes"], 0)
                self.assertGreaterEqual(data["peak_rss_bytes"], data["baseline_rss_bytes"])
                self.assertEqual(data["array_model_bytes"], 3 * 8 * n * n)
                self.assertEqual(data["block"], int(CONFIGS[name][-1]) if "blocked" in name else 0)
                self.assertTrue(data["runtime_version"])
                self.assertTrue(data["runtime_flags"])

    def test_tiny_task_is_batched_and_reported_per_multiplication(self):
        A, B = random_matrix(8, 7), random_matrix(8, 8)
        for name in CONFIGS:
            with self.subTest(config=name):
                data, _ = self.run_worker(name, A, B, "--batch-target-ms", "20")
                self.assertGreater(data["batch"], 1)
                self.assertAlmostEqual(data["time_ns"], data["time_total_ns"] / data["batch"],
                                       delta=1e-6 * data["time_ns"])

    def test_bad_inputs_fail_cleanly(self):
        A = random_matrix(4, 9)
        path = self.dir / "A4.bin"
        matrix_io.write_matrix(path, A)
        for name in CONFIGS:
            with self.subTest(config=name):
                missing = [*CONFIGS[name], "--n", "4", "--a", str(self.dir / "nope.bin"),
                           "--b", str(self.dir / "nope.bin")]
                proc = subprocess.run(missing, capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                # tamaño de fichero incoherente con --n
                wrong = [*CONFIGS[name], "--n", "5", "--a", str(path), "--b", str(path)]
                proc = subprocess.run(wrong, capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(json.loads(proc.stdout.strip().splitlines()[-1])["status"], "error")
        for bad in (["--method", "strassen"], ["--method", "blocked", "--block", "0"]):
            with self.subTest(args=bad):
                proc = subprocess.run([EXE, *bad, "--n", "4", "--a", str(path), "--b", str(path)],
                                      capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


@unittest.skipUnless(sys.platform == "win32", "la lectura externa del pico solo existe en Windows")
class TestRunnerMemory(unittest.TestCase):
    def test_child_peak_wset_sees_allocation(self):
        code = "b = bytearray(120 * 1024 * 1024); b[::4096] = b'\\x01' * len(b[::4096])"
        proc = subprocess.Popen([sys.executable, "-c", code])
        proc.wait(timeout=60)
        peak = run_benchmarks.child_peak_wset(proc)
        self.assertIsNotNone(peak)
        self.assertGreater(peak, 120 * 1024 * 1024)


class TestRunnerCases(unittest.TestCase):
    def test_case_order_and_failure_policy(self):
        key = run_benchmarks.case_key
        # dentro de un n, más densidad = caso "mayor"; las densas van al final
        self.assertLess(key(1000, 0.1), key(1000, 50))
        self.assertLess(key(1000, 50), key(1000, None))
        self.assertLess(key(1000, None), key(2000, 0.1))


if __name__ == "__main__":
    unittest.main()
