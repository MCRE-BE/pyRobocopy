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

## Windows Only
As this library is a wrapper around the Windows `robocopy` utility, it is only compatible with Windows environments.
