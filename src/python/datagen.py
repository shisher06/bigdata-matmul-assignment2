#!/usr/bin/env python3
"""Generador determinista de las matrices de entrada compartidas.

Reutilizado de la Práctica 1 SIN CAMBIOS en la parte densa (mismas semillas, mismo
generador, mismo formato): ``data/A_<n>.bin`` y ``data/B_<n>.bin`` son exactamente los
mismos ficheros que en la Práctica 1 (mismo SHA-256 que su ``data/manifest.json``).
Formato: float64 little-endian, row-major, sin cabecera; valores uniformes en [0, 1).

Novedad de la Práctica 2: matrices DISPERSAS para la Parte B, en el MISMO formato denso
(los ceros se guardan), para que todos los métodos lean las mismas matrices lógicas:
``data_sparse/A_<n>_d<pct>.bin`` y ``B_...``. Para cada celda, con un generador propio:

    u = rnd.random();  valor = 1.0 - rnd.random() si u < densidad, si no 0.0

Es decir, cada celda es no-cero de forma independiente con probabilidad ``densidad``
(posiciones uniformes, sin estructura) y su valor es uniforme en (0, 1] (nunca 0).
El número real de no-ceros queda en ``data_sparse/manifest.json``.

Reproducibilidad:

* Densas: semilla de A_n = base_seed * 1_000_003 + 2n; la de B_n es esa + 1.
* Dispersas: semilla de A = (base_seed * 1_000_003 + 2n) * 1_000_000 + 2 * round(1000 * pct);
  la de B es esa + 1 (pct = densidad en %).
* ``random.Random(seed).random()`` produce la misma secuencia en cualquier
  versión de CPython 3 y en cualquier sistema operativo.
* Los ``manifest.json`` guardan semilla, formato y SHA-256 de cada fichero.
  Si regeneras y el SHA-256 no coincide con el del manifest, el script avisa.

Uso::

    python src/python/datagen.py                          # densas, tamaños por defecto
    python src/python/datagen.py --sizes 10 100           # densas, tamaños concretos
    python src/python/datagen.py --sizes 1000 --densities 0.1 1 10   # dispersas
    python src/python/datagen.py --verify                 # comprueba integridad
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_SEED = 2026
# Tamaños de la Práctica 1 + potencias de dos (anomalía de la P1) + tamaños mayores.
DEFAULT_SIZES = [10, 25, 50, 100, 200, 300, 400, 500, 512, 600, 800, 1000, 1024, 1200, 1500,
                 1536, 2000, 2048, 2500, 3000, 4000]
DEFAULT_SPARSE_DIR = ROOT / "data_sparse"
SPARSE_GENERATOR_DESC = (
    "CPython random.Random(seed): por celda u = random(); valor = 1 - random() si "
    "u < densidad, si no 0.0 (posiciones uniformes e independientes, valores en (0, 1])"
)
MANIFEST_NAME = "manifest.json"

GENERATOR_DESC = (
    "CPython random.Random(seed).random() (Mersenne Twister), uniforme en [0, 1)"
)


def seeds_for(base_seed: int, n: int) -> tuple[int, int]:
    seed_a = base_seed * 1_000_003 + 2 * n
    return seed_a, seed_a + 1


def generate_values(seed: int, n: int) -> array:
    rnd = random.Random(seed)
    rand = rnd.random
    return array("d", [rand() for _ in range(n * n)])


def to_le_bytes(values: array) -> bytes:
    if sys.byteorder == "big":
        values = array("d", values)
        values.byteswap()
    return values.tobytes()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matrix_path(data_dir: Path, name: str, n: int) -> Path:
    return data_dir / f"{name}_{n}.bin"


def _new_manifest(seed: int) -> dict:
    return {
        "generator": GENERATOR_DESC,
        "dtype": "float64 little-endian",
        "layout": "row-major, sin cabecera (8*n*n bytes)",
        "value_range": "[0, 1)",
        "base_seed": seed,
        "seed_rule": "A_n: base_seed*1000003 + 2n ; B_n: A_n + 1",
        "files": {},
    }


def load_manifest(data_dir: Path) -> dict | None:
    path = data_dir / MANIFEST_NAME
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _entry_order(key: str) -> tuple[int, float]:
    """Orden de las entradas del manifest: "1000" (densas) o "1000_d0.5" (dispersas)."""
    n, _, pct = key.partition("_d")
    return int(n), float(pct or 0)


def save_manifest(data_dir: Path, manifest: dict) -> None:
    manifest["files"] = dict(sorted(manifest["files"].items(), key=lambda kv: _entry_order(kv[0])))
    with open(data_dir / MANIFEST_NAME, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")


def generate(
    sizes: list[int],
    data_dir: Path = DEFAULT_DATA_DIR,
    seed: int = DEFAULT_SEED,
    force: bool = False,
    log=print,
) -> dict:
    """Genera (si faltan o están corruptos) los ficheros de ``sizes``."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(data_dir)
    if manifest is None or force and manifest.get("base_seed") != seed:
        manifest = _new_manifest(seed)
    elif manifest["base_seed"] != seed:
        raise ValueError(
            f"{MANIFEST_NAME} se creó con la semilla {manifest['base_seed']}, no {seed}. "
            "Usa --force para regenerar todo con la nueva semilla."
        )

    for n in sizes:
        if n < 1:
            raise ValueError(f"Tamaño inválido: {n}")
        seed_a, seed_b = seeds_for(seed, n)
        entry = manifest["files"].setdefault(str(n), {})
        for name, s in (("A", seed_a), ("B", seed_b)):
            path = matrix_path(data_dir, name, n)
            expected = entry.get(name, {}).get("sha256")
            if path.exists() and not force and expected and sha256_file(path) == expected:
                log(f"  {path.name}: ya existe y coincide con el manifest")
                continue
            payload = to_le_bytes(generate_values(s, n))
            digest = sha256_bytes(payload)
            if expected and not force and digest != expected:
                raise RuntimeError(
                    f"La regeneración de {path.name} con la semilla {s} NO reproduce el "
                    f"SHA-256 del manifest ({digest[:12]}… != {expected[:12]}…)."
                )
            path.write_bytes(payload)
            entry[name] = {
                "file": path.name,
                "seed": s,
                "bytes": len(payload),
                "sha256": digest,
            }
            log(f"  {path.name}: generado ({len(payload) / 1e6:.2f} MB)")

    save_manifest(data_dir, manifest)
    return manifest


