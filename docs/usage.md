---
hide:
  - navigation
---
# Usage

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
