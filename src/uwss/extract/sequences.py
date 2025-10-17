from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import fitz  # PyMuPDF


TIME_RE = re.compile(r"(?P<t>\d+(?:[\.,]\d+)?)\s*(?P<u>days?|months?|weeks?|hours?|cycles?|years?|mins?|minutes?)\b", re.IGNORECASE)
VAL_RE = re.compile(r"(?P<v>[-+]?\d+(?:[\.,]\d+)?)(?:\s*(?P<vu>mV|V|A/m\^2|µA/cm\^2|mm|µm|%)\b)?")


@dataclass
class SequencePoint:
    doc_path: str
    page: int
    sequence_id: str
    time_value: float
    time_unit: str
    value: float
    value_unit: Optional[str]
    variable: Optional[str] = None


def _norm_num(s: str) -> float:
    return float(s.replace(",", "."))


def extract_sequences_from_text(text: str, doc_path: str, page: int) -> List[SequencePoint]:
    points: List[SequencePoint] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Simple heuristic: for each line, find time then the first value on same/next line
    for i, line in enumerate(lines):
        t_match = TIME_RE.search(line)
        if not t_match:
            continue
        # Search for value on the same line first
        tail = line[t_match.end():]
        v_match = VAL_RE.search(tail)
        if not v_match and i + 1 < len(lines):
            v_match = VAL_RE.search(lines[i + 1])
        if not v_match:
            continue
        try:
            tval = _norm_num(t_match.group("t"))
            tun = t_match.group("u").lower()
            vval = _norm_num(v_match.group("v"))
            vun = v_match.group("vu")
        except Exception:
            continue
        seq_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_path}:{page}"))
        # Simple variable tagging
        text_lower = (line + " " + (lines[i + 1] if i + 1 < len(lines) else "")).lower()
        variable = None
        if any(k in text_lower for k in ["potential", "half-cell", "mV"]):
            variable = "half_cell_potential"
        elif any(k in text_lower for k in ["mass loss", "weight loss", "%"]):
            variable = "mass_loss"
        elif any(k in text_lower for k in ["crack width", "mm", "µm"]):
            variable = "crack_width"
        points.append(SequencePoint(doc_path=doc_path, page=page, sequence_id=seq_id,
                                    time_value=tval, time_unit=tun, value=vval, value_unit=vun, variable=variable))
    return points


def extract_sequences_from_pdf(pdf_path: Path) -> List[SequencePoint]:
    doc = fitz.open(pdf_path)
    all_points: List[SequencePoint] = []
    try:
        for pno in range(len(doc)):
            page = doc[pno]
            text = page.get_text("text") or ""
            pts = extract_sequences_from_text(text, str(pdf_path), pno + 1)
            all_points.extend(pts)
    finally:
        doc.close()
    return all_points


def write_jsonl(points: Iterable[SequencePoint], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for pt in points:
            rec = {
                "doc_path": pt.doc_path,
                "page": pt.page,
                "sequence_id": pt.sequence_id,
                "time_value": pt.time_value,
                "time_unit": pt.time_unit,
                "value": pt.value,
                "value_unit": pt.value_unit,
                "variable": pt.variable,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def validate_jsonl(series_path: Path) -> dict:
    stats = {"total": 0, "by_unit": {}, "by_doc": {}, "by_var": {}}
    if not series_path.exists():
        return stats
    with series_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            stats["total"] += 1
            tun = rec.get("time_unit") or ""
            stats["by_unit"][tun] = stats["by_unit"].get(tun, 0) + 1
            doc = rec.get("doc_path") or ""
            stats["by_doc"][doc] = stats["by_doc"].get(doc, 0) + 1
            var = rec.get("variable") or "unknown"
            stats["by_var"][var] = stats["by_var"].get(var, 0) + 1
    return stats


# ---------------- Normalization -----------------

def _norm_time_to_days(value: float, unit: str) -> float:
    u = (unit or "").lower()
    if u in ("day", "days"):
        return value
    if u in ("week", "weeks"):
        return value * 7.0
    if u in ("month", "months"):
        return value * 30.0
    if u in ("year", "years"):
        return value * 365.0
    if u in ("hour", "hours"):
        return value / 24.0
    if u in ("cycle", "cycles"):
        # keep cycles as-is (no direct mapping); approximate as days
        return value
    return value


def _norm_value(variable: Optional[str], value: float, vunit: Optional[str]) -> Tuple[float, str]:
    var = (variable or "").lower()
    vu = (vunit or "").lower()
    # half-cell potential -> mV
    if var == "half_cell_potential":
        if vu == "v":
            return value * 1000.0, "mV"
        if vu == "mv" or vu == "":
            return value, "mV"
        return value, vu
    # crack width -> mm
    if var == "crack_width":
        if vu == "µm" or vu == "um":
            return value / 1000.0, "mm"
        if vu == "mm" or vu == "":
            return value, "mm"
        return value, vu
    # mass loss remains %
    if var == "mass_loss":
        if vu == "%" or vu == "":
            return value, "%"
        return value, vu
    return value, vu or ""


def normalize_sequences_jsonl(inp: Path, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    stats = {"written": 0}
    if not inp.exists():
        return stats
    with inp.open("r", encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            rec = json.loads(line)
            t_value = float(rec.get("time_value"))
            t_unit = rec.get("time_unit") or ""
            v_value = float(rec.get("value"))
            v_unit = rec.get("value_unit")
            variable = rec.get("variable")
            t_days = _norm_time_to_days(t_value, t_unit)
            v_norm, v_unit_norm = _norm_value(variable, v_value, v_unit)
            rec["time_days"] = t_days
            rec["value_norm"] = v_norm
            rec["value_unit_norm"] = v_unit_norm
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["written"] += 1
    return stats


