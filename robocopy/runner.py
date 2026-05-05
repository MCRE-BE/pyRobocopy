"""Orchestration logic for running Robocopy processes."""

# %%
####################
# Import Statement #
####################
import logging
import subprocess

from tqdm.auto import tqdm

from .config import RobocopyConfig
from .error import NothingToLoadError
from .parser import RobocopyParser
from .types import FileResult, RobocopyResult, RobocopyStatistics, RobocopyStatus, StatRow


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
        lines = proc.stdout.splitlines()

        for line in reversed(lines):
            if "Files :" in line:
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
        # 1. Validation
        self._validate_source()

        # 2. Preparation
        total_files = self._get_total_files(smart_progress)
        args = self.config.to_args()
        if smart_progress and "/V" not in [a.upper() for a in args]:
            args.append("/V")
        parser = RobocopyParser(config=self.config)
        result = RobocopyResult(config=self.config, exit_code=0)
        pbar = self._init_progress_bar(smart_progress, total_files)

        # 3. Execution
        self._execute_robocopy(args, parser, result, pbar)

        # 4. Cleanup
        if pbar:
            pbar.close()

        if not result.success:
            self.log.error(f"Robocopy failed with exit code {result.exit_code}")

        return result

    def _validate_source(self) -> None:
        """Validate that the source directory exists.

        Raises
        ------
        NothingToLoadError
            If source directory does not exist.
        """
        if not self.config.source.exists():
            raise NothingToLoadError(f"Source {self.config.source} does not exist.")

    def _get_total_files(self, smart_progress: bool) -> int:
        """Get total files for progress tracking if enabled.

        Parameters
        ----------
        smart_progress : bool
            Whether smart progress is enabled.

        Returns
        -------
        int
            Total file count.
        """
        if smart_progress:
            self.log.info("Calibrating progress bar (discovery phase)...")
            total_files = self.discover_totals()
            self.log.info(f"Discovered {total_files} files to process.")
            return total_files
        return 0

    def _init_progress_bar(self, smart_progress: bool, total_files: int) -> tqdm | None:
        """Initialize progress bar if smart progress is enabled.

        Parameters
        ----------
        smart_progress : bool
            Whether smart progress is enabled.
        total_files : int
            Total number of files.

        Returns
        -------
        tqdm | None
            Progress bar instance or None.
        """
        if smart_progress:
            return tqdm(
                total=total_files,
                unit="file",
                desc=f"Sync {self.config.source.name}",
            )
        return None

    def _execute_robocopy(
        self,
        args: list[str],
        parser: RobocopyParser,
        result: RobocopyResult,
        pbar: tqdm | None,
    ) -> None:
        """Execute the robocopy subprocess and process its output.

        Parameters
        ----------
        args : list[str]
            Command line arguments.
        parser : RobocopyParser
            The parser for extracting information from lines.
        result : RobocopyResult
            The result object to populate.
        pbar : tqdm | None
            The progress bar to update.
        """
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
            parsed = parser.parse_line(
                line=line,
            )
            self._handle_parsed_line(parsed, result, pbar, line)

    def _handle_parsed_line(
        self,
        parsed: FileResult | str | None,
        result: RobocopyResult,
        pbar: tqdm | None,
        raw_line: str,
    ) -> None:
        """Handle a single parsed line and update result/progress.

        Parameters
        ----------
        parsed : FileResult | str | None
            The parsed result from the line.
        result : RobocopyResult
            The result object to update.
        pbar : tqdm | None
            The progress bar to update.
        raw_line : str
            The raw line for fallback checks.
        """
        if isinstance(parsed, str):
            self._handle_string_parsed(parsed, result)
        elif isinstance(parsed, FileResult):
            self._handle_file_result_parsed(parsed, pbar)
        elif pbar and "100%" in raw_line:
            # Fallback for large files without MT
            pbar.update(1)

    def _handle_string_parsed(self, parsed: str, result: RobocopyResult) -> None:
        """Handle a string-parsed result (errors, summary markers, etc.)."""
        if parsed.startswith("Error"):
            result.errors.append(parsed)
            self.log.error(f"[Robocopy] {parsed}")
        elif parsed.startswith("RETRY_WAIT:"):
            wait_time = parsed.split(":")[1]
            self.log.warning(f"[Robocopy] Retrying in {wait_time} seconds...")
        elif parsed == "SUMMARY_START":
            self.log.info("[Robocopy] Total\tCopied\tSkipped\tMismatched\tFAILED\tExtras")
        elif self.parser_context_found_stats(parsed):
            self._parse_stat_row(
                line=parsed,
                stats=result.stats,
            )
            self.log.info(f"[Robocopy] {parsed}")

    def _handle_file_result_parsed(self, parsed: FileResult, pbar: tqdm | None) -> None:
        """Handle a FileResult-parsed result (file copied, skipped, etc.)."""
        if pbar:
            if parsed.status.counts_towards_total:
                pbar.update(1)
            if "Dir" in parsed.status.value:
                pbar.set_postfix(dir=parsed.source_path.name, refresh=True)

        if parsed.status == RobocopyStatus.FAILED:
            self.log.warning(f"[Robocopy] Failed to process: {parsed.source_path}")

    def parser_context_found_stats(self, parsed: str) -> bool:
        """Helper to check if stats are found in the current context."""
        # This is a bit of a hack since we don't have easy access to parser.stats_found here
        # without passing the parser, but we can check the prefix.
        return any(parsed.startswith(s) for s in ["Dirs :", "Files :", "Bytes :"])

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
