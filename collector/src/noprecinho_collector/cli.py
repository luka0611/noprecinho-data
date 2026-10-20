"""`noprecinho probe <name>` — Milestone 0 probes. Meant to run in GitHub Actions (probe.yml), never unattended on a PC.

Exit codes: 0 ok, 2 blocked (the source refused — stop and alert the owner), 3 budget exhausted.
Writes `blocked=true|false` and `reason=...` to $GITHUB_OUTPUT and Markdown to $GITHUB_STEP_SUMMARY when present.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .pdh_client import Blocked, BudgetExhausted, PdhClient
from .probes import PROBES, Probe


def _append(env: str, text: str) -> None:
    path = os.environ.get(env)
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)


def _request_table(c: PdhClient) -> list[str]:
    rows = ["", "| # | method | path | status | ms | total | note |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(c.log, 1):
        rows.append(f"| {i} | {r.method} | {r.path} | {r.status} | {r.ms} | {r.total if r.total is not None else ''} | {r.note} |")
    return rows


def cmd_probe(args: argparse.Namespace) -> int:
    if os.environ.get("COLLECT_ENABLED", "true").lower() == "false":
        print("COLLECT_ENABLED=false — kill switch on, nothing done.")
        _append("GITHUB_STEP_SUMMARY", "Kill switch on (`COLLECT_ENABLED=false`); no requests made.\n")
        return 0
    inputs = {k: v for k, v in (("gtin", args.gtin), ("cnpj", args.cnpj)) if v}
    status, reason = 0, ""
    with PdhClient(delay_s=args.delay, max_requests=args.max_requests) as c:
        p = Probe(c, Path(args.out) / args.name, inputs)
        try:
            PROBES[args.name](p)
        except Blocked as e:
            status, reason = 2, f"blocked: {e}"
        except BudgetExhausted as e:
            status, reason = 3, f"budget: {e}"
        md = [f"## probe `{args.name}`", "", *p.md]
        if reason:
            md += ["", f"**STOPPED — {reason}**"]
        md += _request_table(c) + [f"", f"requests made: {c.requests_made}/{c.max_requests}, delay {c.delay_s:.0f} s", ""]
    text = "\n".join(md)
    print(text)
    _append("GITHUB_STEP_SUMMARY", text + "\n")
    _append("GITHUB_OUTPUT", f"blocked={'true' if status == 2 else 'false'}\nreason={reason}\n")
    return status


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="noprecinho")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe", help="run one Milestone 0 probe")
    pr.add_argument("name", choices=sorted(PROBES))
    pr.add_argument("--out", default="probe-out")
    pr.add_argument("--gtin", default="")
    pr.add_argument("--cnpj", default="")
    pr.add_argument("--delay", type=float, default=float(os.environ.get("DELAY_S", "25")))
    pr.add_argument("--max-requests", type=int, default=int(os.environ.get("MAX_REQUESTS", "10")))
    args = ap.parse_args(argv)
    return cmd_probe(args)


if __name__ == "__main__":
    sys.exit(main())
