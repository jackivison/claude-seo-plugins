---
description: Start a new Yoast meta upload job folder (GOAL.md, BRIEF.md, metadata-sheet.csv)
argument-hint: [client-name]
allowed-tools: Bash(mkdir:*), Bash(cp:*), Bash(ls:*), Read
---

Set up a new Yoast meta upload job.

1. Work out the client name from the argument "$ARGUMENTS". If it's empty, ask the person which client or site this is for.
2. Turn it into a folder name (lowercase, hyphens, e.g. `acme-plant-hire`) and create it in the current directory. If that folder already exists, stop and ask rather than overwriting anything.
3. Copy the three template files into it:
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/upload/templates/"{GOAL.md,BRIEF.md,metadata-sheet.csv} <folder>/
   ```
4. Tell the person, in a few short lines:
   - the folder is ready, and what's in it;
   - next: fill in `GOAL.md`, paste the approved rows into `metadata-sheet.csv` (Post ID is the key column; you can fill it in for them from the site), and either log in to wp-admin in the browser you can control (bulk editor route) or save an application password in `<folder>/.secrets/wp-app-password.txt` (REST route);
   - then open Claude Code in that folder and paste in `BRIEF.md`, or just say "upload the approved metadata".

Don't start the upload from this command. The `yoast-meta-upload:upload` skill runs the job.
