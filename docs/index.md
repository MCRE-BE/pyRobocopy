---
hide:
  - navigation
---

# pyRobocopy

A high-performance, object-oriented Python wrapper for the Windows `robocopy` utility. This library is designed to replace slow Python-level file synchronization with fast, robust, OS-level execution.

## Key Features

- **Smart Progress Tracking**: Automatically performs a discovery pass to determine the total file count for accurate percentage-based progress bars.
- **Structured Configuration**: Over 70+ Robocopy flags organized into logical categories (Copy, Selection, Logging).
- **Command-Line Parsing**: Initialize full configuration objects directly from raw Robocopy command strings.
- **Multithreading**: Full support for Robocopy's multi-thread (`/MT`) engine.
- **Rich Results**: Programmatic access to outcome statistics and error mapping for Windows System Errors.
