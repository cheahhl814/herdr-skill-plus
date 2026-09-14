#!/usr/bin/env python3
"""
quiz-import-pdf.py — PDF / Markdown chapter → quiz.schema.v1.json skeleton.

Reads the source via pymupdf4llm (PDF) or directly (Markdown) and emits a
quiz.json with item-kind = 'mcq' / 'short' placeholders that the authoring
agent (or human) fills in. This is *not* an item generator — the LLM fills
in the questions and answer_key/correct fields by reading the extracted
text. The script guarantees the output validates against
quiz.schema.v1.json so §7 can render it without per-item shape drift.

Usage:
    quiz-import-pdf.py --pdf textbook.pdf --pages 42-44 --title "SAM flags" \
        --out quiz.json
    quiz-import-pdf.py --md chapter.md --title "Flags" --out quiz.json

Why a stub, not an autogen: LLM-generated answer keys without a human fact-
check become authoritative hallucinations. The stub extracts the source text;
the agent then authors items against it. Caller's call to fact-check.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA_REF = "herdr-skill+/quiz.v1"


def extract_pdf(path: str, pages: list[int] | None) -> tuple[str, str]:
    try:
        import pymupdf4llm  # type: ignore
    except ImportError:
        sys.exit(
            "pymupdf4llm not installed. `uv pip install pymupdf4llm` "
            "or pass --md for markdown input."
        )
    chunks = pymupdf4llm.to_markdown(path, pages=pages) if pages else pymupdf4llm.to_markdown(path)
    extracted_by = f"quiz-import-pdf.py@script+pymupdf4llm"
    return "\n\n".join(c["text"] if isinstance(c, dict) else c for c in chunks), extracted_by


def extract_md(path: str) -> tuple[str, str]:
    text = Path(path).read_text(encoding="utf-8")
    return text, "quiz-import-pdf.py@script+plain-read"


def build_skeleton(title: str, lesson_id: str | None, source: dict, item_count: int) -> dict:
    items: list[dict] = []
    for i in range(item_count):
        items.append(
            {
                "kind": "mcq",
                "q": f"ITEM {i + 1}: paste the question here, citing the source passage.",
                "options": [
                    {"label": "option A (correct=true here)"},
                    {"label": "option B"},
                    {"label": "option C"},
                    {"label": "option D"},
                ],
                "provenance": {"source_section": "(fill from extracted text)"},
            }
        )
    return {
        "schema": SCHEMA_REF,
        "title": title,
        **({"lesson_id": lesson_id} if lesson_id else {}),
        "source": source,
        "items": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="Source PDF path (uses pymupdf4llm)")
    src.add_argument("--md", help="Source markdown / plain text path")
    ap.add_argument("--pages", help="Page range like 42-44 (PDF only)", default=None)
    ap.add_argument("--title", required=True, help="Quiz title")
    ap.add_argument("--lesson-id", default=None, help="Opaque lesson id (ch3-sam-flags etc.)")
    ap.add_argument("--items", type=int, default=5, help="Number of skeleton items (default 5)")
    ap.add_argument("--out", default="quiz.json", help="Output path (default ./quiz.json)")
    args = ap.parse_args()

    if args.pdf:
        pages = None
        if args.pages:
            try:
                lo, hi = (int(x) for x in args.pages.split("-", 1))
                pages = list(range(lo, hi + 1))
            except ValueError:
                sys.exit("--pages must be like 42-44")
        text, extracted_by = extract_pdf(args.pdf, pages)
        source = {
            "type": "pdf",
            "path": args.pdf,
            **({"pages": pages} if pages else {}),
            "extracted_by": extracted_by,
            "extracted_text_excerpt": text[:2000],
        }
    else:
        text, extracted_by = extract_md(args.md)
        source = {
            "type": "markdown" if args.md.endswith(".md") else "manual",
            "path": args.md,
            "extracted_by": extracted_by,
            "extracted_text_excerpt": text[:2000],
        }

    quiz = build_skeleton(args.title, args.lesson_id, source, args.items)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(quiz, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({args.items} skeleton items).")
    print("Next step: have the agent (or a human) fill in item.q, options, and 'correct' against the extracted_text_excerpt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
