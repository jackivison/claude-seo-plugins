#!/usr/bin/env python3
"""Pre-upload check for a Yoast metadata sheet.

Reads metadata-sheet.csv and reports anything that would make the upload go
wrong: missing or duplicate Post IDs, approved rows with no new value, values
over length, duplicate new values, stray whitespace, curly quotes and
spreadsheet artefacts. It never changes the New title / New description cells.

With --write it fills in the Title chars, Title px (est.) and Desc chars
columns (and nothing else), saving the sheet in place.

Standard library only. Exit code 1 if any errors were found, 0 otherwise.
"""

import argparse
import csv
import re
import sys
from collections import defaultdict

# Rough Arial 20px widths (Google's desktop title font), in pixels.
NARROW = set("fijlrtI!|.,:;'`")
WIDE = set("mwMW@")
UPPER_WIDE = set("ABCDEFGHKNOPQRSUVXYZ&%")


def est_px(text):
    px = 0.0
    for ch in text:
        if ch in NARROW:
            px += 5.5
        elif ch in WIDE:
            px += 16.5
        elif ch in UPPER_WIDE:
            px += 13.0
        elif ch == " ":
            px += 5.5
        elif ch.isupper() or ch.isdigit():
            px += 11.0
        else:
            px += 10.0
    return round(px)


CURLY = "‘’“”"
ARTEFACT = re.compile(r"^(#(REF|VALUE|N/A|NAME|DIV/0)!?|=.*)$", re.I)


def find_col(headers, *names):
    lower = {h.strip().lower(): h for h in headers}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def is_yes(v):
    return (v or "").strip().lower() in {"yes", "y", "true", "1", "approved"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", help="path to metadata-sheet.csv")
    ap.add_argument("--title-max", type=int, default=60, help="max title characters (default 60)")
    ap.add_argument("--title-px-max", type=int, default=600, help="max estimated title pixels (default 600)")
    ap.add_argument("--desc-max", type=int, default=155, help="max description characters (default 155)")
    ap.add_argument("--write", action="store_true", help="fill in the char/px columns and save the sheet")
    args = ap.parse_args()

    with open(args.sheet, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    c_id = find_col(headers, "Post ID", "ID")
    c_url = find_col(headers, "URL")
    c_title = find_col(headers, "New title")
    c_desc = find_col(headers, "New description")
    c_appr = find_col(headers, "Approved")
    c_route = find_col(headers, "Route")
    c_tchars = find_col(headers, "Title chars")
    c_tpx = find_col(headers, "Title px (est.)", "Title px")
    c_dchars = find_col(headers, "Desc chars")

    errors, warnings = [], []
    if not c_title and not c_desc:
        print("ERROR: no 'New title' or 'New description' column found.")
        return 1
    if not c_appr:
        errors.append("no 'Approved' column: approval must be explicit (convert colours to Yes/No first)")
    if not c_id:
        warnings.append("no 'Post ID' column: both upload routes save by Post ID, fill it in before uploading")

    ids = defaultdict(list)
    titles = defaultdict(list)
    descs = defaultdict(list)
    approved = skipped = 0
    routes = defaultdict(int)

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        label = f"row {i}" + (f" (ID {row.get(c_id, '').strip()})" if c_id and row.get(c_id, "").strip() else "")
        title = row.get(c_title, "") if c_title else ""
        desc = row.get(c_desc, "") if c_desc else ""

        if args.write:
            if c_tchars:
                row[c_tchars] = str(len(title)) if title else ""
            if c_tpx:
                row[c_tpx] = str(est_px(title)) if title else ""
            if c_dchars:
                row[c_dchars] = str(len(desc)) if desc else ""

        if c_appr and not is_yes(row.get(c_appr)):
            skipped += 1
            continue
        approved += 1
        if c_route:
            routes[(row.get(c_route) or "unset").strip() or "unset"] += 1

        pid = (row.get(c_id) or "").strip() if c_id else ""
        if c_id:
            if not pid:
                errors.append(f"{label}: approved but no Post ID")
            elif not pid.isdigit():
                errors.append(f"{label}: Post ID '{pid}' isn't a number")
            else:
                ids[pid].append(i)
        if c_url:
            url = (row.get(c_url) or "").strip()
            if url and not re.match(r"^https?://", url):
                warnings.append(f"{label}: URL '{url}' doesn't start with http(s)://")

        if not title.strip() and not desc.strip():
            errors.append(f"{label}: approved but both new values are empty (blank means 'leave alone')")

        for name, val, limit in (("title", title, args.title_max), ("description", desc, args.desc_max)):
            if not val:
                continue
            if ARTEFACT.match(val.strip()):
                errors.append(f"{label}: new {name} looks like a spreadsheet artefact: {val!r}")
            if val != val.strip():
                warnings.append(f"{label}: new {name} has leading/trailing spaces")
            if "  " in val:
                warnings.append(f"{label}: new {name} has double spaces")
            if "\n" in val or "\r" in val:
                errors.append(f"{label}: new {name} contains a line break")
            if any(c in val for c in CURLY):
                warnings.append(f"{label}: new {name} has curly quotes (agree curly vs straight before upload)")
            if "%%" in val:
                warnings.append(f"{label}: new {name} contains a Yoast variable ({val!r}), confirm that's wanted")
            if len(val) > limit:
                warnings.append(f"{label}: new {name} is {len(val)} chars (limit {limit})")
        if title and est_px(title) > args.title_px_max:
            warnings.append(f"{label}: new title is ~{est_px(title)}px (limit {args.title_px_max})")

        if title.strip():
            titles[title.strip().lower()].append(i)
        if desc.strip():
            descs[desc.strip().lower()].append(i)

    for pid, where in ids.items():
        if len(where) > 1:
            errors.append(f"Post ID {pid} appears on rows {', '.join(map(str, where))}")
    for name, seen in (("title", titles), ("description", descs)):
        for val, where in seen.items():
            if len(where) > 1:
                warnings.append(f"duplicate new {name} on rows {', '.join(map(str, where))}: {val[:60]!r}")

    print(f"Sheet: {args.sheet}")
    print(f"Rows: {len(rows)}  approved: {approved}  skipped (not approved): {skipped}")
    if routes:
        print("By route: " + ", ".join(f"{k}: {v}" for k, v in sorted(routes.items())))
    print()
    for e in errors:
        print("ERROR  " + e)
    for w in warnings:
        print("WARN   " + w)
    if not errors and not warnings:
        print("No problems found.")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")

    if args.write:
        with open(args.sheet, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(rows)
        print("Char/px columns written.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
