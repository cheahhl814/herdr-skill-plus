#!/usr/bin/env python3
"""herdr-batch.py — interruption-survivable batch ledger for herdr-skill+ §1.6.

One JSON file per delegation batch. One row per delegated agent. The ledger,
not the calling agent's context, is the source of truth once a batch outgrows
a single turn (context compaction, herdr restart, detach).

Standard library only (json, argparse, pathlib, datetime). Python >= 3.8.

Row fields:
  agent_name    join key — must match the herdr_agent start name (§1 step 3)
  task          one-line task description
  tier          §4.6 task tier: T0 | T1 | T2 | T3
  harness       agent kind (claude, codex, opencode, pi, ...)
  tab_id        herdr tab hosting the agent's root pane
  pane_id       herdr pane the agent runs in
  worktree      worktree path/workspace if §1 isolation applied one
  session_id    from `herdr-convo locate <pane>` (claude/codex/opencode/pi)
  convo_cursor  last-seen herdr-convo read cursor
  state         pending | working | blocked | done | idle | lost | merged
  verified      §2 output check passed (bool)
  round         §8 brainstorming: last completed round (r0/r1/r2/synthesis)

Subcommands:
  new   [--dir DIR]           create a ledger, print its path
  set   FILE --agent NAME [--field NAME=VALUE ...] [--verified BOOL]
                              create/update a row; NAME=VALUE where NAME is any
                              field except agent_name/verified
  show  FILE [--md]           print all rows (markdown table with --md)
  todo  FILE                  print rows still needing work (not verified/merged/lost)

Examples:
  python3 bin/herdr-batch.py new --dir .herdr-batch
  python3 bin/herdr-batch.py set .herdr-batch/<id>.json --agent refactor-tests \
      --field task="port test suite" --field tier=T1 --field harness=claude \
      --field tab_id=w13:t2 --field pane_id=w13:p9 \
      --field worktree=../repo-wt-refactor-tests --field state=working
  # after herdr-convo locate:
  python3 bin/herdr-batch.py set .herdr-batch/<id>.json --agent refactor-tests \
      --field session_id=abc123 --field convo_cursor=42
  python3 bin/herdr-batch.py show .herdr-batch/<id>.json --md   # relay table
"""

import argparse
import datetime
import json
import pathlib
import sys

FIELDS = (
    "task",
    "tier",
    "harness",
    "tab_id",
    "pane_id",
    "worktree",
    "session_id",
    "convo_cursor",
    "state",
    "round",
)
TERMINAL_STATES = {"merged", "lost"}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: pathlib.Path) -> dict:
    try:
        with path.open() as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: ledger not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: corrupt ledger {path}: {exc}")
    if "rows" not in data or not isinstance(data["rows"], dict):
        sys.exit(f"error: {path} is not a herdr-batch ledger (missing 'rows')")
    return data


def _save(path: pathlib.Path, data: dict) -> None:
    data["updated"] = _now()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)  # atomic-ish write; a crash never truncates the ledger


def cmd_new(args) -> None:
    directory = pathlib.Path(args.dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"batch-{stamp}.json"
    if path.exists():
        sys.exit(f"error: refusing to overwrite existing ledger {path}")
    _save(path, {"batch_id": path.stem, "created": _now(), "rows": {}})
    print(path)


def cmd_set(args) -> None:
    path = pathlib.Path(args.file).expanduser()
    data = _load(path)
    rows = data["rows"]
    row = rows.setdefault(
        args.agent,
        {"agent_name": args.agent, "state": "pending", "verified": False},
    )
    updates = dict(f.split("=", 1) for f in args.field)
    unknown = set(updates) - set(FIELDS)
    if unknown:
        sys.exit(
            f"error: unknown field(s) {sorted(unknown)}; valid: {', '.join(FIELDS)}"
        )
    row.update(updates)
    if updates.get("state") == "merged":
        row["verified"] = True  # merging implies the §2 check passed
    _save(path, data)
    print(json.dumps(row, sort_keys=True))


def cmd_show(args) -> None:
    data = _load(pathlib.Path(args.file).expanduser())
    rows = sorted(data["rows"].values(), key=lambda r: r["agent_name"])
    cols = ["agent_name", "harness", "tier", "round", "state", "verified", "pane_id",
            "tab_id", "worktree", "convo_cursor", "task"]
    if args.md:
        print("| " + " | ".join(cols) + " |")
        print("|" + "|".join([" --- "] * len(cols)) + "|")
    for row in rows:
        vals = [str(row.get(col, "")) for col in cols]
        print(("| " + " | ".join(vals) + " |") if args.md else "\t".join(vals))
    print(f"({len(rows)} agent(s); batch {data['batch_id']}, "
          f"created {data['created']}, updated {data['updated']})",
          file=sys.stderr)


def cmd_todo(args) -> None:
    data = _load(pathlib.Path(args.file).expanduser())
    open_rows = [
        row
        for row in data["rows"].values()
        if not row.get("verified") and row.get("state") not in TERMINAL_STATES
    ]
    if not open_rows:
        print("all rows verified/merged/lost — batch complete or escalated")
        return
    for row in sorted(open_rows, key=lambda r: r["agent_name"]):
        print(f"{row['agent_name']}: state={row.get('state', 'pending')} "
              f"pane={row.get('pane_id', '?')} task={row.get('task', '?')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="herdr-skill+ §1.6 batch ledger (see module docstring)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="create a new batch ledger")
    p_new.add_argument("--dir", default=".herdr-batch")
    p_new.set_defaults(func=cmd_new)

    p_set = sub.add_parser("set", help="create/update one agent row")
    p_set.add_argument("file")
    p_set.add_argument("--agent", required=True,
                       help="agent name (§1 step 3 naming = join key)")
    p_set.add_argument("--field", action="append", default=[], metavar="NAME=VALUE",
                       help=f"set one field; repeatable; names: {', '.join(FIELDS)}")
    p_set.add_argument("--verified", metavar="BOOL",
                       help="§2 output check passed (true/false)")
    p_set.set_defaults(func=cmd_set)

    p_show = sub.add_parser("show", help="print all rows")
    p_show.add_argument("file")
    p_show.add_argument("--md", action="store_true",
                        help="markdown table (for relaying to the user)")
    p_show.set_defaults(func=cmd_show)

    p_todo = sub.add_parser("todo", help="rows still open (unverified)")
    p_todo.add_argument("file")
    p_todo.set_defaults(func=cmd_todo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()