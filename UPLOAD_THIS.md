# UPLOAD THIS FILE — NOT THE SOURCE SNAPSHOT

## The file you must upload is:

```
dist/JUDGE_ATLAS-main-final.zip
```

## Or use the symlink in this directory:

```
UPLOAD_THIS.zip
```

## Do NOT upload any of these:

- `JUDGE_ATLASX-main-master*.zip`
- GitHub "Download ZIP" output
- Any manually compressed project folder
- Any ZIP containing `.env.example` files
- Any ZIP with root folder other than `JUDGE_ATLAS-main/`

## Quick commands

Build the canonical archive:
```bash
make build-for-upload
```

Verify before uploading:
```bash
make verify-upload
```

## Why this matters

The canonical archive (`dist/JUDGE_ATLAS-main-final.zip`) is the only file that:
- Has the correct root folder (`JUDGE_ATLAS-main/`)
- Contains all 58 proof logs
- Contains no forbidden files (`.env.example`, `.kilo/`, etc.)
- Passes `validate_final_zip.py`
- Matches the SHA-256 in `FINAL_RELEASE_HANDOFF.md`

Source snapshots (like `JUDGE_ATLASX-main-master N.zip`) will always fail validation because they contain development artifacts and are missing proof logs.

## If you are unsure

Run:
```bash
make build-for-upload
```

Then upload the file that appears on your Desktop:
```
UPLOAD_THIS_JUDGE_ATLAS-main-final.zip
```
