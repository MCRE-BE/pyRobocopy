---
hide:
  - navigation
---
# Installation

This library is a thin Python wrapper around the Windows `robocopy` utility.

## Recommended Installation (uv)

We recommend using [uv](https://github.com/astral-sh/uv) for dependency management.

### Option A: Direct Add
To add `pyRobocopy` directly to your project:

```bash
uv add git+https://github.com/MCRE-BE/pyRobocopy.git
```

### Option B: Project Configuration
You can also define the source in your `pyproject.toml` to manage it more easily:

```toml
[tool.uv.sources]
pyrobocopy = { git = "https://github.com/MCRE-BE/pyRobocopy" }
```

Then simply run:
```bash
uv add pyrobocopy
```

## Standard Installation

If you are using standard `pip`, you can install directly from the GitHub source:

```bash
pip install git+https://github.com/MCRE-BE/pyRobocopy.git
```

## Environment Requirements

- **OS**: Windows (Required for the underlying `robocopy.exe`)
- **Python**: 3.10 or higher
