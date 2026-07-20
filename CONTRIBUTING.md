# Contributing

1. Open an issue before large changes.
2. Keep runtime tool-neutral and file-first.
3. Never commit manuscripts, credentials, cookies, browser profiles, private logs, or absolute home paths.
4. Add tests for state transitions and false-completion guards.
5. Preserve author/editor/reader role separation.
6. Record third-party material in `THIRD_PARTY_NOTICES.md`.

Run before submitting:

```bash
python -m unittest discover -s tests -v
python scripts/release_check.py
```
