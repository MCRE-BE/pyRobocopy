"""Orchestration logic for running Robocopy processes."""

# %%
####################
# Import Statement #
####################
from __future__ import annotations

import logging
import subprocess

from tqdm.auto import tqdm

from .config import RobocopyConfig
from .error import NothingToLoadError
from .parser import RobocopyParser
from .types import RobocopyResult, RobocopyStatistics, StatRow


###########
# CLASSES #
###########
class RobocopyRunner:
    """Master class for orchestrating Robocopy runs.

    Parameters
    ----------
    config : RobocopyConfig
        The configuration for the copy operation.
    """

    def __init__(self, config: RobocopyConfig, logger: logging.Logger | None = None):
        self.config = config
        self.log = logger or logging.getLogger("robocopy")

    def discover_totals(self) -> int:
        """Run a dry-run with high parallelism to find total file count.

        Returns
        -------
        int
            The total number of files reported in the 'Total' column.
        """
        args = self.config.to_args()
        # Add discovery flags
        args.extend(
            [
                "/L",
                "/NFL",  # (No File List)
                "/NDL",  # (No Directory List)
                "/NJH",
                "/R:0",
                "/W:0",
                "/MT:32",
            ],
        )

        proc = subprocess.run(  # noqa: S603
            args,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )

        idx = proc.stdout.rfind("Files :")
        if idx != -1:
            end_idx = proc.stdout.find("\n", idx)
            if end_idx == -1:
                end_idx = len(proc.stdout)
            line = proc.stdout[idx:end_idx]
            parts = line.split()
            try:
                return int(parts[2])
            except (IndexError, ValueError):
                return 0
        return 0

    def run(
        self,
        smart_progress: bool = False,
    ) -> RobocopyResult:
        """Execute the robocopy command.

        Parameters
        ----------
        smart_progress : bool
            If True, performs a discovery pass to enable accurate percentage tracking.

        Returns
        -------
        RobocopyResult
            Structured outcome of the run.

        Raises
        ------
        NothingToLoadError
            If source directory does not exist.
        """
        if not self.config.source.exists():
            raise NothingToLoadError(f"Source {self.config.source} does not exist.")

        total_files = 0
        if smart_progress:
            self.log.info("Calibrating progress bar (discovery phase)...")
            total_files = self.discover_totals()
            self.log.info(f"Discovered {total_files} files to process.")

        args = self.config.to_args()
        parser = RobocopyParser(
            config=self.config,
        )
        result = RobocopyResult(
            config=self.config,
            exit_code=0,
        )

        pbar = None
        if smart_progress:
            pbar = tqdm(
                total=total_files,
                unit="file",
                desc=f"Sync {self.config.source.name}",
            )

        try:
            with subprocess.Popen(  # noqa: S603
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
            ) as proc:
                self._process_output_stream(
                    proc=proc,
                    parser=parser,
                    result=result,
                    pbar=pbar,
                )
                proc.wait()
                result.exit_code = proc.returncode
        except Exception as e:
            self.log.error("Robocopy run failed fatally.", exc_info=True)
            result.errors.append(str(e))
            result.exit_code = 16

        if pbar:
            pbar.close()

        if not result.success:
            self.log.error(f"Robocopy failed with exit code {result.exit_code}")

        return result

    def _process_line(
        self,
        line: str,
        parser: RobocopyParser,
        result: RobocopyResult,
        pbar: tqdm | None,
    ) -> None:
        """Process a single line from the robocopy output stream.

        Parameters
        ----------
        line : str
            The line to process.
        parser : RobocopyParser
            The parser for extracting information.
        result : RobocopyResult
            The result object to populate.
        pbar : tqdm, optional
            The progress bar to update.
        """
        parsed = parser.parse_line(
            line=line,
        )
        if isinstance(parsed, str):
            if parsed.startswith("Error"):
                result.errors.append(parsed)
            elif parsed == "SUMMARY_START":
                self.log.info("[Robocopy] Total\tCopied\tSkipped\tMismatched\tFAILED\tExtras")
                return
            elif parser.stats_found and ":" in parsed:
                self._parse_stat_row(
                    line=parsed,
                    stats=result.stats,
                )
                self.log.info(f"[Robocopy] {parsed}")

        if pbar and "100%" in line:
            pbar.update(1)

    def _process_output_stream(
        self,
        proc: subprocess.Popen,
        parser: RobocopyParser,
        result: RobocopyResult,
        pbar: tqdm | None,
    ) -> None:
        """Read and parse the robocopy output stream in real-time.

        Parameters
        ----------
        proc : subprocess.Popen
            The running robocopy process.
        parser : RobocopyParser
            The parser for extracting information from lines.
        result : RobocopyResult
            The result object to populate with errors and stats.
        pbar : tqdm, optional
            The progress bar to update.
        """
        if not proc.stdout:
            return

        for line in proc.stdout:
            self._process_line(
                line=line,
                parser=parser,
                result=result,
                pbar=pbar,
            )

    def _parse_stat_row(
        self,
        line: str,
        stats: RobocopyStatistics,
    ) -> None:
        """Parse a single line of the Robocopy summary table.

        Parameters
        ----------
        line : str
            Formatted line from the summary table.
        stats : RobocopyStatistics
            Statistics object to update.
        """
        parts = line.split()
        if len(parts) < 7:
            return

        try:
            row = StatRow(
                total=int(parts[2]),
                copied=int(parts[3]),
                skipped=int(parts[4]),
                mismatched=int(parts[5]),
                failed=int(parts[6]),
                extras=int(parts[7]),
            )
            if "Dirs :" in line:
                stats.dirs = row
            elif "Files :" in line:
                stats.files = row
            elif "Bytes :" in line:
                stats.bytes = row
        except (ValueError, IndexError):
            pass