def verify(data_dir: Path = DEFAULT_DATA_DIR) -> list[str]:
    """Comprueba que los ficheros existen y coinciden con el manifest."""
    data_dir = Path(data_dir)
    manifest = load_manifest(data_dir)
    if manifest is None:
        return [f"No existe {data_dir / MANIFEST_NAME}"]
    problems: list[str] = []
    for n, entry in manifest["files"].items():
        for name, info in entry.items():
            path = data_dir / info["file"]
            if not path.exists():
                problems.append(f"{path.name}: falta")
            elif path.stat().st_size != info["bytes"]:
                problems.append(f"{path.name}: tamaño distinto del manifest")
            elif sha256_file(path) != info["sha256"]:
                problems.append(f"{path.name}: SHA-256 distinto del manifest")
    return problems


# --------------------------------------------------------------------------- #
# Matrices dispersas (Parte B de la Práctica 2)
# --------------------------------------------------------------------------- #
def density_label(pct: float) -> str:
    """0.1 -> "0.1", 5.0 -> "5" (densidad en %, para nombres de fichero y del manifest)."""
    return f"{pct:g}"


def sparse_seeds_for(base_seed: int, n: int, pct: float) -> tuple[int, int]:
    seed_a = (base_seed * 1_000_003 + 2 * n) * 1_000_000 + 2 * round(1000 * pct)
    return seed_a, seed_a + 1


def sparse_path(data_dir: Path, name: str, n: int, pct: float) -> Path:
    return Path(data_dir) / f"{name}_{n}_d{density_label(pct)}.bin"


def generate_sparse_values(seed: int, n: int, pct: float) -> tuple[array, int]:
    """Matriz n x n con cada celda no-cero con probabilidad pct/100. Devuelve (valores, nnz)."""
    if not 0 <= pct <= 100:
        raise ValueError(f"Densidad fuera de [0, 100] %: {pct}")
    d = pct / 100.0
    rnd = random.Random(seed)
    rand = rnd.random
    values = array("d", [(1.0 - rand()) if rand() < d else 0.0 for _ in range(n * n)])
    nnz = n * n - values.tolist().count(0.0)
    return values, nnz


