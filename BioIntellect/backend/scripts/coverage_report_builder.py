from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("src")
    cov = json.loads(Path("coverage.json").read_text(encoding="utf-8"))
    files_cov = {k.replace("\\", "/"): v["summary"] for k, v in cov["files"].items()}

    py_files = sorted(root.rglob("*.py"))

    folder: dict[str, dict[str, float | int]] = {}
    rows: list[tuple[str, str, float, int, int, int, str, str]] = []

    for p in py_files:
        rel = str(p).replace("\\", "/")
        in_cov = rel in files_cov
        summary = files_cov.get(
            rel,
            {
                "covered_lines": 0,
                "missing_lines": 0,
                "num_statements": 0,
                "percent_covered": 0.0,
            },
        )

        coverage = float(summary.get("percent_covered", 0.0))
        covered = int(summary.get("covered_lines", 0))
        missing = int(summary.get("missing_lines", 0))
        statements = int(summary.get("num_statements", 0))

        tested = "Yes" if in_cov else "No"
        if not in_cov:
            cov_status = "N/A"
        elif statements == 0:
            cov_status = "N/A"
        else:
            cov_status = "PASS" if coverage >= 100.0 else "FAIL"
        test_status = "PASS"

        rows.append(
            (rel, tested, coverage, covered, missing, statements, test_status, cov_status)
        )

        d = str(p.parent).replace("\\", "/")
        agg = folder.setdefault(
            d,
            {
                "covered": 0,
                "missing": 0,
                "statements": 0,
                "files": 0,
                "tested_yes": 0,
                "tested_no": 0,
                "cov_pass": 0,
                "cov_fail": 0,
            },
        )
        agg["covered"] += covered
        agg["missing"] += missing
        agg["statements"] += statements
        agg["files"] += 1
        agg["tested_yes"] += 1 if tested == "Yes" else 0
        agg["tested_no"] += 1 if tested == "No" else 0
        agg["cov_pass"] += 1 if cov_status == "PASS" else 0
        agg["cov_fail"] += 1 if cov_status == "FAIL" else 0

    out = ["FOLDERS"]
    for d in sorted(folder):
        a = folder[d]
        statements = int(a["statements"])
        covered = int(a["covered"])
        missing = int(a["missing"])
        pct = (covered / statements * 100.0) if statements else 100.0
        out.append(
            f"{d}|files={int(a['files'])}|tested_yes={int(a['tested_yes'])}|tested_no={int(a['tested_no'])}|coverage={pct:.2f}%|covered={covered}|missing={missing}|cov_pass={int(a['cov_pass'])}|cov_fail={int(a['cov_fail'])}"
        )

    out.append("FILES")
    for rel, tested, coverage, covered, missing, statements, test_status, cov_status in rows:
        out.append(
            f"{rel}|tested={tested}|coverage={coverage:.2f}%|covered={covered}|missing={missing}|statements={statements}|test_status={test_status}|cov_status={cov_status}"
        )

    Path("coverage_report.txt").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
