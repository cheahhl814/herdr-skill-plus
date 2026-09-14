#!/usr/bin/env python3
"""
quiz-import-pdf.py - PDF / Markdown chapter -> course-Markdown scaffold.

**Markdown is the spine**, JSON is only emitted at the lesson->quiz boundary.
This importer mirrors the existing course layout at
`course-materials/<course>/<lesson>/{README,exercises}.md` (see
`obs-2026-08-18-6-week-bacterial-genome-pipeline-course-built-via-2-herdr-de`)
plus a `quiz-<id>.json` matching `quiz.schema.v1.json` for §7 grading.

Usage:
    # One lesson from a Markdown chapter (single source -> one lesson)
    quiz-import-pdf.py --md chapter.md --title "SAM flags" \\
        --lesson-id ch3-sam-flags --out-dir course-materials/

    # One lesson from a PDF chapter (use --pages)
    quiz-import-pdf.py --pdf textbook.pdf --pages 42-60 \\
        --title "SAM flags" --lesson-id ch3-sam-flags \\
        --out-dir course-materials/

    # Multi-chapter PDF: run once per chapter (the simplest, most predictable shape)
    for chap in 1 2 3; do
      quiz-import-pdf.py --pdf textbook.pdf --pages "$chap"-pages \\
        --title "Chapter $chap" --lesson-id ch$chap \\
        --out-dir course-materials/
    done
    # Then write course-materials/README.md by hand with the mermaid course map.

    # Quiz only - emit quiz-<id>.json from an already-authored lesson
    quiz-import-pdf.py --quiz-from course-materials/<course>/<lesson>/exercises.md \\
        --lesson-id ch3-sam-flags --title "SAM flags"

It produces, per lesson:
    <out-dir>/<slug>/README.md         (~1500 words of lecture / concepts)
    <out-dir>/<slug>/exercises.md      (typed shell commands)
    <out-dir>/<slug>/quiz-<id>.json    (matches quiz.schema.v1.json for §7)

Why call-once-per-chapter rather than --lessons ch1=... ch2=...:
    A multi-chapter PDF's table of contents is hard to parse generically
    (Roman vs Arabic pages, appendix vs body, foreword vs chapter 1).
    A human who knows the page ranges imports faster than the script
    guessing wrong. Run this script in a loop; the workflow is
    predictable and easy to diff.
"""

from __future__ import annotations

import argparse
import json
import re
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
    chunks = (
        pymupdf4llm.to_markdown(path, pages=pages)
        if pages
        else pymupdf4llm.to_markdown(path)
    )
    extracted_by = "quiz-import-pdf.py+pymupdf4llm"
    return "\n\n".join(c["text"] if isinstance(c, dict) else c for c in chunks), extracted_by


def extract_md(path: str) -> tuple[str, str]:
    return Path(path).read_text(encoding="utf-8"), "quiz-import-pdf.py+plain-read"


