---
name: upload
description: Upload approved SEO titles and meta descriptions in bulk to a WordPress site's Yoast SEO fields, via the WordPress REST API where Yoast allows it, or via Yoast's own bulk editor save endpoints in the person's logged-in browser (works even without REST API access). Covers building the upload sheet, testing, uploading byte for byte, keeping an undo record and verifying every live page.
---

# Uploading meta titles and descriptions through Yoast with AI

This workflow was proven on a UK life sciences site: 103 priority pages first (206 saves, zero failures, 103/103 matching live), then the full approved set (1,153 field saves, zero failures, 706/706 live pages matching the sheet). The REST API only reached 3 of the first 103 pages, so almost everything went through **Yoast's own bulk editor endpoints** in a logged-in browser.

This workflow is about the **upload**. The new titles and descriptions should already be written and approved in the sheet. Your job is to get them onto the site exactly as approved, prove it, and be able to undo it.

Everything for the job lives in one job folder: `GOAL.md`, `metadata-sheet.csv`, `BRIEF.md`. If the person doesn't have one yet, create it by copying the files in `${CLAUDE_PLUGIN_ROOT}/skills/upload/templates/` into a new folder named after the client (the `/yoast-meta-upload:new-job` command does this). If anything's missing, ask.

Work through the stages **in order**. Don't upload anything until stages 1 to 4 are done and the person has said go.

## Standing rules (apply at every stage)

- **Keep the person updated.** If you're unsure, ask. If you're stuck, ask. If there's a better way, say so before changing anything.
- **No AI in the upload.** The upload sends each approved cell exactly as written, byte for byte. You don't reword, fix, trim or "improve" anything on the way in. If a value looks wrong, stop and ask.
- **Approved rows only.** Only rows marked approved go up. Never guess approval.
- **Never delete.** A blank new value means "leave it alone", never "clear the field".
- **Keep the undo record.** Save every field's old value before (or as) you change it.
- **Credentials:** the person logs in. For the REST API you need a username and an **application password**, read from a file and never printed. For the bulk editor route you work inside their logged-in browser and never see a password at all.
- **Truth:** only report something as done once you've re-read it on the live page.

## Stage 1: understand the goal

Get `GOAL.md` filled in:

- the site, and how many rows / pages are going up;
- which post types are involved (posts, pages, custom post types like case studies or products) and whether any **category or taxonomy pages** are in the sheet;
- what's being changed: SEO title, meta description, or both;
- who approved the sheet, and how approval is marked (an Approved column, or a cell colour, e.g. green);
- what "done" looks like: e.g. "every approved row live and matching the sheet, undo record saved, report of anything skipped".

## Stage 2: backwards engineering

Do one by hand, then probe. **Don't write anything in this stage.**

1. **One by hand.** The person (or you, watching) edits one page's Yoast title and description in wp-admin, and notes exactly how it shows on the live page. That's the target.
2. **Yoast setup.** Note the Yoast version (Plugins screen), and whether the person's account can open **Yoast SEO > Tools > Bulk editor** (it needs an editor or admin role).
3. **Probe the REST API (read only).** If there's an application password, `GET /wp-json/` and fetch one item of each post type in the sheet with `?context=edit`. Look for writable Yoast title and description fields. Recent Yoast versions open them to REST for standard posts; pages and custom post types are often not writable. Report exactly which post types REST can write and which it can't.
4. **Probe the bulk editor (read only).** Open the bulk editor page in the logged-in browser. Confirm it lists the post types in the sheet with their IDs, and find the save mechanism it uses: Yoast's bulk editor saves each field through `admin-ajax.php` (title and description save actions) with a nonce printed on that page, and replies with the old and new value. Don't call it yet.
5. **Taxonomy pages.** Category and tag SEO titles aren't in the bulk editor and usually aren't writable over REST. Plan those for the term edit screen in the browser, one by one, or hand them back to the person.

Summarise: "These post types go by REST, these by the bulk editor, these by hand." Get a yes.

## Stage 3: build the sheet for a seamless upload

`metadata-sheet.csv` is the single source of truth. One row per page. Make sure it has:

