#!/usr/bin/env python
"""Prepare MTS-Dialog CSV files into JSONL training files for SFT.

Output row format:
{"instruction": "...", "input": "...", "output": "..."}
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

EXPECTED_COLUMNS: Tuple[str, ...] = ("ID", "section_header", "section_text", "dialogue")
DEFAULT_ENCODING = "utf-8"
DEFAULT_TRAIN_CSV = (
    "Augmented-Data/MTS-Dialog-Augmented-TrainingSet-3-FR-and-ES-3603-Pairs-final.csv"
)
DEFAULT_VAL_CSV = "Main-Dataset/MTS-Dialog-ValidationSet.csv"
DEFAULT_TEST_CSV = "Main-Dataset/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv"
DEFAULT_TRAIN_OUT = "medical_train.jsonl"
DEFAULT_VAL_OUT = "medical_val.jsonl"
DEFAULT_TEST_OUT = "medical_test.jsonl"
DEFAULT_STATS_OUT = "medical_dataset_stats.json"

# Normalized headers from MTS-Dialog README.
HEADER_MAP: Dict[str, str] = {
    "FAM/SOCHX": "Family History / Social History",
    "GENHX": "History of Present Illness",
    "PASTMEDICALHX": "Past Medical History",
    "CC": "Chief Complaint",
    "PASTSURGICAL": "Past Surgical History",
    "ALLERGY": "Allergy",
    "ROS": "Review of Systems",
    "MEDICATIONS": "Medications",
    "ASSESSMENT": "Assessment",
    "EXAM": "Exam",
    "DIAGNOSIS": "Diagnosis",
    "DISPOSITION": "Disposition",
    "PLAN": "Plan",
    "EDCOURSE": "Emergency Department Course",
    "IMMUNIZATIONS": "Immunizations",
    "IMAGING": "Imaging",
    "GYNHX": "Gynecologic History",
    "PROCEDURES": "Procedures",
    "OTHER_HISTORY": "Other History",
    "LABS": "Labs",
}

INLINE_SPACES_RE = re.compile(r"[ \t\f\v]+")
ANY_SPACES_RE = re.compile(r"\s+")


@dataclass
class SplitResult:
    name: str
    source_csv: Path
    records: List[Dict[str, str]]
    keys: Set[Tuple[str, str, str]]
    stats: Dict[str, object]


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_mts_root = script_dir / "fine-tuning data" / "chat data" / "MTS-Dialog"

    parser = argparse.ArgumentParser(
        description="Prepare MTS-Dialog CSV files into JSONL files for Phi-3.5 fine-tuning."
    )
    parser.add_argument("--mts-root", type=Path, default=default_mts_root)
    parser.add_argument("--train-csv", default=DEFAULT_TRAIN_CSV)
    parser.add_argument("--val-csv", default=DEFAULT_VAL_CSV)
    parser.add_argument("--test-csv", default=DEFAULT_TEST_CSV)
    parser.add_argument("--out-dir", type=Path, default=script_dir)
    parser.add_argument("--train-out", default=DEFAULT_TRAIN_OUT)
    parser.add_argument("--val-out", default=DEFAULT_VAL_OUT)
    parser.add_argument("--test-out", default=DEFAULT_TEST_OUT)
    parser.add_argument(
        "--stats-out",
        default=None,
        help=(
            "Stats JSON path (relative to --out-dir when not absolute). "
            "Default: medical_dataset_stats.json in non-dry-run; omitted in dry-run unless provided."
        ),
    )
    parser.add_argument("--encoding", default=DEFAULT_ENCODING)
    parser.add_argument("--allow-overlap", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False)
    return parser.parse_args()


def resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path)


def clean_text(value: str) -> str:
    text = (value or "").replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [INLINE_SPACES_RE.sub(" ", line).strip() for line in text.split("\n")]

    compact_lines: List[str] = []
    previous_blank = False
    for line in lines:
        if line == "":
            if not previous_blank:
                compact_lines.append("")
            previous_blank = True
            continue
        compact_lines.append(line)
        previous_blank = False

    return "\n".join(compact_lines).strip()


def normalize_header(value: str) -> str:
    return clean_text(value).upper()


def normalize_for_key(value: str) -> str:
    return ANY_SPACES_RE.sub(" ", clean_text(value)).strip()


def validate_csv_schema(fieldnames: Sequence[str] | None, csv_path: Path) -> None:
    if fieldnames is None:
        raise ValueError(f"Schema validation failed for {csv_path}: header row is missing.")

    fields = tuple(fieldnames)
    if fields != EXPECTED_COLUMNS:
        raise ValueError(
            "Schema validation failed for "
            f"{csv_path}: expected columns exactly {EXPECTED_COLUMNS}, got {fields}."
        )


def build_instruction(header_display: str) -> str:
    return (
        f"Generate the {header_display} clinical note section from the dialogue. "
        "Use only facts from the dialogue, keep medical meaning faithful, "
        "and do not hallucinate unsupported details."
    )


def build_input(header_display: str, dialogue: str) -> str:
    return f"Section Header: {header_display}\nDialogue:\n{dialogue}"


def percentile(sorted_values: Sequence[int], percent: float) -> int:
    if not sorted_values:
        return 0
    rank = max(1, math.ceil((percent / 100.0) * len(sorted_values)))
    idx = min(rank - 1, len(sorted_values) - 1)
    return sorted_values[idx]


def summarize_lengths(lengths: Iterable[int]) -> Dict[str, float | int]:
    values = list(lengths)
    if not values:
        return {"count": 0, "min": 0, "p50": 0, "p95": 0, "max": 0, "mean": 0.0}
    sorted_values = sorted(values)
    mean = sum(sorted_values) / len(sorted_values)
    return {
        "count": len(sorted_values),
        "min": sorted_values[0],
        "p50": percentile(sorted_values, 50),
        "p95": percentile(sorted_values, 95),
        "max": sorted_values[-1],
        "mean": round(mean, 2),
    }


def prepare_split(split_name: str, csv_path: Path, encoding: str) -> SplitResult:
    raw_rows = 0
    dropped = Counter()
    headers = Counter()
    records: List[Dict[str, str]] = []
    keys: Set[Tuple[str, str, str]] = set()

    dialogue_lengths: List[int] = []
    output_lengths: List[int] = []
    instruction_lengths: List[int] = []
    input_lengths: List[int] = []

    with csv_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        validate_csv_schema(reader.fieldnames, csv_path)

        for row_idx, row in enumerate(reader, start=2):
            raw_rows += 1
            source_id = clean_text(row.get("ID", ""))
            header_code = normalize_header(row.get("section_header", ""))
            dialogue = clean_text(row.get("dialogue", ""))
            section_text = clean_text(row.get("section_text", ""))

            if not source_id:
                dropped["missing_id"] += 1
                continue
            if not header_code:
                dropped["missing_section_header"] += 1
                continue
            if header_code not in HEADER_MAP:
                raise ValueError(
                    f"[{split_name}] Unknown section_header '{row.get('section_header')}' "
                    f"at {csv_path}:{row_idx}."
                )
            if not dialogue:
                dropped["empty_dialogue"] += 1
                continue
            if not section_text:
                dropped["empty_section_text"] += 1
                continue

            dedup_key = (
                header_code,
                normalize_for_key(dialogue),
                normalize_for_key(section_text),
            )
            if dedup_key in keys:
                dropped["duplicate_in_split"] += 1
                continue

            keys.add(dedup_key)

            header_display = f"{header_code} ({HEADER_MAP[header_code]})"
            instruction = build_instruction(header_display)
            input_text = build_input(header_display, dialogue)

            record = {"instruction": instruction, "input": input_text, "output": section_text}
            records.append(record)

            headers[header_code] += 1
            dialogue_lengths.append(len(dialogue))
            output_lengths.append(len(section_text))
            instruction_lengths.append(len(instruction))
            input_lengths.append(len(input_text))

    stats: Dict[str, object] = {
        "source_csv": str(csv_path),
        "raw_rows": raw_rows,
        "kept_rows": len(records),
        "dropped_rows": sum(dropped.values()),
        "dropped_reasons": dict(sorted(dropped.items())),
        "duplicate_stats": {
            "removed_duplicates": dropped.get("duplicate_in_split", 0),
            "unique_after_dedup": len(records),
        },
        "header_distribution": dict(sorted(headers.items())),
        "length_stats": {
            "dialogue_chars": summarize_lengths(dialogue_lengths),
            "output_chars": summarize_lengths(output_lengths),
            "instruction_chars": summarize_lengths(instruction_lengths),
            "input_chars": summarize_lengths(input_lengths),
        },
    }
    return SplitResult(name=split_name, source_csv=csv_path, records=records, keys=keys, stats=stats)


def overlap_fingerprint(keys: Set[Tuple[str, str, str]], limit: int = 3) -> List[str]:
    fingerprints: List[str] = []
    for key in list(keys)[:limit]:
        digest = hashlib.sha1("||".join(key).encode("utf-8")).hexdigest()[:12]
        fingerprints.append(digest)
    return fingerprints


def build_overlap_stats(
    train: SplitResult, val: SplitResult, test: SplitResult
) -> Tuple[Dict[str, object], Dict[str, int]]:
    pairs = [
        ("train_val", train.keys, val.keys),
        ("train_test", train.keys, test.keys),
        ("val_test", val.keys, test.keys),
    ]

    overlaps: Dict[str, object] = {}
    counts: Dict[str, int] = {}
    for name, left, right in pairs:
        intersection = left & right
        count = len(intersection)
        counts[name] = count
        overlaps[name] = {
            "count": count,
            "sample_fingerprints": overlap_fingerprint(intersection),
        }
    overlaps["total_overlaps"] = sum(counts.values())
    return overlaps, counts


def write_jsonl(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def print_summary(train: SplitResult, val: SplitResult, test: SplitResult, overlaps: Dict[str, object]) -> None:
    print("Preparation summary:")
    for split in (train, val, test):
        split_stats = split.stats
        print(
            f"- {split.name}: raw={split_stats['raw_rows']} "
            f"kept={split_stats['kept_rows']} dropped={split_stats['dropped_rows']} "
            f"duplicates_removed={split_stats['duplicate_stats']['removed_duplicates']}"
        )
    print(
        "- overlap counts: "
        f"train_val={overlaps['train_val']['count']}, "
        f"train_test={overlaps['train_test']['count']}, "
        f"val_test={overlaps['val_test']['count']}"
    )


def main() -> None:
    args = parse_args()

    mts_root = args.mts_root.resolve()
    out_dir = args.out_dir.resolve()

    train_csv = resolve_path(mts_root, args.train_csv).resolve()
    val_csv = resolve_path(mts_root, args.val_csv).resolve()
    test_csv = resolve_path(mts_root, args.test_csv).resolve()

    for csv_path in (train_csv, val_csv, test_csv):
        if not csv_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    train_out = resolve_path(out_dir, args.train_out).resolve()
    val_out = resolve_path(out_dir, args.val_out).resolve()
    test_out = resolve_path(out_dir, args.test_out).resolve()

    if args.stats_out is None:
        stats_out = None if args.dry_run else resolve_path(out_dir, DEFAULT_STATS_OUT).resolve()
    else:
        stats_out = resolve_path(out_dir, args.stats_out).resolve()

    print("Input files:")
    print(f"- train: {train_csv}")
    print(f"- val:   {val_csv}")
    print(f"- test:  {test_csv}")
    print(f"- encoding: {args.encoding}")

    train = prepare_split("train", train_csv, args.encoding)
    val = prepare_split("val", val_csv, args.encoding)
    test = prepare_split("test", test_csv, args.encoding)

    overlap_stats, overlap_counts = build_overlap_stats(train, val, test)
    print_summary(train, val, test, overlap_stats)

    overlapping_pairs = {name: count for name, count in overlap_counts.items() if count > 0}
    if overlapping_pairs and not args.allow_overlap:
        pairs_text = ", ".join(f"{pair}={count}" for pair, count in sorted(overlapping_pairs.items()))
        raise RuntimeError(
            "Cross-split overlap detected and --allow-overlap is false. "
            f"Overlaps: {pairs_text}."
        )

    stats_payload: Dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "mts_root": str(mts_root),
            "train_csv": str(train_csv),
            "val_csv": str(val_csv),
            "test_csv": str(test_csv),
            "out_dir": str(out_dir),
            "train_out": str(train_out),
            "val_out": str(val_out),
            "test_out": str(test_out),
            "stats_out": str(stats_out) if stats_out is not None else None,
            "encoding": args.encoding,
            "allow_overlap": args.allow_overlap,
            "dry_run": args.dry_run,
        },
        "splits": {
            "train": train.stats,
            "val": val.stats,
            "test": test.stats,
        },
        "cross_split_overlap": overlap_stats,
    }

    if args.dry_run:
        print("Dry-run enabled: dataset files were not written.")
        if stats_out is not None:
            write_json(stats_out, stats_payload)
            print(f"Stats written: {stats_out}")
        return

    write_jsonl(train_out, train.records)
    write_jsonl(val_out, val.records)
    write_jsonl(test_out, test.records)
    if stats_out is not None:
        write_json(stats_out, stats_payload)

    print("Output files:")
    print(f"- train jsonl: {train_out}")
    print(f"- val jsonl:   {val_out}")
    print(f"- test jsonl:  {test_out}")
    if stats_out is not None:
        print(f"- stats json:  {stats_out}")


if __name__ == "__main__":
    main()
