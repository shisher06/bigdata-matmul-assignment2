#!/usr/bin/env python3
"""Compila el worker de C y documenta compilador y flags.

Reutilizado de la Práctica 1. En la Práctica 2 solo se compila la configuración principal
de C de la P1 (``-O2``): todos los métodos (ijk, ikj, blocked, csr) están en el MISMO
binario y se eligen con ``--method``, así que comparten compilador y flags.

Salidas::

    build/c/matmul.exe            C -O2 (los cuatro métodos): la configuración de TODAS las
                                  comparaciones principales
    build/build_info.json         versión exacta del compilador y flags usados

``-ffp-contract=off`` impide que GCC fusione ``C[i][j] += a * B[k][j]`` en una sola
instrucción FMA: con FMA cambia el redondeo y C dejaría de coincidir bit a bit con el
baseline. Sin ``-ffast-math``, así que el orden de las sumas no cambia. Con gcc 11 ``-O2``
no activa la vectorización automática (``-ftree-vectorize`` llega con ``-O3``): las
diferencias entre métodos se deben al acceso a memoria, no a instrucciones SIMD.

Uso::

    python scripts/build.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
EXE = ".exe" if sys.platform == "win32" else ""

C_SOURCE = ROOT / "src" / "c" / "matmul.c"
C_COMMON = ["-std=c11", "-Wall", "-Wextra", "-ffp-contract=off"]
# variante -> flags de optimización. "O2" es la configuración de la comparación principal.
C_VARIANTS = {
    "O2": ["-O2"],
}


def c_binary(variant: str = "O2") -> Path:
    name = "matmul" if variant == "O2" else f"matmul_{variant}"
    return BUILD / "c" / f"{name}{EXE}"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _first_line(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    text = (proc.stdout or proc.stderr).strip().splitlines()
    return text[0] if text else "desconocido"


def c_flags(variant: str) -> list[str]:
    return [*C_COMMON, *C_VARIANTS[variant]]


def build_c(gcc: str = "gcc") -> dict:
    (BUILD / "c").mkdir(parents=True, exist_ok=True)
    built = {}
    for variant in C_VARIANTS:
        flags = c_flags(variant)
        out = c_binary(variant)
        cmd = ["gcc", *flags, f'-DBUILD_FLAGS="{" ".join(flags)}"', "-o", _rel(out), _rel(C_SOURCE)]
        if sys.platform == "win32":
            cmd.append("-lpsapi")
        else:
            cmd.append("-lm")
        print("  $", " ".join(cmd), flush=True)
        subprocess.run([gcc, *cmd[1:]], check=True, cwd=ROOT)
        built[variant] = {"binary": _rel(out), "flags": " ".join(flags),
                          "command": " ".join(cmd)}
    return built


def build() -> dict:
    gcc = shutil.which("gcc")
    if not gcc:
        raise RuntimeError("Falta gcc en el PATH")
    print("== Compilación ==", flush=True)
    info = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gcc": {"path": gcc, "version": _first_line([gcc, "--version"]),
                "target": _first_line([gcc, "-dumpmachine"])},
        "c": build_c(gcc),
    }
    (BUILD / "build_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    return info


def load_info() -> dict | None:
    path = BUILD / "build_info.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    info = build()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
