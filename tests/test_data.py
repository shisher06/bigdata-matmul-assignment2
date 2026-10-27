"""Tests de los datos de entrada, la E/S binaria y el verificador.

Se ejecutan con:  python -m unittest discover -s tests -v

Cubren: que el generador denso sigue reproduciendo EXACTAMENTE los ficheros de la Práctica 1
(SHA-256 del manifest copiado de practica1/data/manifest.json), el generador de matrices
dispersas (determinismo, densidad real, rango de valores, casos 0 % y 100 %, manifest y
detección de ficheros corruptos), la E/S en el formato compartido y las tolerancias de
verify.py.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "python"))

import datagen  # noqa: E402
import matrix_io  # noqa: E402

try:
    import numpy as np
    import verify
except ImportError:  # pragma: no cover
    np = None


class TestDenseInputsAreThoseOfAssignment1(unittest.TestCase):
    def test_regeneration_reproduces_p1_manifest(self):
        manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["base_seed"], 2026)
        for n in (10, 25, 50):
            seed_a, seed_b = datagen.seeds_for(2026, n)
            for name, seed in (("A", seed_a), ("B", seed_b)):
                with self.subTest(n=n, matrix=name):
                    payload = datagen.to_le_bytes(datagen.generate_values(seed, n))
                    self.assertEqual(datagen.sha256_bytes(payload),
                                     manifest["files"][str(n)][name]["sha256"])

    def test_same_manifest_as_practica1_when_available(self):
        p1 = ROOT.parent / "practica1" / "data" / "manifest.json"
        if not p1.exists():
            self.skipTest("practica1/ no está al lado de practica2/")
        old = json.loads(p1.read_text(encoding="utf-8"))["files"]
        new = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))["files"]
        for n, entry in old.items():
            for name in ("A", "B"):
                with self.subTest(n=n, matrix=name):
                    self.assertEqual(new[n][name]["sha256"], entry[name]["sha256"])


class TestSparseGenerator(unittest.TestCase):
    def test_deterministic_density_and_range(self):
        n, pct = 200, 10.0
        seed_a, seed_b = datagen.sparse_seeds_for(2026, n, pct)
        self.assertEqual(seed_b, seed_a + 1)
        v1, nnz1 = datagen.generate_sparse_values(seed_a, n, pct)
        v2, nnz2 = datagen.generate_sparse_values(seed_a, n, pct)
        self.assertEqual(v1.tobytes(), v2.tobytes())
        self.assertEqual(nnz1, nnz2)
        self.assertEqual(nnz1, sum(1 for x in v1 if x != 0.0))
        # binomial(n², 0.1): media 4000, desviación 60 -> margen de 5 desviaciones
        expected, sd = n * n * pct / 100, math.sqrt(n * n * 0.1 * 0.9)
        self.assertLess(abs(nnz1 - expected), 5 * sd)
        self.assertTrue(all(0.0 < x <= 1.0 for x in v1 if x != 0.0))
        other, _ = datagen.generate_sparse_values(seed_b, n, pct)
        self.assertNotEqual(v1.tobytes(), other.tobytes())

    def test_zero_and_full_density(self):
        values, nnz = datagen.generate_sparse_values(3, 30, 0.0)
        self.assertEqual(nnz, 0)
        self.assertTrue(all(x == 0.0 for x in values))
        values, nnz = datagen.generate_sparse_values(3, 30, 100.0)
        self.assertEqual(nnz, 900)
        with self.assertRaises(ValueError):
            datagen.generate_sparse_values(3, 30, 150.0)

    def test_seeds_do_not_collide(self):
        seeds = set()
        for n in (1000, 2000, 4000):
            for pct in (0.1, 0.5, 1, 2, 5, 10, 20, 30, 50):
                seeds.update(datagen.sparse_seeds_for(2026, n, pct))
            seeds.update(datagen.seeds_for(2026, n))
        self.assertEqual(len(seeds), 3 * (9 * 2 + 2))

    def test_manifest_verify_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            manifest = datagen.generate_sparse([20], [5.0, 50.0], d, log=lambda *_: None)
            entry = manifest["files"]["20_d5"]["A"]
            self.assertEqual(entry["file"], "A_20_d5.bin")
            self.assertEqual(entry["density_pct"], 5.0)
            self.assertEqual(datagen.verify(d), [])
            M = matrix_io.read_matrix(d / "A_20_d5.bin", 20)
            self.assertEqual(sum(1 for row in M for x in row if x), entry["nnz"])
            # regenerar no cambia nada; corromper un fichero se detecta
            datagen.generate_sparse([20], [5.0], d, log=lambda *_: None)
            path = d / "B_20_d50.bin"
            raw = bytearray(path.read_bytes())
            raw[0] ^= 1
            path.write_bytes(bytes(raw))
            self.assertTrue(any("B_20_d50.bin" in p for p in datagen.verify(d)))


class TestMatrixIO(unittest.TestCase):
    def test_roundtrip_and_wrong_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "M.bin"
            M = [[1.5, -2.0, 0.0], [3.25, 4.0, 1e-300], [0.0, 0.0, 7.0]]
            matrix_io.write_matrix(path, M)
            self.assertEqual(path.stat().st_size, 8 * 9)
            self.assertEqual(matrix_io.read_matrix(path, 3), M)
            with self.assertRaises(ValueError):
                matrix_io.read_matrix(path, 4)


@unittest.skipIf(np is None, "NumPy no instalado (solo se usa como referencia)")
class TestVerifier(unittest.TestCase):
    def test_tolerances(self):
        R = np.random.default_rng(0).random((30, 30))
        self.assertTrue(verify.compare(R * (1 + 1e-13), R)["ok"])
        bad = R.copy()
        bad[3, 4] += 1e-3
        self.assertFalse(verify.compare(bad, R)["ok"])
        nan = R.copy()
        nan[0, 0] = np.nan
        self.assertFalse(verify.compare(nan, R)["ok"])


if __name__ == "__main__":
    unittest.main()
