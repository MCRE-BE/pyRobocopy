# Shared Project Context & Standards (Global)

**Common Location:** `C:\Users\PBE00A26\Python_Code\.gemini\GEMINI.md`
**Hardlinked to:**
- `Python_Code\GEMINI.md` (Global)
- `dll-danda-ibp-scripts\GEMINI.md`
- `pyRobocopy\GEMINI.md`
- `ntfy_lite\GEMINI.md`

## Tech Stack & Tooling
- **Language**: Python 3.13+ (unless specified otherwise).
- **Environment**: Use `uv` for all dependency management and execution.
- **Linting & Formatting**:
  - **Ruff**: Always run `uv run ruff check --fix` and `uv run ruff format` after editing.

## Engineering Standards

- **Python Style**:
  - **Documentation**: Use **NumPy docstring** convention for all public classes and functions.
  - **Formatting**: Use **trailing commas** for multi-line lists/parameters to force clean diffs.
  - **Safety**: Prefer **named arguments** over positional ones for clarity.
  - **Types**: Use strict type annotations for all new code. Favor `typing.Self` and standard collections (`list`, `dict`).
  - **Paths**: Use `pathlib.Path` exclusively.

- **Git Workflow**:
  - Use **Conventional Commits** (`feat:`, `fix:`, `docs:`, etc.).
  - **Branching**: Never commit directly to `master` or `main`. Use feature branches and merge-based workflows.

---

## Repository Specifics

### [1] dll-danda-ibp-scripts (Monorepo)
- Core logic for ETL, IBPM, and Argos synchronization.
- **Note**: This monorepo consumes `ntfy_lite` and `pyRobocopy` as external dependencies.

### [2] pyRobocopy (Standalone)
- Windows-specific Robocopy wrapper.
- Hosted at: `https://github.com/MCRE-BE/pyRobocopy.git`
- **Installation**: `uv add git+https://github.com/MCRE-BE/pyRobocopy.git`

### [3] ntfy_lite (Standalone)
- Minimalism Python API for ntfy.sh.
- Hosted at: `https://github.com/MCRE-BE/ntfy_lite.git`
- **Installation**: `uv add git+https://github.com/MCRE-BE/ntfy_lite.git`

### [4] becse-adp-dllgsc
- Data Product for BeCSE ADP Dllgsc.
- Domain: Data engineering and transformation on Databricks using `dbt`.
- Tech: Python 3.10, dbt, SQL (databricks dialect), Azure infrastructure.

# Gemini Agent Instructions

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately.
- Use plan mode for verification steps, not just building.
- Write detailed specs upfront to reduce ambiguity.

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean.
- Offload research, exploration, and parallel analysis to subagents.
- For complex problems, throw more compute at it via subagents.
- One task per subagent for focused execution.

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern.
- Write rules for yourself that prevent the same mistake.
- Ruthlessly iterate on these lessons until mistake rate drops.
- Review lessons at session start for relevant project.

### 4. Verification Before Done
- Never mark a task complete without proving it works.
- Diff behavior between main and your changes when relevant.
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness.

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution."
- Skip this for simple, obvious fixes -- don't over-engineer.
- Challenge your own work before presenting it.

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests -- then resolve them.
- Zero context switching required from the user.
- Go fix failing CI tests without being told how.

## Task Management
1. **Plan First**: Write plan to `tasks/todo.md` with checkable items.
2. **Verify Plan**: Check in before starting implementation.
3. **Track Progress**: Mark items complete as you go.
4. **Explain Changes**: High-level summary at each step.
5. **Document Results**: Add review section to `tasks/todo.md`.
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections.

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Only touch what's necessary. No side effects with new bugs.
