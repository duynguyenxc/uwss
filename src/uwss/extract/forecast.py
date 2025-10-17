from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np


@dataclass
class ForecastPoint:
	sequence_id: str
	horizon: float  # days
	pred: float


def _load_norm_series(series_norm_path: Path) -> dict:
	by_seq = {}
	with series_norm_path.open("r", encoding="utf-8") as f:
		for line in f:
			if not line.strip():
				continue
			rec = json.loads(line)
			seq = rec["sequence_id"]
			by_seq.setdefault(seq, []).append(rec)
	return by_seq


def _linear_fit(xs: np.ndarray, ys: np.ndarray) -> Tuple[float, float]:
	# y = a * x + b
	A = np.vstack([xs, np.ones_like(xs)]).T
	a, b = np.linalg.lstsq(A, ys, rcond=None)[0]
	return float(a), float(b)


def forecast_linear(series_norm_path: Path, out_path: Path, horizon_days: float = 30.0) -> int:
	by_seq = _load_norm_series(series_norm_path)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	n = 0
	with out_path.open("w", encoding="utf-8") as f:
		for seq_id, rows in by_seq.items():
			rows = sorted(rows, key=lambda r: r.get("time_days", 0.0))
			xs = np.array([float(r.get("time_days", 0.0)) for r in rows], dtype=float)
			ys = np.array([float(r.get("value_norm", r.get("value", 0.0))) for r in rows], dtype=float)
			if len(xs) < 2:
				continue
			a, b = _linear_fit(xs, ys)
			x_next = xs[-1] + horizon_days
			y_pred = a * x_next + b
			f.write(json.dumps({
				"sequence_id": seq_id,
				"horizon_days": horizon_days,
				"pred": float(y_pred)
			}) + "\n")
			n += 1
	return n