- **Post ID**: the most important column. Both upload routes work by ID, not URL. Fill it from the REST API (`/wp-json/wp/v2/<type>?per_page=100&_fields=id,link`), the bulk editor listing, or the page source (`page-id-123` / `postid-123` in the body class, or the `?p=123` shortlink).
- **Post type** and **URL**.
- **Current title** and **Current description** (as live now, pulled fresh).
- **New title** and **New description**: the approved values, final literal text. No Yoast variables like `%%sitename%%` unless the person explicitly wants them.
- **Title chars** and **Title px (est.)**, **Desc chars**: calculated by a script, not by eye.
- **Approved**: Yes / No. If the client approved by colour, convert colours to Yes/No first and show the person the count.
- **Route**: REST / Bulk editor / Manual (from stage 2).
- **Uploaded**, **Live title matches**, **Live desc matches**: ticked by the script.
- **Old title (undo)**, **Old desc (undo)**: filled during upload.
- **Notes**.

Before the upload, check the sheet with a script and fix or flag. A ready-made checker ships with this skill; run it first and build on it if the job needs more:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/upload/scripts/check_sheet.py" metadata-sheet.csv --title-max 60 --desc-max 155
```

It reports the problems below and, with `--write`, fills in the Title chars, Title px (est.) and Desc chars columns. It never touches the new values. It covers:

- missing or duplicate Post IDs; URLs that don't match their ID;
- approved rows with an empty new value;
- titles over the agreed limit (e.g. 60 characters / ~600 px) and descriptions over the limit (e.g. 155);
- duplicate new titles or descriptions across pages;
- stray spaces, line breaks, and curly vs straight apostrophes and quotes (WordPress may change curly ones on save; agree which to use so the live check matches);
- formula artefacts or blank cached cells from the spreadsheet export.

Show the person the counts: rows approved, rows skipped and why, per route.

## Stage 4: guard rails

Confirm before any write:

- the route per post type, and the order (e.g. REST posts first, then bulk editor pages);
- **dry run first**: print exactly what would change, row by row, with old and new values;
- **test small**: upload one row, then a canary batch (e.g. 25), check them live, and wait for an OK before the rest;
- **pace it**: a second or two between saves, back off on errors or rate limits;
- the undo record location (e.g. `undo-<date>.csv`).

## Stage 5: upload

### Route A: WordPress REST API (posts it can reach)

- Read the username and application password from the file the person names. Never print them.
- Write a small script in the job folder: for each approved REST row, update the post's Yoast title and description fields found in stage 2, by Post ID.
- It must: support a dry run; send values byte for byte; save the old value first; only touch the two fields; never delete; log every save; and stop on unexpected errors.

### Route B: Yoast bulk editor endpoints (no REST access needed)

- The person is logged in to wp-admin in the browser you control, with the bulk editor page open.
- From that page, use its own nonce and call Yoast's title and description save actions on `admin-ajax.php`, one field at a time, by Post ID, sending the approved value byte for byte. This is exactly what the bulk editor's own Save buttons do.
- Yoast replies with the old and new value for each save. Record the old value in the undo file.
- Work in batches, pacing between saves. If a response isn't a success, stop and report.
- Never ask for or type the person's password.

### Route C: manual / term pages

Category and taxonomy pages, or anything neither route reaches: edit them in the browser, one by one (or hand the list to the person).

## Stage 6: verify

Re-read **every live page** (not the admin screen, not your log):

- the `<title>` matches the sheet's new title, and the meta description matches the new description, exactly;
- compare after decoding HTML entities; treat curly vs straight apostrophes as the only acceptable difference, and list them separately;
- if the site has page caching, purge it (or ask the person to) before checking, and re-check any mismatches after the purge;
- no page outside the sheet changed.

Tick the sheet's live-match columns. Report: uploaded, matched, mismatched (with values), skipped (with reasons).

## Stage 7: close out

- Hand over the completed sheet, the undo file, the log, and the script.
- Remind the person to **revoke the application password** if one was used.
- Note any rows left for a human (term pages, rejected rows, mismatches).

## Undo

If anything needs rolling back, the undo file has every old value by Post ID. Re-run the same route with the old values (dry run first).

## Known snags

- **REST reaches less than you think**: often only standard posts. That's what the bulk editor route is for.
- **Bulk editor permissions**: the account needs a role that can see Yoast's Tools.
- **Session and nonce expiry**: long runs can outlast the login or the page nonce. Reload the bulk editor page and carry on from the log.
- **Caching**: a page cache or CDN can show old titles for a while. Purge, then verify.
- **Apostrophes and entities**: `'` vs `’`, `&amp;` vs `&`. Decide up front and compare decoded.
- **Spreadsheet damage**: find and replace across a sheet can break URL cells; formulas can export as blanks. Check before upload.
- **Usage limits**: very long AI sessions can stop mid-run. Work from the log so you can resume where you left off.
