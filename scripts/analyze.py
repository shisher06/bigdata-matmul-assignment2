#!/usr/bin/env python3
"""Genera tablas y gráficas a partir de los CSV de medidas en bruto de la Práctica 2.

Basado en ``analyze.py`` de la Práctica 1 (mismos estadísticos, mismo estilo de gráficas);
las tablas y figuras se adaptan a lo que compara la Práctica 2. El tipo de campaña se
detecta solo (o con ``--kind``):

* ``dense``  (Parte A, results/01_A_densa): ijk vs ikj vs blocked frente a n.
    summary.md, summary.csv y plots/ time_vs_n, ns_per_iter_vs_n, speedup_vs_n,
    memory_vs_n, variability_vs_n. Con ``--p1-summary`` añade la comparación del baseline
    con la medida de la Práctica 1.
* ``blocks`` (results/02_A_extra_bloques): tamaño de bloque de blocked.
    plots/block_size.png
* ``sparse`` (Parte B, results/03_B_dispersa y 04_...): csr vs densos frente a la densidad.
    plots/ sparse_time_vs_density, sparse_speedup_vs_density, sparse_output_fill,
    sparse_memory, sparse_cost_per_product

Estadísticos: mediana y rango intercuartílico (Q1, Q3 con interpolación lineal,
``numpy.percentile``) de las ejecuciones con ``status == OK``. Las fallidas (timeout, OOM...)
NO entran en ninguna mediana: se listan aparte como resultados.

Uso::

    python scripts/analyze.py --csv results/01_A_densa/raw.csv --out-dir results/01_A_densa \\
        --p1-summary ../practica1/results/04_comparativa_3_lenguajes/summary.csv
    python scripts/analyze.py --csv results/03_B_dispersa/raw.csv --out-dir results/03_B_dispersa
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Mismo estilo que la Práctica 1. El baseline ijk conserva el color de "C (-O2)" de la P1.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
STYLE = {
    "ijk": {"color": "#1baf7a", "marker": "^", "label": "ijk (baseline, A1)"},
    "ikj": {"color": "#2a78d6", "marker": "o", "label": "ikj (loop order)"},
    "blocked": {"color": "#eb6834", "marker": "s", "label": "blocked ikj (64)"},
    "csr": {"color": "#6250d6", "marker": "D", "label": "CSR (Gustavson)"},
}
BLOCK_COLORS = ["#9ec5f0", "#5b9de0", "#2a78d6", "#1a4f99", "#0b2a57"]
FALLBACK = {"color": "#e34948", "marker": "*"}
ORDER = ["ijk", "ikj", "blocked", "csr"]

NUM_FIELDS = [
    "repetition", "reps_planned", "time_ns", "batch", "convert_ns", "nnz_a", "nnz_b", "nnz_c",
    "proc_peak_wset_bytes", "inproc_peak_bytes", "inproc_baseline_bytes", "wset_after_bytes",
    "array_model_bytes", "object_model_bytes", "max_rel_err", "max_abs_err", "os_threads_max",
    "warmup_runs", "warmup_n", "run_order", "block", "density_pct",
]


def _num(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with open(path, "r", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for key in NUM_FIELDS:
                    row[key] = _num(row.get(key))
                row["n"] = int(row["n"])
                rows.append(row)
    return rows


def style_for(config: str) -> dict:
    if config in STYLE:
        return STYLE[config]
    if config.startswith("blocked-"):
        bs = int(config.split("-")[1])
        idx = [16, 32, 64, 128, 256].index(bs) if bs in (16, 32, 64, 128, 256) else 0
        return {"color": BLOCK_COLORS[idx], "marker": "os^Dv"[idx], "label": f"block {bs}"}
    return {**FALLBACK, "label": config}


def sort_configs(configs) -> list:
    def k(c):
        if c in ORDER:
            return (0, ORDER.index(c), 0)
        if c.startswith("blocked-"):
            return (1, 0, int(c.split("-")[1]))
        return (2, 0, c)
    return sorted(configs, key=k)


def _median(values):
    values = [v for v in values if v is not None and v >= 0]
    return float(np.median(values)) if values else float("nan")


def summarise(rows: list[dict]) -> tuple[list[dict], dict]:
    """Una fila por (config, n, densidad). Devuelve (resumen, fallos por configuración)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["config"], row["n"], row["density_pct"])].append(row)
    summary, failures = [], defaultdict(list)
    for (config, n, dens), grp in sorted(
            groups.items(), key=lambda kv: (sort_configs([kv[0][0]]) and ORDER.index(kv[0][0])
                                            if kv[0][0] in ORDER else 9, kv[0][0], kv[0][1],
                                            kv[0][2] if kv[0][2] is not None else 101)):
        ok = [r for r in grp if r["status"] == "OK" and r["time_ns"] is not None]
        failures[config].extend(r for r in grp if r["status"] != "OK")
        if not ok:
            continue
        t = np.array([r["time_ns"] for r in ok]) / 1e9
        q1, med, q3 = np.percentile(t, [25, 50, 75])
        conv = [r["convert_ns"] for r in ok if r["convert_ns"] is not None]
        conv_med = float(np.median(conv)) / 1e9 if conv else float("nan")
        verified = [r for r in ok if r.get("verified") == "yes"]
        nnz_c = ok[0]["nnz_c"]
        summary.append({
            "config": config, "method": ok[0]["method"], "block": int(ok[0]["block"] or 0),
            "n": n, "density_pct": dens if dens is not None else float("nan"),
            "reps_ok": len(ok),
            "reps_planned": max(int(r["reps_planned"] or 0) for r in ok) or len(ok),
            "median_s": med, "q1_s": q1, "q3_s": q3, "iqr_s": q3 - q1,
            "rel_iqr_pct": 100 * (q3 - q1) / med if med > 0 else float("nan"),
            "min_s": float(t.min()), "max_s": float(t.max()),
            "ns_per_inner_iter": med * 1e9 / n**3,
            "convert_s": conv_med,
            "total_with_convert_s": med + conv_med if conv else med,
            "nnz_a": ok[0]["nnz_a"], "nnz_b": ok[0]["nnz_b"], "nnz_c": nnz_c,
            "density_a_pct": 100 * ok[0]["nnz_a"] / n**2 if ok[0]["nnz_a"] is not None else float("nan"),
            "density_c_pct": 100 * nnz_c / n**2 if nnz_c is not None else float("nan"),
            "proc_peak_mb": _median(r["proc_peak_wset_bytes"] for r in ok) / 1e6,
            "wset_after_mb": _median(r["wset_after_bytes"] for r in ok) / 1e6,
            "inproc_above_baseline_mb": (_median(r["inproc_peak_bytes"] for r in ok)
                                         - _median(r["inproc_baseline_bytes"] for r in ok)) / 1e6,
            "array_model_mb": (ok[0]["array_model_bytes"] or float("nan")) / 1e6,
            "object_model_mb": (ok[0]["object_model_bytes"] or float("nan")) / 1e6,
            "batch": int(ok[-1]["batch"] or 1),
            "warmup": f"{int(ok[0]['warmup_runs'] or 0)}x{int(ok[0]['warmup_n'] or 0)}",
            "os_threads_max": max((r["os_threads_max"] or 0) for r in ok) or float("nan"),
            "max_rel_err": verified[0]["max_rel_err"] if verified else float("nan"),
            "c_sha256": next((r.get("c_sha256") for r in ok if r.get("c_sha256")), ""),
            "runtime": ok[0].get("runtime_version") or "",
            "flags": ok[0].get("runtime_flags") or "",
        })
    return summary, failures