def _new_sparse_manifest(seed: int) -> dict:
    return {
        "generator": SPARSE_GENERATOR_DESC,
        "dtype": "float64 little-endian",
        "layout": "row-major, sin cabecera (8*n*n bytes); los ceros se guardan (formato denso)",
        "value_range": "(0, 1] en los no-ceros",
        "nonzero_distribution": "uniforme: cada celda es no-cero de forma independiente con "
                                "probabilidad = densidad",
        "base_seed": seed,
        "seed_rule": "A: (base_seed*1000003 + 2n)*1000000 + 2*round(1000*pct) ; B: A + 1",
        "files": {},
    }


def generate_sparse(
    sizes: list[int],
    densities: list[float],
    data_dir: Path = DEFAULT_SPARSE_DIR,
    seed: int = DEFAULT_SEED,
    force: bool = False,
    log=print,
) -> dict:
    """Genera (si faltan o están corruptos) las matrices dispersas de sizes x densities."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(data_dir)
    if manifest is None or force and manifest.get("base_seed") != seed:
        manifest = _new_sparse_manifest(seed)
    elif manifest["base_seed"] != seed:
        raise ValueError(
            f"{MANIFEST_NAME} se creó con la semilla {manifest['base_seed']}, no {seed}. "
            "Usa --force para regenerar todo con la nueva semilla."
        )
    for n in sizes:
        for pct in densities:
            seed_a, seed_b = sparse_seeds_for(seed, n, pct)
            entry = manifest["files"].setdefault(f"{n}_d{density_label(pct)}", {})
            for name, s in (("A", seed_a), ("B", seed_b)):
                path = sparse_path(data_dir, name, n, pct)
                expected = entry.get(name, {}).get("sha256")
                if path.exists() and not force and expected and sha256_file(path) == expected:
                    log(f"  {path.name}: ya existe y coincide con el manifest")
                    continue
                values, nnz = generate_sparse_values(s, n, pct)
                payload = to_le_bytes(values)
                digest = sha256_bytes(payload)
                if expected and not force and digest != expected:
                    raise RuntimeError(
                        f"La regeneración de {path.name} con la semilla {s} NO reproduce el "
                        f"SHA-256 del manifest ({digest[:12]}… != {expected[:12]}…)."
                    )
                path.write_bytes(payload)
                entry[name] = {
                    "file": path.name,
                    "n": n,
                    "density_pct": pct,
                    "seed": s,
                    "nnz": nnz,
                    "actual_density_pct": 100.0 * nnz / (n * n),
                    "bytes": len(payload),
                    "sha256": digest,
                }
                log(f"  {path.name}: generado ({len(payload) / 1e6:.2f} MB, nnz = {nnz}, "
                    f"densidad real {100.0 * nnz / (n * n):.4g} %)")
            save_manifest(data_dir, manifest)  # tras cada par: lo generado no se pierde
    save_manifest(data_dir, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    parser.add_argument("--densities", type=float, nargs="+", default=None,
                        help="densidades en %% (no-ceros); si se indica, genera matrices dispersas")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="por defecto data/ (densas) o data_sparse/ (dispersas)")
    parser.add_argument("--force", action="store_true", help="regenera aunque existan")
    parser.add_argument("--verify", action="store_true", help="solo comprueba integridad")
    args = parser.parse_args(argv)
    sparse = args.densities is not None
    data_dir = args.data_dir or (DEFAULT_SPARSE_DIR if sparse else DEFAULT_DATA_DIR)

    if args.verify:
        dirs = [args.data_dir] if args.data_dir else [DEFAULT_DATA_DIR, DEFAULT_SPARSE_DIR]
        problems = [p for d in dirs if (Path(d) / MANIFEST_NAME).exists() or d == DEFAULT_DATA_DIR
                    for p in verify(d)]
        if problems:
            print("PROBLEMAS:\n  " + "\n  ".join(problems))
            return 1
        print("Todos los ficheros coinciden con el manifest.")
        return 0

    print(f"Generando datos en {data_dir} (semilla base {args.seed})")
    if sparse:
        generate_sparse(sorted(set(args.sizes)), sorted(set(args.densities)), data_dir, args.seed,
                        args.force)
    else:
        generate(sorted(set(args.sizes)), data_dir, args.seed, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
