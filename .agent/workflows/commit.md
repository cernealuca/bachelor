---
description: Commit current changes to git with a descriptive message
---

# Git Commit Workflow

This workflow commits all current changes to the git repository.

## Steps

1. Check what files have changed:
// turbo
```bash
git status
```

2. Stage all changes:
// turbo
```bash
git add .
```

3. Create a commit with a descriptive message:
```bash
git commit -m "<describe what was accomplished>"
```

The commit message should follow this format:
- Start with a verb (Add, Update, Fix, Implement, Refactor, etc.)
- Be concise but descriptive
- Mention the main feature/component affected
- Example: "Add OCR processing for field catalog PDF"

4. Push to remote repository:
// turbo
```bash
git push
```

## Notes

- Always commit after completing a significant feature or fix
- The `.gitignore` excludes: PDFs (too large), `__pycache__`, `.env`, temp files, `ocr_test/`, `pdf_chunks/`
- If push fails due to remote changes, pull first: `git pull --rebase`
