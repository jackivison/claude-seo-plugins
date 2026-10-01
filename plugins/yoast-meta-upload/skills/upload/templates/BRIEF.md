# Starter brief (not a magic prompt, just the job in plain words)

I want you to upload approved SEO titles and meta descriptions to [site] through Yoast. Follow the yoast-meta-upload workflow (the `yoast-meta-upload:upload` skill).

Everything is in this folder:
- GOAL.md: the job, the post types, how approval is marked and what done looks like
- metadata-sheet.csv: one row per page with the approved new values

[If using the REST API: the username is [username] and the application password is in .secrets/wp-app-password.txt. Use it, but never print it.]
[If using the bulk editor: I'm logged in to wp-admin in the browser you can control.]

Upload only the approved rows, exactly as written. Don't reword anything. A blank new value means leave it alone. Save every old value so we can undo. Do a dry run, then one row, then a small batch, and show me before doing the rest. Check every live page against the sheet at the end.

Keep me updated. If you're unsure, ask me. If you're stuck, ask me. If there's a better way, tell me before you change anything. Don't delete anything.
