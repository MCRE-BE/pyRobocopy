# pyRobocopy: Monorepo Sync Guide

This document describes the workflow for keeping the standalone `pyRobocopy` repository in sync with the `dll-danda-ibp-scripts` monorepo.

> [!IMPORTANT]
> This repository uses **no-squash** sync to preserve every single commit in both repositories. Ensure you do NOT use the `--squash` flag when performing subtree operations.

## 1. Prerequisites
You should have both repositories cloned locally and configured as remotes in your working environment.

In your **monorepo** folder:
```bash
git remote add robocopy_standalone https://github.com/MCRE-BE/pyRobocopy.git
```

## 2. Syncing Workflow

### Pulling into Monorepo (Most Common)
To bring the latest changes from this standalone repo into the monorepo:

1.  **Switch to your target branch** in the monorepo (e.g., `master` or a feature branch).
2.  **Run the subtree pull**:
    ```bash
    git subtree pull --prefix=libs/robocopy robocopy_standalone main
    ```
3.  **Resolve conflicts** (if any) and commit.

### Pushing from Monorepo back to Standalone
If you've made a fix inside the monorepo and want to bring it here:

1.  **In the monorepo**, push the folder changes to a temporary branch:
    ```bash
    git subtree push --prefix=libs/robocopy robocopy_standalone feature/from-monorepo
    ```
2.  **In this standalone repo**, merge that fix:
    ```bash
    git fetch origin
    git merge feature/from-monorepo
    ```

---

## 3. Best Practices & Principles

### Why no-squash?
By avoiding the `--squash` flag, we ensure that:
- **Full History**: Every individual commit message and author metadata is preserved in the monorepo.
- **Traceability**: You can see exactly when and why each line changed, even if the work was done in the standalone repo.

### Consistent Usage
Once a subtree is established without squash, it is critical to **never** use the `--squash` flag in subsequent pull or push operations, as mixing the two can lead to duplicate commits and merge conflicts.