def loglog_fit(points):
    """Pendiente de log(t) vs log(n). Devuelve (pendiente, error_estándar|None) o None."""
    if len(points) < 2:
        return None
    x = np.log([p[0] for p in points])
    y = np.log([p[1] for p in points])
    if len(points) >= 4:
        coeffs, cov = np.polyfit(x, y, 1, cov=True)
        return float(coeffs[0]), float(np.sqrt(cov[0, 0]))
    return float(np.polyfit(x, y, 1)[0]), None


def fmt(x, digits=4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{x:.{digits}g}"


def fmt_s(x) -> str:
    """Tiempo legible con unidad."""
    if x is None or math.isnan(x):
        return "-"
    if x < 1e-3:
        return f"{x * 1e6:.3g} µs"
    if x < 1:
        return f"{x * 1e3:.3g} ms"
    return f"{x:.4g} s"


def fmt_pct(x) -> str:
    return "-" if x is None or math.isnan(x) else f"{x:g}"


def series(summary, config, density=None):
    return sorted((s for s in summary if s["config"] == config and
                   (density is None or s["density_pct"] == density)), key=lambda s: s["n"])


def write_summary_csv(summary: list[dict], path: Path) -> None:
    if not summary:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)


def limits_lines(config, rows, failures) -> list[str]:
    mine = [r for r in rows if r["config"] == config]
    bad = failures.get(config, [])
    ok_n = sorted({r["n"] for r in mine if r["status"] == "OK"})
    first_bad = min((r["n"] for r in bad), default=None)
    within = [n for n in ok_n if first_bad is None or n < first_bad]
    lines = [f"- Mayor tamaño probado dentro de los límites: **{max(within) if within else '-'}**",
             f"- Mayor tamaño intentado: **{max(r['n'] for r in mine) if mine else '-'}**"]
    for r in bad:
        dens = f", densidad {fmt_pct(r['density_pct'])} %" if r["density_pct"] is not None else ""
        lines.append(
            f"- n = {r['n']}{dens}, repetición {int(r['repetition'] or 0)}: **{r['status']}** "
            f"({r.get('note') or ''}); límite de tiempo {r.get('timeout_s')} s, presupuesto de "
            f"memoria {r.get('mem_budget_mb') or '-'} MB. Sin tiempo asignado.")
    if not bad:
        lines.append("- Sin timeouts ni fallos de memoria.")
    return lines


def correctness_lines(summary) -> list[str]:
    by_case = defaultdict(dict)
    for s in summary:
        if s["c_sha256"]:
            dens = None if math.isnan(s["density_pct"]) else s["density_pct"]
            by_case[(s["n"], dens)][s["config"]] = s["c_sha256"]
    same = [c for c, d in by_case.items() if len(d) >= 2 and len(set(d.values())) == 1]
    diff = [c for c, d in by_case.items() if len(d) >= 2 and len(set(d.values())) > 1]
    def lab(c):
        return f"{c[0]}" if c[1] is None else f"{c[0]}/{fmt_pct(c[1])}%"
    L = [f"- Matriz C idéntica bit a bit (mismo SHA-256 del volcado) en todos los métodos medidos "
         f"en {len(same)} de {len(same) + len(diff)} casos comparables"
         + (f": {', '.join(lab(c) for c in sorted(same, key=lambda c: (c[0], 101 if c[1] is None else c[1])))}."
            if same else ".")]
    if diff:
        L.append(f"- **C distinta entre métodos** en: {', '.join(lab(c) for c in diff)}.")
    errs = [s["max_rel_err"] for s in summary if not math.isnan(s["max_rel_err"])]
    if errs:
        L.append(f"- Error relativo máximo frente a NumPy (repetición 1, todas las configuraciones): "
                 f"{max(errs):.3g} (tolerancia rtol = 1e-9).")
    L.append("- Repeticiones 2..k: checksum igual al de la repetición 1 en todas las filas `OK`.")
    return L


