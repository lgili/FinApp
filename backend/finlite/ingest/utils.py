"""Ingestion utilities (file hashing, parsing helpers)."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_amount(text: str) -> Decimal:
    """Parse Brazilian/US formatted amounts, stripping currency symbols.

    Supported examples:
    - "12.34"
    - "12,34"
    - "1.234,56"
    - "R$ 1.234,56"
    - "-1.234,56"
    """
    raw = text.strip()
    raw = raw.replace("R$", "").strip()
    # Remove thousands separator for BR format
    if "," in raw and "." in raw and raw.rfind(",") > raw.rfind("."):
        raw = raw.replace(".", "")
    # Replace decimal comma with dot
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    # Remove any spaces
    raw = raw.replace(" ", "")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {text}") from exc


def read_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys to lowercase to allow case-insensitive alias matching
            norm = {
                (k.strip().lower() if isinstance(k, str) else k): (
                    v.strip() if isinstance(v, str) else v
                )
                for k, v in row.items()
            }
            # Handle extra columns caused by decimal comma (e.g., "-123,45" becomes ["-123", "45"]).
            if None in norm and isinstance(norm[None], list) and norm[None]:
                if "valor" in norm and isinstance(norm["valor"], str):
                    extra = ",".join(norm[None])
                    norm["valor"] = f"{norm['valor']},{extra}"
                # Remove the placeholder key from the dict
                norm.pop(None, None)
            yield norm
