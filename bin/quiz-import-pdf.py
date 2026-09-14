#!/usr/bin/env python3
"""
quiz-import-pdf.py - PDF / Markdown / stdin text -> course-Markdown scaffold.

**Markdown is the spine**, JSON is only emitted at the lesson->quiz boundary.
This importer mirrors the existing course layout at
`course-materials/<course>/<lesson>/{README,exercises}.md` (see
`obs-2026-08-18-6-week-bacterial-genome-pipeline-course-built-via-2-herdr-de`)
plus a `quiz-<id>.json` matching `quiz.schema.v1.json` for §7 grading.

Three source paths exist because real course content arrives in many
shapes; we keep a Python CLI deterministic and use LLM mediation only
as a fallback for shapes no parser handles.

Usage:
    # 1. PDF chapter - one lesson scaffold (pymupdf4llm)
    quiz-import-pdf.py --pdf textbook.pdf --pages 42-60 \\
        --title "SAM flags" --lesson-id ch3-sam-flags \\
        --out-dir course-materials/

    # 2. Markdown / plain text on disk - one lesson scaffold
    quiz-import-pdf.py --md chapter.md --title "SAM flags" \\
        --lesson-id ch3-sam-flags --out-dir course-materials/

    # 3. LLM-mediated fallback - pipe *any* text via stdin
    #    (YouTube transcript copy-paste, Notion export, lecture notes
    #    dictated from audio, DOCX-after-pandoc-conversion, etc.)
    #
    #    The script does NOT call an LLM. It writes the source text to
    #    <lesson>/source.txt, scaffolds the Markdown + quiz JSON
    #    skeletons, and emits a FILL_THIS.md directive that the agent
    #    reads in chat and fills. The user retains ownership - the
    #    script never *fetches* anything; the user provides the text.
    cat transcript.txt | quiz-import-pdf.py --llm-stdin \\
        --title "SAM flags" --lesson-id ch3-sam-flags \\
        --out-dir course-materials/
    # ...then the agent reads the printed directive and fills the
    # skeleton README, exercises, and quiz JSON from source.txt.

    # 4. Quiz only - emit quiz-<id>.json from an already-authored lesson
    quiz-import-pdf.py --quiz-from course-materials/<course>/<lesson>/exercises.md \\
        --lesson-id ch3-sam-flags --title "SAM flags"

The script produces, per lesson:
    <out-dir>/<slug>/README.md         (~1500 words lecture / concepts skeleton)
    <out-dir>/<slug>/exercises.md      (typed shell commands skeleton)
    <out-dir>/<slug>/quiz-<id>.json    (matches quiz.schema.v1.json for §7)
    <out-dir>/<slug>/source.txt        (only in --llm-stdin mode; immutable
                                        reference of the user-provided text)

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


def write_llm_directive(lesson_dir: Path, lesson_title: str, lesson_id: str, source_text: str, source_path: Path, items: int) -> Path:
    """Write the directive the agent (or human) reads to fill the skeletons.

    The directive is the LLM-mediated counterpart to a parser invocation: it
    is concrete enough that an LLM agent can mechanically fill the
    README / exercises / quiz skeletons from source.txt without having to
    re-derive the source. Includes the source SHA so the agent can verify
    the staged text matches the user's intent.
    """
    import hashlib
    sha = hashlib.sha256(source_text.encode("utf-8")).hexdigest()[:12]
    excerpt = source_text[:1500] + ("..." if len(source_text) > 1500 else "")
    body = (
        "# FILL_THIS.md - LLM-authored lesson directive\n\n"
        f"---\n"
        f"title: {lesson_title}\n"
        f"lesson_id: {lesson_id}\n"
        f"source_path: {source_path}\n"
        f"source_sha256_12: {sha}\n"
        f"source_chars: {len(source_text)}\n"
        f"items_requested: {items}\n"
        f"status: pending - agent or human fills the skeletons below\n"
        "---\n\n"
        "## What this is\n\n"
        "You (the agent reading this in chat) are being asked to fill the lesson\n"
        "skeletons under this directory from the user-provided text at\n"
        f"`{source_path}`. The skeletons are:\n\n"
        f"- `README.md` - lecture / concepts, ~1500 words, suitable for §6 tutorial read-aloud\n"
        f"- `exercises.md` - typed shell commands the student runs, suitable for §6 lesson walk\n"
        f"- `quiz-{lesson_id}.json` - {items} quiz items matching `quiz.schema.v1.json`, suitable for §7 per-item gate\n\n"
        "## Source excerpt (first 1500 chars)\n\n"
        f"```text\n{excerpt}\n```\n\n"
        "## Fill instructions\n\n"
        "1. Read `source.txt` in full. Do not paraphrase beyond what the source states.\n"
        "2. Fill `README.md` by replacing the **Source excerpt** fenced block with prose\n"
        "   covering the lesson's main concepts. Keep `## Learning objectives` placeholder\n"
        "   until you list 3-5 outcomes.\n"
        "3. Fill `exercises.md` by replacing the `Exercise 2 / 3-N` stubs with real,\n"
        "   typed shell commands grounded in the source. Use verbatim commands where\n"
        "   the source gives them; reconstruct only when the source describes a tool\n"
        "   but not its invocation, and flag reconstruction with `# reconstructed`.\n"
        "4. Fill `quiz-{lesson_id}.json` per item:\n"
        "   - Pick a mix of `mcq`, `multi`, `preview`, `short`, `task` kinds\n"
        "     (see `quiz.schema.v1.json`).\n"
        "   - Set `correct: true` on exactly the right option(s).\n"
        "   - For `short`, write `answer_key` as a reference answer; §7 accepts\n"
        "     obvious synonyms during grading, you only write the canonical form.\n"
        "   - For `task`, link to its §6 lesson via `task_id` if known.\n"
        "5. Validate the JSON against `quiz.schema.v1.json` after writing:\n"
        '   uv run --with jsonschema python3 -c "import json, jsonschema; \\\n'
        f'   jsonschema.validate(json.load(open(\'quiz-{lesson_id}.json\')), json.load(open(\'quiz.schema.v1.json\')))"\n'
        "6. Delete this `FILL_THIS.md` once the skeletons are filled; it has no\n"
        "   semantic role beyond orchestrating your next turn.\n\n"
        "## Hard rules\n\n"
        "- Do NOT introduce facts not present in `source.txt`. If the source is thin\n"
        "  on a topic, write fewer items rather than hallucinate correct answers.\n"
        "- Do NOT mark more than one option `correct: true` on `mcq` items.\n"
        "- Do NOT batch quiz items into fewer call(s) - §7 enforces one\n"
        "  ask_user_question call per item.\n"
    )
    path = lesson_dir / "FILL_THIS.md"
    path.write_text(body, encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="Source PDF path (uses pymupdf4llm)")
    src.add_argument("--md", help="Source markdown / plain text path")
    src.add_argument("--llm-stdin", action="store_true", help="Read source text from stdin (LLM-mediated fallback)")
    src.add_argument("--quiz-from", help="Existing lesson .md path; emit quiz JSON only, no Markdown re-emit")
    ap.add_argument("--pages", help="PDF page range like 42-60 (PDF only)", default=None)
    ap.add_argument("--title", required=True, help="Course or lesson title")
    ap.add_argument("--lesson-id", default=None, help="Opaque lesson id (ch3-sam-flags etc.)")
    ap.add_argument("--items", type=int, default=5, help="Quiz items (default 5)")
    ap.add_argument("--no-quiz", action="store_true", help="Emit README+exercises only; skip quiz-<id>.json")
    ap.add_argument("--out-dir", default="course-materials", help="Output root directory")
    args = ap.parse_args()

    emitted: list[Path] = []
    directive_emitted: Path | None = None

    if args.llm_stdin:
        # LLM-mediated fallback: user pipes text into stdin. Script writes
        # the text to disk as the immutable reference, scaffolds the
        # Markdown + JSON skeletons, and emits a FILL_THIS.md directive
        # that the agent reads in chat. The script never *fetches*; the
        # user provides the text - the rights stay with the user.
        if sys.stdin.isatty():
            sys.exit("--llm-stdin requires piped input; redirect or pipe a file. Try: cat source.txt | quiz-import-pdf.py --llm-stdin ...")
        text = sys.stdin.read()
        if not text.strip():
            sys.exit("--llm-stdin: stdin was empty.")
        slug = slugify(args.lesson_id or args.title)
        out_dir = Path(args.out_dir)
        lesson_dir = out_dir / slug
        lesson_dir.mkdir(parents=True, exist_ok=True)
        source_path = lesson_dir / "source.txt"
        source_path.write_text(text, encoding="utf-8")
        source_meta = {
            "type": "stdin",
            "path": str(source_path),
            "extracted_by": "quiz-import-pdf.py+stdin-redirect",
            "source_chars": len(text),
        }
        course_readme = out_dir / "README.md"
        if not course_readme.exists():
            emitted.append(write_top_level_readme(out_dir, args.title, str(source_path)))
        written = write_lesson_md(lesson_dir, args.title, text, source_meta)
        emitted.extend(written.values())
        if not args.no_quiz:
            qpath = write_quiz(out_dir, slug, args.lesson_id or slug, args.title, text, source_meta, args.items)
            emitted.append(qpath)
        directive_emitted = write_llm_directive(lesson_dir, args.title, args.lesson_id or slug, text, source_path, args.items)
        emitted.append(directive_emitted)
    elif args.quiz_from:
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
    if directive_emitted is not None:
        print()
        print("=" * 72)
        print("ACTION: Open this file and follow it. The agent must read")
        print(f"  {directive_emitted}")
        print("and fill the skeletons (README.md, exercises.md, quiz-*.json)")
        print("from source.txt. Do not skip this step; empty skeletons teach")
        print("nothing.")
        print("=" * 72)
    else:
        print("Next step: agent or human fills q/options/correct in each quiz-<id>.json against extracted_text_excerpt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
