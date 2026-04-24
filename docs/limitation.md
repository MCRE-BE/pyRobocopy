---
hide:
  - navigation
---
# Limitations and Performance

## Performance Note: Smart Progress

The **Smart Progress** feature involves a pre-scan (`/L`) of the source and destination directories.

- **Local Storage**: On local NVMe or SSD storage, this scan is extremely fast.
- **Network Shares**: On high-latency network shares, the pre-scan may introduce a noticeable delay before the copy starts.

### Recommendation
For massive directory trees on network shares where a progress bar is not strictly required, use `smart_progress=False` for instant execution.

## Compatibility
- **OS**: Windows (Required for the underlying `robocopy.exe`).
- **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14.
