# J.A.V.I.S

## Dependency setup and CI smoke tests

Install runtime dependencies before running full validation:

```bash
pip install -r requirements.txt
```

### Why smoke tests may skip packages in minimal environments

The dependency smoke tests are designed to validate the **declared dependency contract** (what this project requires) while still running in minimal CI/local environments where not all optional or system-sensitive packages can be installed.

In those environments, smoke checks may report skips for unavailable packages instead of failing immediately. This keeps baseline CI runnable while making missing runtime pieces explicit.

### Full validation after installing requirements

After installing dependencies, run full test validation:

```bash
pytest -q
```

### Declared contract vs installed environment

- **Declared dependency contract**: packages listed in `requirements.txt` that the project expects.
- **Installed-environment availability**: what is actually importable on a specific machine/CI image at runtime.

A CI image can satisfy the contract only partially if OS-level prerequisites are missing.

### Packages that often need OS-level prerequisites

These packages can require extra system libraries, drivers, permissions, or platform support:

- `PyAudio`
- `openai-whisper`
- `keyboard`
- `mss`

If they are unavailable, install the required OS dependencies first, then re-run `pip install -r requirements.txt` and `pytest -q`.
