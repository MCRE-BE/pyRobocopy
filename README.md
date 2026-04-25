# pyRobocopy

A high-performance, object-oriented Python wrapper for the Windows `robocopy` utility. This library is designed to replace slow Python-level file synchronization with fast, robust, OS-level execution.

## Key Features

- **Smart Progress Tracking**: Automatically performs a discovery pass to determine the total file count for accurate percentage-based progress bars.
- **Structured Configuration**: Over 70+ Robocopy flags organized into logical categories (Copy, Selection, Logging).
- **Command-Line Parsing**: Initialize full configuration objects directly from raw Robocopy command strings.
- **Multithreading**: Full support for Robocopy's multi-thread (`/MT`) engine.
- **Rich Results**: Programmatic access to outcome statistics and error mapping for Windows System Errors.

## Installation

This library provides a high-level API for Robocopy. Ensure the `robocopy` directory is in your `PYTHONPATH`.

```bash
pip install tqdm loguru  # Core dependencies
```

## Quick Start (Functional API)

The simplest way to use the library is the `robocopy` convenience function, which maintains backward compatibility for standard sync tasks.

```python
from robocopy import robocopy

# Simple sync with a smart progress bar
robocopy(
    src="C:/Source",
    dst="D:/Destination",
    threads=32,
    smart_progress=True
)
```

## Advanced Usage (Object-Oriented API)

For complex synchronization tasks, use the `RobocopyRunner` and `RobocopyConfig` classes.

### 1. Configure via Dataclasses
```python
from robocopy import RobocopyConfig, RobocopyRunner

config = RobocopyConfig(source="C:/data", destination="D:/backup")
config.copy.mirror = True
config.copy.multi_threaded = 16
config.selection.exclude_older = True
config.selection.exclude_files = ["*.tmp", "log.txt"]

runner = RobocopyRunner(config)
result = runner.run(smart_progress=True)

if result.success:
    print(f"Copied {result.stats.files.copied} files.")
```

### 2. Parse from Raw Command
You can instantiate a config directly from a standard Robocopy command string.

```python
cmd = "robocopy C:\\Data D:\\Backup /S /E /MT:32 /XO /XF *.tmp"
config = RobocopyConfig.from_command_line(cmd)

runner = RobocopyRunner(config)
result = runner.run()
```


## Command-Line Interface (CLI)

`pyrobocopy` comes with a command-line interface, exposed as both `pyrobocopy` and `robocopy` commands.

It supports multiple parsing backends using the `--backend` flag:

- **`windows` (Default)**: Passes arguments identically to the native Robocopy utility.
  ```bash
  pyrobocopy C:\Data D:\Backup /S /E /MT:32 /XO
  ```
- **`python`**: Uses a pure Python argparse interface with explicit flags (and short aliases mapped to the Windows flags).
  ```bash
  pyrobocopy --backend=python C:\Data D:\Backup --subdirs --multi-threaded 32 --exclude-older
  # Or using shorthands:
  pyrobocopy --backend=python C:\Data D:\Backup -s -mt 32 -xo
  ```

Run `pyrobocopy help` or `pyrobocopy --backend=python -h` for full usage details.

## Reference

### `RobocopyConfig`
- **`copy`**: Subdirectories, restartable mode, mirror, threads, etc.
- **`selection`**: Exclude files/dirs, filter by age/attributes.
- **`logging`**: Verbosity, timestamps, UI suppression.

### `RobocopyResult`
- **`stats`**: Summary counts for Dirs, Files, and Bytes.
- **`errors`**: List of captured Windows errors (e.g., "Access Denied").
- **`exit_code`**: The raw Robocopy bitwise exit code.

## Performance Note
The **Smart Progress** feature involves a pre-scan (`/L`) of the source/destination. While extremely fast on local NVMe/SSD storage, it may introduce a small delay on high-latency network shares. Use `smart_progress=False` for instant execution on massive network trees if the percentage bar is not required.