def slugify(label: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", label.strip().lower()).strip("-")
    return s or "lesson"


def parse_pages(spec: str | None) -> list[int] | None:
    if not spec:
        return None
    m = re.match(r"^(\d+)-(\d+)$", spec)
    if not m:
        sys.exit(f"--pages must be like 42-60 (got {spec!r})")
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo > hi:
        sys.exit(f"--pages must be lo <= hi (got {spec!r})")
    return list(range(lo, hi + 1))


def write_lesson_md(lesson_dir: Path, lesson_title: str, source_text: str, source_meta: dict) -> dict[str, Path]:
    lesson_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = (
        "---\n"
        f"title: {lesson_title}\n"
        f"source: {source_meta.get('path', '?')}\n"
        f"imported_by: quiz-import-pdf.py\n"
        f"status: skeleton - agent or human fills content from source_text_excerpt\n"
        "---\n\n"
    )
    readme = lesson_dir / "README.md"
    exercises = lesson_dir / "exercises.md"
    readme.write_text(
        frontmatter
        + f"# {lesson_title}\n\n"
        + "## Learning objectives\n\n"
        + "- TODO: list 3-5 outcomes the student should reach by end of lesson.\n\n"
        + "## Source excerpt (paste-immutable; agent fills concept text above)\n\n"
        + "```text\n"
        + source_text[:4000]
        + "\n```\n\n",
        encoding="utf-8",
    )
    exercises.write_text(
        frontmatter
        + f"# {lesson_title} - Exercises\n\n"
        + "Type every command. If output surprises you, read it. If the error is cryptic, search it.\n\n"
        + "## Exercise 1 - Set up the scratch dir\n\n"
        + "```bash\n"
        + "mkdir -p ~/course-scratch\n"
        + "cd ~/course-scratch\n"
        + "```\n\n"
        + "## Exercise 2 - First command from the source\n\n"
        + "Replace this stub with the actual commands derived from the README's source excerpt above.\n\n"
        + "```bash\n"
        + "# TODO: type the first command the student should learn here\n"
        + "```\n\n"
        + "## Exercise 3-N - Continue per the source\n\n"
        + "Add exercises for each concept in the README. Order: easiest first.\n",
        encoding="utf-8",
    )
    return {"readme": readme, "exercises": exercises}


def build_quiz_skeleton(lesson_id: str, lesson_title: str, source_text: str, source_meta: dict, item_count: int) -> dict:
    items: list[dict] = []
    for i in range(item_count):
        items.append(
            {
                "kind": "mcq",
                "q": f"ITEM {i + 1}: paste the question here, citing the source passage.",
                "options": [
                    {"label": "option A (mark correct=true on the right one)"},
                    {"label": "option B"},
                    {"label": "option C"},
                    {"label": "option D"},
                ],
                "provenance": {"source_excerpt": source_text[:1200]},
            }
        )
    return {
        "schema": SCHEMA_REF,
        "title": lesson_title,
        "lesson_id": lesson_id,
        "source": {**source_meta, "extracted_text_excerpt": source_text[:2000]},
        "items": items,
    }


def write_top_level_readme(out_dir: Path, course_title: str, source_path: str) -> Path:
    path = out_dir / "README.md"
    path.write_text(
        f"# {course_title}\n\n"
        f"_Imported from `{source_path}` by quiz-import-pdf.py. "
        f"Each lesson lives in its own subdirectory with `README.md`, `exercises.md`, and "
        f"optional `quiz-<id>.json` for §7. CC-BY-SA 4.0._\n\n"
        f"## Course map\n\n"
        f"Replace this stub with a mermaid `flowchart LR` linking every lesson directory. "
        f"See `course-materials/bacterial-genome-pipeline/README.md` for a worked example.\n\n",
        encoding="utf-8",
    )
    return path


def write_quiz(out_dir: Path, lesson_slug: str, lesson_id: str, lesson_title: str, source_text: str, source_meta: dict, item_count: int) -> Path:
    quiz = build_quiz_skeleton(lesson_id, lesson_title, source_text, source_meta, item_count)
    path = out_dir / lesson_slug / f"quiz-{lesson_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(quiz, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="Source PDF path (uses pymupdf4llm)")
    src.add_argument("--md", help="Source markdown / plain text path")
    src.add_argument("--quiz-from", help="Existing lesson .md path; emit quiz JSON only, no Markdown re-emit")
    ap.add_argument("--pages", help="PDF page range like 42-60 (PDF only)", default=None)
    ap.add_argument("--title", required=True, help="Course or lesson title")
    ap.add_argument("--lesson-id", default=None, help="Opaque lesson id (ch3-sam-flags etc.)")
    ap.add_argument("--items", type=int, default=5, help="Quiz items (default 5)")
    ap.add_argument("--no-quiz", action="store_true", help="Emit README+exercises only; skip quiz-<id>.json")
    ap.add_argument("--out-dir", default="course-materials", help="Output root directory")
    args = ap.parse_args()

    emitted: list[Path] = []

    if args.quiz_from:
        # Quiz-only mode against an existing lesson
        src_path = Path(args.quiz_from)
        text, extracted_by = extract_md(str(src_path))
        slug = src_path.parent.name
        source_meta = {"type": "markdown", "path": str(src_path), "extracted_by": extracted_by}
        out_dir = src_path.parent.parent
        quiz_path = write_quiz(out_dir, slug, args.lesson_id or slug, args.title, text, source_meta, args.items)
        emitted.append(quiz_path)
    else:
        # Lesson-import mode (.md or .pdf)
        if not (args.pdf or args.md):
            ap.error("Provide --pdf, --md, or --quiz-from.")

        if args.pdf:
            pages = parse_pages(args.pages)
            text, extracted_by = extract_pdf(args.pdf, pages)
            source_meta = {"type": "pdf", "path": args.pdf, "extracted_by": extracted_by}
            if pages:
                source_meta["pages"] = pages
        else:
            text, extracted_by = extract_md(args.md)
            t = "markdown" if args.md.endswith(".md") else "manual"
            source_meta = {"type": t, "path": args.md, "extracted_by": extracted_by}

        slug = slugify(args.lesson_id or args.title)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Top-level course README only on the very first lesson (heuristic: directory had no README)
        course_readme = out_dir / "README.md"
        if not course_readme.exists():
            emitted.append(write_top_level_readme(out_dir, args.title, source_meta["path"]))

        written = write_lesson_md(out_dir / slug, args.title, text, source_meta)
        emitted.extend(written.values())
        if not args.no_quiz:
            qpath = write_quiz(out_dir, slug, args.lesson_id or slug, args.title, text, source_meta, args.items)
            emitted.append(qpath)

    print(f"Wrote {len(emitted)} files:")
    for p in emitted:
        print(f"  {p}")
    print("Next step: agent or human fills q/options/correct in each quiz-<id>.json against extracted_text_excerpt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