def config_table_lines(summary, config) -> list[str]:
    sel = [s for s in summary if s["config"] == config]
    sparse = any(not math.isnan(s["density_pct"]) for s in sel)
    L = []
    if sel:
        L.append(f"Compilador: {sel[0]['runtime']}; flags: `{sel[0]['flags'] or '-'}`. «calent.» = "
                 f"ejecuciones x tamaño del calentamiento (incluye la calibración del lote).\n")
    head = "| n | " + ("densidad (%) | " if sparse else "") + \
        "reps | mediana | Q1 | Q3 | IQR/med (%) | ns/n³ | lote | calent. | " + \
        ("conversión | " if config == "csr" else "") + \
        "pico proceso (MB) | WS tras multiplicar (MB) | estructuras (MB) |"
    L.append(head)
    L.append("|" + "---:|" * (head.count("|") - 1))
    for s in sorted(sel, key=lambda s: (s["n"], np.nan_to_num(s["density_pct"], nan=101))):
        reps = f"{s['reps_ok']}" + (f"/{s['reps_planned']}" if s["reps_ok"] != s["reps_planned"] else "")
        if s["reps_ok"] < 5:
            reps += " (!)"
        cells = [str(s["n"])]
        if sparse:
            cells.append(fmt_pct(s["density_pct"]))
        cells += [reps, fmt_s(s["median_s"]), fmt_s(s["q1_s"]), fmt_s(s["q3_s"]),
                  fmt(s["rel_iqr_pct"], 3), fmt(s["ns_per_inner_iter"], 4), str(s["batch"]),
                  s["warmup"]]
        if config == "csr":
            cells.append(fmt_s(s["convert_s"]))
        cells += [fmt(s["proc_peak_mb"], 4), fmt(s["wset_after_mb"], 4), fmt(s["object_model_mb"], 4)]
        L.append("| " + " | ".join(cells) + " |")
    L += ["", "(!) = menos de 5 repeticiones (justificado por coste; ver el informe).", ""]
    return L


# --------------------------------------------------------------------------- #
# Gráficas: utilidades (las mismas que en la Práctica 1)
# --------------------------------------------------------------------------- #
def _prep_axes(ax, xlabel: str, ylabel: str, title: str | None = None):
    ax.set_facecolor(SURFACE)
    if title:
        ax.set_title(title, loc="left", fontsize=10.5, color=INK)
    ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    ax.tick_params(colors=INK_2, labelsize=8.5)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _legend(ax, fontsize=8.5, **kw):
    return ax.legend(frameon=False, fontsize=fontsize, labelcolor=INK, **kw)


