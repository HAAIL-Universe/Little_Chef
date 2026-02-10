#!/usr/bin/env python3
"""Seed data/recipe_books/ with recipes from the Hugging Face
gossminn/wikibooks-cookbook dataset.

Usage:
    python scripts/seed_wikibooks_cookbook.py [--max N] [--format md|json] [--dry-run]

Requires:  pip install datasets
The script is idempotent: it wipes data/recipe_books/ and recreates from scratch.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

DATA_DIR = os.path.join(os.getcwd(), "data", "recipe_books")


def slugify(text: str, max_len: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s[:max_len].strip("_") or "recipe"


def seed(max_recipes: int, fmt: str, dry_run: bool) -> None:
    try:
        from datasets import load_dataset  # type: ignore[import-untyped]
    except ImportError:
        print("ERROR: 'datasets' package not installed. Run: pip install datasets", file=sys.stderr)
        sys.exit(1)

    print(f"Loading gossminn/wikibooks-cookbook (max {max_recipes} recipes, format={fmt}) ...")
    ds = load_dataset("gossminn/wikibooks-cookbook", split="train")

    count = min(max_recipes, len(ds))
    recipes = ds.select(range(count))

    if not dry_run:
        # Wipe and recreate for idempotency
        if os.path.isdir(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)

    written = 0
    seen_slugs: set[str] = set()

    for i, row in enumerate(recipes):
        title = (row.get("title") or f"recipe_{i+1}").strip()
        text = (row.get("text") or "").strip()
        if not text:
            continue

        slug = slugify(title)
        # Ensure unique filenames
        if slug in seen_slugs:
            slug = f"{slug}_{i}"
        seen_slugs.add(slug)

        if fmt == "md":
            content = f"# {title}\n\n{text}\n"
            filename = f"{slug}.md"
        else:
            content = json.dumps({"title": title, "text": text}, ensure_ascii=False, indent=2) + "\n"
            filename = f"{slug}.json"

        filepath = os.path.join(DATA_DIR, filename)

        if dry_run:
            print(f"  [dry-run] Would write: {filename} ({len(content)} chars)")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        written += 1

    print(f"\nSeed complete: {written} recipes {'would be ' if dry_run else ''}written.")
    print(f"Format: {fmt}")
    print(f"Output: {DATA_DIR}")
    if written > 0 and not dry_run:
        # Show a few example filenames
        files = sorted(os.listdir(DATA_DIR))[:5]
        print(f"Example files: {files}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed recipe_books from Wikibooks Cookbook (Hugging Face)")
    parser.add_argument("--max", type=int, default=100, help="Max recipes to download (default: 100)")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format (default: md)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()
    seed(max_recipes=args.max, fmt=args.format, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
