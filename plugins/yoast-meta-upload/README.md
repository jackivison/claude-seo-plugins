# Yoast meta upload

Uploads your approved SEO titles and meta descriptions to a WordPress site's Yoast fields, in bulk, exactly as approved, with an undo record and a live check of every page.

Proven on a UK life sciences site: 1,153 field saves, zero failures, and all 706 live pages checked against the sheet afterwards.

## Two ways in

- **WordPress REST API** (with an application password): fast, but Yoast often only opens its fields to REST for standard blog posts.
- **Yoast's bulk editor** (in your logged-in browser): reaches pages and custom post types too, and works even if your account can't make an application password. Claude never sees your password. This route needs a browser Claude can drive, such as [Claude in Chrome](https://claude.com/chrome).

Category and tag pages aren't in the bulk editor, so those are done by hand or clicked through in the browser.

## Install

```
/plugin marketplace add jackivison/claude-seo-plugins
/plugin install yoast-meta-upload@seo-workflows
```

## Use

1. `/yoast-meta-upload:new-job acme-plant-hire` creates a job folder with `GOAL.md`, `BRIEF.md` and `metadata-sheet.csv`.
2. Fill in `GOAL.md` and paste your approved rows into `metadata-sheet.csv`. **Post ID** is the key column (Claude can fill it in from the site); mark approved rows `Yes`.
3. Log in to wp-admin in the browser Claude controls (bulk editor route), and/or save an application password in `.secrets/wp-app-password.txt` (REST route).
4. Open Claude Code in the job folder and paste in `BRIEF.md`, or just say "upload the approved metadata".

Claude then works through seven stages: understand the goal, probe what each route can reach (read only), check the sheet, agree guard rails, upload, verify every live page, and hand over.

## The rules it follows

- **No AI in the upload.** Every approved cell goes up byte for byte. No rewording, trimming or "improving".
- **Approved rows only.** Never guesses approval.
- **Never deletes.** A blank new value means "leave it alone".
- **Undo record.** Every old value is saved before it's changed.
- **Test small.** Dry run, then one row, then a small batch checked live, then the rest once you say go.
- **Truth.** Nothing is reported as done until it's re-read on the live page.

If you used an application password, revoke it when the job's done.

## Sheet checker

The skill ships a standalone checker you can also run yourself (Python 3, no installs):

```
python3 skills/upload/scripts/check_sheet.py metadata-sheet.csv --title-max 60 --desc-max 155 [--write]
```

It flags missing or duplicate Post IDs, approved rows with nothing in them, over-length values, duplicate titles or descriptions, stray spaces, line breaks, curly quotes, Yoast variables and spreadsheet artefacts. `--write` fills in the character and estimated pixel-width columns.

## Licence

MIT