def _new_fig(w=7.2, h=4.6, ncols=1):
    fig, ax = plt.subplots(1, ncols, figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return path


def _xticks_n(ax, ns):
    candidates = (10, 25, 50, 100, 200, 500, 1000, 2000, 4000)
    ticks = [n for n in candidates if min(ns) <= n <= max(ns)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.minorticks_off()


def _xticks_density(ax, ds):
    ticks = [d for d in (0.1, 0.5, 1, 2, 5, 10, 20, 50, 100) if min(ds) <= d <= max(ds)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.minorticks_off()


def _pow2_marks(ax, ns):
    for p in (512, 1024, 1536, 2048):
        if p in ns:  # solo las que se midieron
            ax.axvline(p, color=GRID, linewidth=5, alpha=0.7, zorder=0)


# --------------------------------------------------------------------------- #
# Parte A: densas
# --------------------------------------------------------------------------- #
def dense_report(summary, failures, rows, fit_min_n, p1_summary: Path | None, out_dir: Path) -> str:
    configs = sort_configs({s["config"] for s in summary})
    by = {c: {s["n"]: s for s in series(summary, c)} for c in configs}
    ns = sorted({s["n"] for s in summary})
    L = ["# Resumen de resultados - Parte A (densas)", ""]
    L.append("Estadísticos sobre las ejecuciones con `status = OK`: mediana y rango intercuartílico "
             "(IQR = Q3 - Q1). Tiempos por multiplicación. Memoria en MB decimales (10⁶ B). "
             "Cada ejecución es un proceso nuevo. Mismas entradas que la Práctica 1.\n")
    L += ["## Comparación entre métodos (mediana del tiempo por multiplicación)", ""]
    base = "ijk" if "ijk" in configs else None
    others = [c for c in configs if c != base]
    head = "| n | " + " | ".join(style_for(c)["label"] for c in configs)
    if base:
        head += " | " + " | ".join(f"speedup {c} vs ijk" for c in others)
    L.append(head + " |")
    L.append("|---:|" + "---:|" * (len(configs) + (len(others) if base else 0)))
    for n in ns:
        cells = [fmt_s(by[c][n]["median_s"]) if n in by[c] else "-" for c in configs]
        if base:
            for c in others:
                cells.append(f"{by[base][n]['median_s'] / by[c][n]['median_s']:.3g}x"
                             if n in by[c] and n in by[base] else "-")
        L.append(f"| {n} | " + " | ".join(cells) + " |")
    L += ["", "«-» = sin medida válida para ese tamaño (ver *Límites*).", ""]

    L += ["## Coste por iteración interna (ns = tiempo / n³)", ""]
    L.append("| n | " + " | ".join(style_for(c)["label"] for c in configs) + " |")
    L.append("|---:|" + "---:|" * len(configs))
    for n in ns:
        L.append(f"| {n} | " + " | ".join(fmt(by[c][n]["ns_per_inner_iter"], 3) if n in by[c] else "-"
                                          for c in configs) + " |")
    L.append("")

    if p1_summary and p1_summary.exists():
        with open(p1_summary, newline="", encoding="utf-8") as fh:
            p1 = {int(r["n"]): float(r["median_s"]) for r in csv.DictReader(fh)
                  if r["language"] == "c" and r["variant"] == "base"}
        common = [n for n in ns if n in p1 and base and n in by[base]]
        if common:
            L += ["## Baseline: reproducción de la medida de la Práctica 1", ""]
            L.append("El baseline `ijk` es el mismo código, flags y entradas que «C (-O2)» de la "
                     "Práctica 1 (campaña `04_comparativa_3_lenguajes`), medido de nuevo hoy.\n")
            L.append("| n | Práctica 1 (mediana) | Práctica 2 (mediana) | P2 / P1 |")
            L.append("|---:|---:|---:|---:|")
            for n in common:
                L.append(f"| {n} | {fmt_s(p1[n])} | {fmt_s(by[base][n]['median_s'])} | "
                         f"{by[base][n]['median_s'] / p1[n]:.3g} |")
            L.append("")

    L += ["## Memoria: pico del working set del proceso completo (MB)", ""]
    L.append("Medido por el runner con `GetProcessMemoryInfo` sobre el proceso hijo al terminar "
             "(la misma métrica que en la Práctica 1).\n")
    L.append("| n | " + " | ".join(style_for(c)["label"] for c in configs) + " | modelo 3·8n² |")
    L.append("|---:|" + "---:|" * (len(configs) + 1))
    for n in ns:
        cells = [fmt(by[c][n]["proc_peak_mb"], 4) if n in by[c] else "-" for c in configs]
        model = next((by[c][n]["array_model_mb"] for c in configs if n in by[c]), float("nan"))
        L.append(f"| {n} | " + " | ".join(cells) + f" | {fmt(model, 4)} |")
    L += ["", "## Corrección", "", *correctness_lines(summary), ""]

    for c in configs:
        sel = series(summary, c)
        L += [f"## {style_for(c)['label']} - `{c}`", "", *config_table_lines(summary, c)]
        L += ["### Límites", "", *limits_lines(c, rows, failures), ""]
        L += ["### Crecimiento frente al modelo cúbico", ""]
        pts = [(s["n"], s["median_s"]) for s in sel if s["n"] >= fit_min_n]
        fit = loglog_fit(pts)
        if fit:
            slope, se = fit
            se_txt = f" +- {se:.3f} (error estándar)" if se is not None else ""
            L.append(f"- Pendiente log-log de la mediana (n >= {fit_min_n}, {len(pts)} tamaños): "
                     f"**{slope:.3f}**{se_txt}; el modelo algorítmico predice 3.")
        pts2 = [(s["n"], s["median_s"]) for s in sel if s["n"] >= fit_min_n and s["n"] not in
                (512, 1024, 1536, 2048)]
        fit2 = loglog_fit(pts2)
        if fit2:
            L.append(f"- Igual pero sin las potencias de dos (512, 1024, 1536, 2048): "
                     f"**{fit2[0]:.3f}**.")
        L.append("")

    # ----- gráficas
    plots = out_dir / "plots"
    fig, ax = _new_fig()
    _prep_axes(ax, "n (matrix side, n x n)", "time per multiplication (s, log scale)",
               "Runtime vs. matrix size (median; bars = IQR)")
    guide_done = False
    for c in configs:
        st, s = style_for(c), series(summary, c)
        n = np.array([r["n"] for r in s], dtype=float)
        med = np.array([r["median_s"] for r in s])
        err = [med - np.array([r["q1_s"] for r in s]), np.array([r["q3_s"] for r in s]) - med]
        ax.errorbar(n, med, yerr=err, color=st["color"], marker=st["marker"], markersize=4,
                    linewidth=1.5, capsize=2, label=st["label"], zorder=3)
        anchor = next((r for r in s if r["n"] >= 100), None)
        if anchor is not None:
            xs = np.array([100, max(n)], dtype=float)
            ax.plot(xs, anchor["median_s"] * (xs / anchor["n"]) ** 3, linestyle=(0, (4, 3)),
                    color=st["color"], alpha=0.45, linewidth=1.0, zorder=2,
                    label=None if guide_done else "n³ trend anchored at n = 100 (same colour)")
            guide_done = True
    ax.set_xscale("log")
    ax.set_yscale("log")
    _xticks_n(ax, ns)
    _legend(ax, loc="upper left")
    _save(fig, plots / "time_vs_n.png")

    fig, ax = _new_fig()
    _prep_axes(ax, "n (matrix side, n x n; grey bands = powers of two and 1536)",
               "ns per inner iteration (time / n³)",
               "Cost per inner iteration: a flat line means exact n³ scaling")
    for c in configs:
        st, s = style_for(c), [r for r in series(summary, c) if r["n"] >= 100]
        ax.plot([r["n"] for r in s], [r["ns_per_inner_iter"] for r in s], color=st["color"],
                marker=st["marker"], markersize=4, linewidth=1.5, label=st["label"])
    ax.set_xscale("log")
    _xticks_n(ax, [n for n in ns if n >= 100])
    _pow2_marks(ax, [n for n in ns if n >= 100])
    ax.set_ylim(bottom=0)
    _legend(ax, loc="upper left")
    _save(fig, plots / "ns_per_iter_vs_n.png")

    if base:
        fig, ax = _new_fig()
        _prep_axes(ax, "n (matrix side, n x n; grey bands = powers of two and 1536)",
                   "speedup = time(ijk) / time(method)",
                   "Speedup over the Assignment 1 baseline (same inputs, same compiler flags)")
        for c in others:
            st = style_for(c)
            pts = [(n, by[base][n]["median_s"] / by[c][n]["median_s"]) for n in ns
                   if n in by[c] and n in by[base]]
            ax.plot(*zip(*pts), color=st["color"], marker=st["marker"], markersize=4,
                    linewidth=1.5, label=st["label"])
        ax.axhline(1.0, color=INK_2, linewidth=0.8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        _xticks_n(ax, ns)
        _pow2_marks(ax, ns)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}x"))
        _legend(ax, loc="upper left")
        _save(fig, plots / "speedup_vs_n.png")

    fig, ax = _new_fig(h=4.2)
    _prep_axes(ax, "n (matrix side, n x n)", "MB (10^6 bytes, log scale)",
               "Peak working set of the whole process")
    for c in configs:
        st, s = style_for(c), series(summary, c)
        ax.plot([r["n"] for r in s], [r["proc_peak_mb"] for r in s], color=st["color"],
                marker=st["marker"], markersize=4, linewidth=1.5, label=st["label"])
    s0 = series(summary, configs[0])
    ax.plot([r["n"] for r in s0], [r["array_model_mb"] for r in s0], color=INK_2,
            linestyle=(0, (4, 3)), linewidth=1.0, label="3 x 8 x n² bytes (A, B, C)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    _xticks_n(ax, ns)
    _legend(ax, loc="upper left")
    _save(fig, plots / "memory_vs_n.png")

    fig, ax = _new_fig(h=3.8)
    _prep_axes(ax, "n (matrix side, n x n)", "IQR / median (%)",
               "Variability across repetitions (each repetition is a fresh process)")
    for c in configs:
        st, s = style_for(c), series(summary, c)
        ax.plot([r["n"] for r in s], [r["rel_iqr_pct"] for r in s], color=st["color"],
                marker=st["marker"], markersize=4, linewidth=1.5, label=st["label"])
    ax.set_xscale("log")
    ax.set_ylim(bottom=0)
    _xticks_n(ax, ns)
    _legend(ax, loc="upper right")
    _save(fig, plots / "variability_vs_n.png")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Experimento aparte: tamaño de bloque
# --------------------------------------------------------------------------- #
def blocks_report(summary, failures, rows, out_dir: Path) -> str:
    configs = sort_configs({s["config"] for s in summary})
    ns = sorted({s["n"] for s in summary})
    by = {c: {s["n"]: s for s in series(summary, c)} for c in configs}
    L = ["# Resumen - experimento aparte: tamaño de bloque de `blocked`", ""]
    L.append("Mediana del tiempo por multiplicación (IQR/mediana entre paréntesis) y ns por "
             "iteración interna. El mejor bloque de cada n en negrita.\n")
    L.append("| n | " + " | ".join(style_for(c)["label"] for c in configs) + " |")
    L.append("|---:|" + "---:|" * len(configs))
    for n in ns:
        best = min((by[c][n]["median_s"] for c in configs if n in by[c]), default=None)
        cells = []
        for c in configs:
            if n not in by[c]:
                cells.append("-")
                continue
            s = by[c][n]
            txt = f"{fmt_s(s['median_s'])} ({fmt(s['rel_iqr_pct'], 2)} %), {s['ns_per_inner_iter']:.3f} ns"
            cells.append(f"**{txt}**" if s["median_s"] == best else txt)
        L.append(f"| {n} | " + " | ".join(cells) + " |")
    L += ["", "## Corrección", "", *correctness_lines(summary), ""]
    for c in configs:
        L += [f"## {style_for(c)['label']} - `{c}`", "", *config_table_lines(summary, c)]
        L += ["### Límites", "", *limits_lines(c, rows, failures), ""]

    fig, ax = _new_fig(h=4.2)
    _prep_axes(ax, "block size (bs x bs doubles)", "ns per inner iteration (time / n³)",
               "Blocked ikj: effect of the block size (median; bars = IQR)")
    blocks = sorted({s["block"] for s in summary})
    colors = ["#1baf7a", "#2a78d6", "#eb6834", "#6250d6", "#e87ba4", "#eda100"]
    for idx, n in enumerate(ns):
        pts = [(by[c][n]["block"], by[c][n]) for c in configs if n in by[c]]
        pts.sort()
        x = [p[0] for p in pts]
        med = np.array([p[1]["ns_per_inner_iter"] for p in pts])
        lo = med - np.array([p[1]["q1_s"] * 1e9 / n**3 for p in pts])
        hi = np.array([p[1]["q3_s"] * 1e9 / n**3 for p in pts]) - med
        ax.errorbar(x, med, yerr=[lo, hi], color=colors[idx % len(colors)], marker="os^Dv*"[idx % 6],
                    markersize=4, linewidth=1.5, capsize=2, label=f"n = {n}")
    ax.set_xscale("log", base=2)
    ax.set_xticks(blocks)
    ax.set_xticklabels([str(b) for b in blocks])
    ax.minorticks_off()
    ax.set_ylim(bottom=0)
    _legend(ax, loc="upper left")
    _save(fig, out_dir / "plots" / "block_size.png")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Parte B: dispersas
# --------------------------------------------------------------------------- #
def expected_output_density(n: int, d: float) -> float:
    """P(C[i][j] != 0) con no-ceros uniformes e independientes de densidad d: 1 - (1 - d²)^n."""
    return 1.0 - (1.0 - d * d) ** n


def crossover(xs, ys_sparse, ys_dense):
    """Densidad (interpolación log-log) a la que el método disperso deja de ganar."""
    for (x0, s0, d0), (x1, s1, d1) in zip(zip(xs, ys_sparse, ys_dense),
                                          list(zip(xs, ys_sparse, ys_dense))[1:]):
        r0, r1 = math.log(s0 / d0), math.log(s1 / d1)
        if r0 < 0 <= r1:
            t = -r0 / (r1 - r0)
            return math.exp(math.log(x0) + t * (math.log(x1) - math.log(x0)))
    return None


def sparse_report(summary, failures, rows, out_dir: Path) -> str:
    configs = sort_configs({s["config"] for s in summary})
    ns = sorted({s["n"] for s in summary})
    dense_cfgs = [c for c in configs if c != "csr"]
    best_dense = "blocked" if "blocked" in configs else (dense_cfgs[0] if dense_cfgs else None)
    L = ["# Resumen de resultados - Parte B (dispersas)", ""]
    L.append("Entradas: `data_sparse/`, no-ceros con posiciones uniformes e independientes "
             "(densidad = % de no-ceros), valores en (0, 1]. Mismas matrices lógicas (mismo "
             "fichero) para todos los métodos. Mediana de las repeticiones. «csr» = solo el "
             "producto CSR x CSR (la conversión denso -> CSR de A y B se mide aparte); "
             "«csr + conv.» = producto + conversión.\n")
    crossovers = []
    for n in ns:
        cs = {s["density_pct"]: s for s in series(summary, "csr") if s["n"] == n}
        ds = {c: {s["density_pct"]: s for s in series(summary, c) if s["n"] == n} for c in dense_cfgs}
        dens = sorted(set(cs) | set().union(*[set(v) for v in ds.values()]) if ds else set(cs))
        L += [f"## n = {n}", ""]
        L.append("| densidad (%) | nnz(A) | nnz(C) | densidad C (%) | esperada (%) | csr | conversión | "
                 "csr + conv. | " + " | ".join(style_for(c)["label"] for c in dense_cfgs) +
                 (f" | {best_dense} / csr | {best_dense} / (csr + conv.)" if best_dense and cs else "") + " |")
        L.append("|" + "---:|" * (8 + len(dense_cfgs) + (2 if best_dense and cs else 0)))
        for d in dens:
            any_s = cs.get(d) or next(ds[c][d] for c in dense_cfgs if d in ds[c])
            c_ = cs.get(d)
            cells = [fmt_pct(d), str(int(any_s["nnz_a"])), str(int(any_s["nnz_c"])),
                     fmt(any_s["density_c_pct"], 3),
                     fmt(100 * expected_output_density(n, any_s["density_a_pct"] / 100), 3),
                     fmt_s(c_["median_s"]) if c_ else "-", fmt_s(c_["convert_s"]) if c_ else "-",
                     fmt_s(c_["total_with_convert_s"]) if c_ else "-"]
            cells += [fmt_s(ds[c][d]["median_s"]) if d in ds[c] else "-" for c in dense_cfgs]
            if best_dense and cs:
                bd = ds.get(best_dense, {}).get(d)
                cells.append(f"{bd['median_s'] / c_['median_s']:.3g}x" if bd and c_ else "-")
                cells.append(f"{bd['median_s'] / c_['total_with_convert_s']:.3g}x" if bd and c_ else "-")
            L.append("| " + " | ".join(cells) + " |")
        L.append("")
        if best_dense and cs and best_dense in ds:
            common = [d for d in sorted(cs) if d in ds[best_dense]]
            if len(common) >= 2:
                x = crossover(common, [cs[d]["median_s"] for d in common],
                              [ds[best_dense][d]["median_s"] for d in common])
                xc = crossover(common, [cs[d]["total_with_convert_s"] for d in common],
                               [ds[best_dense][d]["median_s"] for d in common])
                crossovers.append((n, x, xc))
                L.append(f"- Densidad de cruce csr = {best_dense} (interpolación log-log): "
                         f"solo producto **{fmt(x, 3)} %**; con conversión **{fmt(xc, 3)} %** "
                         f"(«-» = no hay cruce en el rango medido).")
        L.append("")

    L += ["## Memoria (MB)", ""]
    L.append("«estructuras» = bytes de los datos del método: densos 3·8n²; csr = CSR de A, B y C "
             "(12 B por no-cero + 8(n+1) B). «WS tras multiplicar» = working set actual del "
             "proceso justo después del producto (en csr, las densas de entrada ya liberadas). "
             "«pico» = pico del working set del proceso (incluye la lectura de los ficheros densos).\n")
    L.append("| n | densidad (%) | csr: estructuras | csr: WS tras multiplicar | csr: pico | "
             "denso: estructuras | denso: WS tras multiplicar | denso: pico |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s in sorted(series(summary, "csr"), key=lambda s: (s["n"], s["density_pct"])):
        bd = next((x for x in series(summary, best_dense) if x["n"] == s["n"]
                   and x["density_pct"] == s["density_pct"]), None) if best_dense else None
        L.append(f"| {s['n']} | {fmt_pct(s['density_pct'])} | {fmt(s['object_model_mb'], 4)} | "
                 f"{fmt(s['wset_after_mb'], 4)} | {fmt(s['proc_peak_mb'], 4)} | "
                 f"{fmt(bd['object_model_mb'], 4) if bd else '-'} | "
                 f"{fmt(bd['wset_after_mb'], 4) if bd else '-'} | {fmt(bd['proc_peak_mb'], 4) if bd else '-'} |")
    L += ["", "## Corrección", "", *correctness_lines(summary), ""]
    for c in configs:
        L += [f"## {style_for(c)['label']} - `{c}`", "", *config_table_lines(summary, c)]
        L += ["### Límites", "", *limits_lines(c, rows, failures), ""]

    # ----- gráficas
    plots = out_dir / "plots"
    ncols = len(ns)
    fig, axes = _new_fig(w=4.6 * ncols + 0.6, h=4.3, ncols=ncols)
    axes = np.atleast_1d(axes)
    for ax, n in zip(axes, ns):
        _prep_axes(ax, "density of A and B (% nonzeros, log scale)",
                   "time per multiplication (s, log scale)" if ax is axes[0] else "", f"n = {n}")
        for c in configs:
            st = style_for(c)
            s = [r for r in series(summary, c) if r["n"] == n]
            s.sort(key=lambda r: r["density_pct"])
            if not s:
                continue
            x = [r["density_pct"] for r in s]
            ax.plot(x, [r["median_s"] for r in s], color=st["color"], marker=st["marker"],
                    markersize=4, linewidth=1.5, label=st["label"] + (" - product only" if c == "csr" else ""))
            if c == "csr":
                ax.plot(x, [r["total_with_convert_s"] for r in s], color=st["color"], marker=st["marker"],
                        markersize=3.5, linewidth=1.2, linestyle=(0, (4, 2)), mfc="none",
                        label="CSR - product + conversion")
        ax.set_xscale("log")
        ax.set_yscale("log")
        _xticks_density(ax, sorted({r["density_pct"] for r in summary if r["n"] == n}))
    _legend(axes[0], loc="lower right", fontsize=7.8)
    fig.suptitle("Sparse (CSR) vs. dense methods on the same sparse inputs",
                 x=0.01, ha="left", fontsize=10.5, color=INK)
    _save(fig, plots / "sparse_time_vs_density.png")

    if best_dense and "csr" in configs:
        fig, ax = _new_fig(h=4.2)
        _prep_axes(ax, "density of A and B (% nonzeros, log scale)",
                   f"time({best_dense}) / time(CSR)  (log scale)",
                   "Advantage of CSR over the best dense method (> 1: CSR is faster)")
        colors = ["#6250d6", "#e87ba4", "#eda100"]
        for idx, n in enumerate(ns):
            cs = {s["density_pct"]: s for s in series(summary, "csr") if s["n"] == n}
            bd = {s["density_pct"]: s for s in series(summary, best_dense) if s["n"] == n}
            common = sorted(set(cs) & set(bd))
            if not common:
                continue
            col = colors[idx % len(colors)]
            ax.plot(common, [bd[d]["median_s"] / cs[d]["median_s"] for d in common], color=col,
                    marker="os^"[idx % 3], markersize=4, linewidth=1.5, label=f"n = {n}, product only")
            ax.plot(common, [bd[d]["median_s"] / cs[d]["total_with_convert_s"] for d in common],
                    color=col, marker="os^"[idx % 3], markersize=3.5, linewidth=1.2,
                    linestyle=(0, (4, 2)), mfc="none", label=f"n = {n}, product + conversion")
        ax.axhline(1.0, color=INK_2, linewidth=0.9)
        ax.set_xscale("log")
        ax.set_yscale("log")
        _xticks_density(ax, sorted({r["density_pct"] for r in summary}))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}x"))
        _legend(ax, loc="upper right", fontsize=7.8)
        _save(fig, plots / "sparse_speedup_vs_density.png")

    fig, ax = _new_fig(h=4.2)
    _prep_axes(ax, "density of A and B (% nonzeros, log scale)", "density of C = A x B (%, log scale)",
               "Output fill-in: the product is much denser than its inputs")
    colors = ["#6250d6", "#e87ba4", "#eda100"]
    for idx, n in enumerate(ns):
        s = sorted({r["density_pct"]: r for r in summary if r["n"] == n}.values(),
                   key=lambda r: r["density_pct"])
        x = [r["density_pct"] for r in s]
        ax.plot(x, [max(r["density_c_pct"], 1e-4) for r in s], color=colors[idx % 3],
                marker="os^"[idx % 3], markersize=4.5, linewidth=0, label=f"n = {n}: measured")
        xx = np.geomspace(min(x), max(x), 80)
        ax.plot(xx, [100 * expected_output_density(n, d / 100) for d in xx], color=colors[idx % 3],
                linewidth=1.1, alpha=0.7, label=f"n = {n}: 1 - (1 - d²)^n")
    ax.plot([min(x), max(x)], [min(x), max(x)], color=INK_2, linestyle=(0, (4, 3)), linewidth=0.9,
            label="same density as the inputs")
    ax.set_xscale("log")
    ax.set_yscale("log")
    _xticks_density(ax, sorted({r["density_pct"] for r in summary}))
    _legend(ax, loc="lower right", fontsize=7.8)
    _save(fig, plots / "sparse_output_fill.png")

    if "csr" in configs:
        fig, ax = _new_fig(h=4.2)
        _prep_axes(ax, "density of A and B (% nonzeros, log scale)", "MB (10^6 bytes, log scale)",
                   "Memory: CSR structures vs. dense storage")
        for idx, n in enumerate(ns):
            s = sorted((r for r in series(summary, "csr") if r["n"] == n), key=lambda r: r["density_pct"])
            col = colors[idx % 3]
            x = [r["density_pct"] for r in s]
            ax.plot(x, [r["object_model_mb"] for r in s], color=col, marker="os^"[idx % 3],
                    markersize=4, linewidth=1.5, label=f"n = {n}: CSR of A, B, C (model)")
            ax.plot(x, [r["wset_after_mb"] for r in s], color=col, marker="os^"[idx % 3],
                    markersize=3.5, linewidth=1.1, linestyle=(0, (4, 2)), mfc="none",
                    label=f"n = {n}: CSR process working set after the product")
            ax.axhline(3 * 8 * n * n / 1e6, color=col, linewidth=0.9, linestyle=(0, (1, 2)),
                       label=f"n = {n}: dense 3 x 8 x n²")
        ax.set_xscale("log")
        ax.set_yscale("log")
        _xticks_density(ax, sorted({r["density_pct"] for r in summary}))
        _legend(ax, loc="lower right", fontsize=7.3)
        _save(fig, plots / "sparse_memory.png")

        fig, ax = _new_fig(h=4.0)
        _prep_axes(ax, "density of A and B (% nonzeros, log scale)",
                   "ns per expected useful product (log scale)",
                   "CSR cost per useful multiply-add, time / (n³ d²)")
        for idx, n in enumerate(ns):
            s = sorted((r for r in series(summary, "csr") if r["n"] == n), key=lambda r: r["density_pct"])
            x = [r["density_pct"] for r in s]
            y = [r["median_s"] * 1e9 / (n**3 * (r["density_a_pct"] / 100) ** 2) for r in s]
            ax.plot(x, y, color=colors[idx % 3], marker="os^"[idx % 3], markersize=4, linewidth=1.5,
                    label=f"n = {n}")
        for c in dense_cfgs:
            dvals = [r["ns_per_inner_iter"] for r in series(summary, c)]
            if dvals:
                ax.axhline(float(np.median(dvals)), color=style_for(c)["color"], linewidth=1.0,
                           linestyle=(0, (4, 3)), label=f"{style_for(c)['label']}: ns per n³ iteration")
        ax.set_xscale("log")
        ax.set_yscale("log")
        _xticks_density(ax, sorted({r["density_pct"] for r in summary}))
        _legend(ax, loc="upper right", fontsize=7.8)
        _save(fig, plots / "sparse_cost_per_product.png")
    return "\n".join(L)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--csv", type=Path, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--kind", choices=["auto", "dense", "blocks", "sparse"], default="auto")
    parser.add_argument("--fit-min-n", type=int, default=100,
                        help="menor n del ajuste log-log (evita el régimen dominado por costes fijos)")
    parser.add_argument("--p1-summary", type=Path, default=None,
                        help="summary.csv de la Práctica 1 para comparar el baseline")
    args = parser.parse_args(argv)

    missing = [p for p in args.csv if not p.exists()]
    if missing:
        sys.exit(f"No existe {missing[0]}. Ejecuta primero scripts/run_benchmarks.py")
    rows = load_rows(args.csv)
    if not rows:
        sys.exit("Los CSV no contienen medidas")
    kind = args.kind
    if kind == "auto":
        if any(r["density_pct"] is not None for r in rows):
            kind = "sparse"
        elif all(r["config"].startswith("blocked-") for r in rows):
            kind = "blocks"
        else:
            kind = "dense"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary, failures = summarise(rows)
    if not summary:
        sys.exit("No hay ninguna medida con status OK que resumir.")
    write_summary_csv(summary, args.out_dir / "summary.csv")
    if kind == "dense":
        text = dense_report(summary, failures, rows, args.fit_min_n, args.p1_summary, args.out_dir)
    elif kind == "blocks":
        text = blocks_report(summary, failures, rows, args.out_dir)
    else:
        text = sparse_report(summary, failures, rows, args.out_dir)
    (args.out_dir / "summary.md").write_text(text, encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):  # consola de Windows redirigida (cp1252)
        sys.stdout.reconfigure(errors="replace")
    print(text)
    print("Generado:", args.out_dir / "summary.csv", args.out_dir / "summary.md",
          *sorted(str(p) for p in (args.out_dir / "plots").glob("*.png")), sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
