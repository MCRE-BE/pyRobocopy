"""Interactive TUI for Robocopy configuration using Textual."""

import contextlib
from pathlib import Path
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from .config import CopyOptions, LoggingOptions, RobocopyConfig, SelectionOptions
from .runner import RobocopyRunner


class RobocopyInteractive(App[None]):
    """A polished and compact Textual app for interactive Robocopy configuration."""

    CSS_PATH: ClassVar[str] = "interactive.tcss"
    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
    ]

    command_str = reactive("robocopy ...")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout.

        Returns
        -------
        ComposeResult
            The composed widgets for the application.
        """
        yield Header()
        with Container(id="main-container"):
            with Horizontal():
                # Left Panel: Paths
                with Vertical(id="path-panel"):
                    yield Label("PATHS", classes="section-title")

                    yield Label("Source Directory:")
                    with Horizontal(classes="input-group"):
                        yield Input(value="C:\\Source", id="input-source")
                        yield Button("X", id="btn-clear-source", classes="btn-clear")

                    yield Label("Destination Directory:")
                    with Horizontal(classes="input-group"):
                        yield Input(value="D:\\Destination", id="input-destination")
                        yield Button("X", id="btn-clear-dest", classes="btn-clear")

                    yield Label("File Filter (e.g. *.* or *.txt):")
                    with Horizontal(classes="input-group"):
                        yield Input(value="*.*", id="input-files")
                        yield Button("X", id="btn-clear-files", classes="btn-clear")

                    with Vertical(id="action-group"):
                        yield Button("🚀 Execute Sync", variant="success", id="btn-run")

                # Right Panel: Options
                with Vertical(id="options-panel"), TabbedContent(initial="tab-help"):
                    with TabPane("Copy"), ScrollableContainer():
                        yield Label("Copy Behavior Flags", classes="section-title")
                        with Vertical(classes="option-group"):
                            yield from self._compact_options(
                                [
                                    ("Subdirs (/S)", "S", "Copy Subdirectories, but not empty ones.", False),
                                    ("Empty (/E)", "E", "Copy subdirectories, including Empty ones.", False),
                                    ("Restart (/Z)", "Z", "Copy files in restartable mode.", False),
                                    ("Backup (/B)", "B", "Copy files in Backup mode.", False),
                                    (
                                        "Mirror (/MIR)",
                                        "MIR",
                                        "Mirror a directory tree (equivalent to /E plus /PURGE).",
                                        False,
                                    ),
                                    (
                                        "Purge (/PURGE)",
                                        "PURGE",
                                        "Delete dest files/dirs that no longer exist in source.",
                                        False,
                                    ),
                                    ("FAT (/FFT)", "FFT", "Assume FAT File Times (2-second granularity).", True),
                                ],
                            )
                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Multi-threaded (/MT)", classes="compact-label")
                                    yield Label("Number of concurrent threads (default: 8).", classes="compact-desc")
                                yield Input(value="8", id="input-flag-MT", classes="flag-input")

                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Copy Flags (/COPY)", classes="compact-label")
                                    yield Label(
                                        "What to copy (D:Data, A:Attributes, T:Timestamps, etc.) (default: DAT).",
                                        classes="compact-desc",
                                    )
                                yield Input(value="DAT", id="input-flag-COPY", classes="flag-input")

                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Dir Copy Flags (/DCOPY)", classes="compact-label")
                                    yield Label("What to copy for directories (default: DA).", classes="compact-desc")
                                yield Input(value="DA", id="input-flag-DCOPY", classes="flag-input")

                    with TabPane("Selection"), ScrollableContainer():
                        yield Label("Selection Filters", classes="section-title")
                        with Vertical(classes="option-group"):
                            yield from self._compact_options(
                                [
                                    ("Older (/XO)", "XO", "Exclude Older files.", True),
                                    ("Extra (/XX)", "XX", "Exclude Extra files and directories.", False),
                                    ("Archive (/A)", "A", "Copy only files with the Archive attribute set.", False),
                                    (
                                        "Reset (/M)",
                                        "M",
                                        "Copy only files with Archive attribute and reset it.",
                                        False,
                                    ),
                                ],
                            )
                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Exclude Files (/XF)", classes="compact-label")
                                    yield Label("Exclude files matching names/paths/wildcards.", classes="compact-desc")
                                yield Input(
                                    value="",
                                    placeholder="e.g. *.tmp thumb.db",
                                    id="input-flag-XF",
                                    classes="flag-input",
                                )

                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Exclude Dirs (/XD)", classes="compact-label")
                                    yield Label("Exclude directories matching names/paths.", classes="compact-desc")
                                yield Input(
                                    value="",
                                    placeholder="e.g. temp .git",
                                    id="input-flag-XD",
                                    classes="flag-input",
                                )

                    with TabPane("Logging"), ScrollableContainer():
                        yield Label("Output & Logging", classes="section-title")
                        with Vertical(classes="option-group"):
                            yield from self._compact_options(
                                [
                                    ("Verbose (/V)", "V", "Produce verbose output, showing skipped files.", False),
                                    ("NoFile (/NFL)", "NFL", "No File List - don't log file names.", False),
                                    ("NoDir (/NDL)", "NDL", "No Directory List - don't log directory names.", True),
                                    ("Time (/TS)", "TS", "Include source file Timestamps in the output.", False),
                                    ("Path (/FP)", "FP", "Include Full Pathname of files in the output.", False),
                                    ("Bytes (/BYTES)", "BYTES", "Print sizes as bytes.", True),
                                    ("NoJobHeader (/NJH)", "NJH", "No Job Header - don't log job header.", False),
                                    ("NoJobSummary (/NJS)", "NJS", "No Job Summary - don't log job summary.", False),
                                    ("Tee (/TEE)", "TEE", "Output to console window, as well as the log file.", False),
                                ],
                            )

                    with TabPane("Retry & Run"), ScrollableContainer():
                        yield Label("Retries & Progress", classes="section-title")
                        with Vertical(classes="option-group"):
                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Retry Count (/R)", classes="compact-label")
                                    yield Label(
                                        "Number of retries on failed copies (default: 3).",
                                        classes="compact-desc",
                                    )
                                yield Input(value="3", id="input-flag-R", classes="flag-input")

                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Retry Wait (/W)", classes="compact-label")
                                    yield Label(
                                        "Seconds to wait between retries (default: 3).",
                                        classes="compact-desc",
                                    )
                                yield Input(value="3", id="input-flag-W", classes="flag-input")

                            with Horizontal(classes="compact-option"):
                                with Vertical(classes="label-container"):
                                    yield Label("Smart Progress", classes="compact-label")
                                    yield Label(
                                        "Perform a discovery pass to track copy percentage.",
                                        classes="compact-desc",
                                    )
                                yield Switch(value=False, id="flag-smart-progress")

                    with TabPane("Help", id="tab-help"), ScrollableContainer():
                        yield Label("CLI & Usage Help", classes="section-title")
                        help_content = (
                            "Welcome to pyRobocopy Interactive Mode!\n\n"
                            "1. Select your Source and Destination paths on the left.\n"
                            "2. Use the 'Copy', 'Selection', and 'Logging' tabs to tweak options.\n"
                            "3. Click 'Generate' to preview the exact robocopy command.\n"
                            "4. Click 'Execute Sync' to start the actual transfer.\n\n"
                            "You can also run pyrobocopy from the terminal directly:\n"
                            "  pyrobocopy --backend=windows <source> <dest> /S /E\n"
                            "  pyrobocopy --backend=python <source> <dest> --subdirs"
                        )
                        yield Static(help_content, id="help-text")

            # Bottom: Command Preview
            with Vertical(id="command-preview-container"):
                with Horizontal(id="preview-header"):
                    yield Label("COMMAND PREVIEW", classes="section-title")
                    yield Button("🔄 Generate", variant="primary", id="btn-generate-cmd")
                yield Static(self.command_str, id="command-text")

        yield Footer()

    def _compact_options(self, options: list[tuple[str, str, str, bool]]) -> ComposeResult:
        """Create a list of horizontal option rows.

        Parameters
        ----------
        options : list[tuple[str, str, str, bool]]
            A list of 4-tuples (label, flag, desc, default_val).

        Yields
        ------
        ComposeResult
            Yields horizontal rows for options.
        """
        for label, flag, desc, default_val in options:
            with Horizontal(classes="compact-option"):
                with Vertical(classes="label-container"):
                    yield Label(label, classes="compact-label")
                    yield Label(desc, classes="compact-desc")
                yield Switch(value=default_val, id=f"flag-{flag}")

    def on_mount(self) -> None:
        """Initialize command on mount."""
        self.handle_generate(None)

    def watch_command_str(self, new_val: str) -> None:
        """Update the UI when command_str changes.

        Parameters
        ----------
        new_val : str
            The new command preview string.
        """
        with contextlib.suppress(Exception):
            self.query_one("#command-text", Static).update(new_val)

    def _build_config_from_ui(self) -> tuple[RobocopyConfig, bool]:
        """Build a RobocopyConfig directly from the active UI widgets.

        Returns
        -------
        tuple[RobocopyConfig, bool]
            A tuple of (config, smart_progress) containing the constructed config
            and a boolean indicating if smart progress is enabled.
        """
        source = Path(self.query_one("#input-source", Input).value)
        destination = Path(self.query_one("#input-destination", Input).value)
        files = self.query_one("#input-files", Input).value or "*.*"

        # Copy options
        copy_opts = CopyOptions(
            subdirs=self.query_one("#flag-S", Switch).value,
            empty_subdirs=self.query_one("#flag-E", Switch).value,
            restartable=self.query_one("#flag-Z", Switch).value,
            backup_mode=self.query_one("#flag-B", Switch).value,
            multi_threaded=int(self.query_one("#input-flag-MT", Input).value or 8),
            fat_file_times=self.query_one("#flag-FFT", Switch).value,
            copy_flags=self.query_one("#input-flag-COPY", Input).value or "DAT",
            dir_copy_flags=self.query_one("#input-flag-DCOPY", Input).value or "DA",
            purge=self.query_one("#flag-PURGE", Switch).value,
            mirror=self.query_one("#flag-MIR", Switch).value,
        )

        # Selection options
        exclude_files_str = self.query_one("#input-flag-XF", Input).value or ""
        exclude_dirs_str = self.query_one("#input-flag-XD", Input).value or ""
        exclude_files: list[str] = [str(x.strip()) for x in exclude_files_str.split() if x.strip()]
        exclude_dirs: list[str] = [str(x.strip()) for x in exclude_dirs_str.split() if x.strip()]

        sel_opts = SelectionOptions(
            exclude_older=self.query_one("#flag-XO", Switch).value,
            exclude_extra=self.query_one("#flag-XX", Switch).value,
            exclude_files=exclude_files,
            exclude_dirs=exclude_dirs,
            include_archive_only=self.query_one("#flag-A", Switch).value,
            reset_archive=self.query_one("#flag-M", Switch).value,
        )

        # Logging options
        log_opts = LoggingOptions(
            verbose=self.query_one("#flag-V", Switch).value,
            no_file_list=self.query_one("#flag-NFL", Switch).value,
            no_dir_list=self.query_one("#flag-NDL", Switch).value,
            show_timestamps=self.query_one("#flag-TS", Switch).value,
            full_pathnames=self.query_one("#flag-FP", Switch).value,
            bytes_as_integers=self.query_one("#flag-BYTES", Switch).value,
            no_job_header=self.query_one("#flag-NJH", Switch).value,
            no_job_summary=self.query_one("#flag-NJS", Switch).value,
            tee=self.query_one("#flag-TEE", Switch).value,
        )

        retry_count = int(self.query_one("#input-flag-R", Input).value or 3)
        retry_wait = int(self.query_one("#input-flag-W", Input).value or 3)
        smart_progress = self.query_one("#flag-smart-progress", Switch).value

        config = RobocopyConfig(
            source=source,
            destination=destination,
            files=files,
            copy=copy_opts,
            selection=sel_opts,
            logging=log_opts,
            retry_count=retry_count,
            retry_wait=retry_wait,
        )

        return config, smart_progress

    @on(Button.Pressed, "#btn-generate-cmd")
    def handle_generate(self, _event: Button.Pressed | None) -> None:
        """Construct the command and update the reactive string when button is pressed.

        Parameters
        ----------
        _event : Button.Pressed | None
            The event that triggered this handler, if any.
        """
        with contextlib.suppress(Exception):
            config, _ = self._build_config_from_ui()
            quoted_args = []
            for arg in config.to_args():
                if " " in arg and not arg.startswith('"') and not arg.endswith('"'):
                    quoted_args.append(f'"{arg}"')
                else:
                    quoted_args.append(arg)
            self.command_str = " ".join(quoted_args)

    @on(Button.Pressed, "#btn-run")
    def handle_execute(self, event: Button.Pressed) -> None:
        """Handle the Execute Sync button press.

        Parameters
        ----------
        event : Button.Pressed
            The button pressed event.
        """
        event.button.disabled = True
        self.notify("Starting Robocopy sync...", title="Sync Started")
        self.execute_sync()

    @work(exclusive=True, thread=True)
    def execute_sync(self) -> None:
        """Run the Robocopy synchronization in a background thread."""
        try:
            # Re-generate to ensure absolute synchronization
            self.call_from_thread(self.handle_generate, None)
            config, smart_progress = self._build_config_from_ui()
            runner = RobocopyRunner(config)
            result = runner.run(smart_progress=smart_progress)
            self.call_from_thread(
                self.notify,
                f"Sync completed with exit code {result.exit_code}",
                title="Sync Finished",
                severity="information" if result.exit_code < 8 else "error",
            )
        except Exception as e:
            self.call_from_thread(
                self.notify,
                f"Error during sync: {e}",
                title="Sync Failed",
                severity="error",
            )
        finally:
            self.call_from_thread(self._enable_run_button)

    def _enable_run_button(self) -> None:
        """Enable the run button after execution."""
        with contextlib.suppress(Exception):
            self.query_one("#btn-run", Button).disabled = False

    @on(Button.Pressed, "#btn-clear-source")
    def clear_source(self, _event: Button.Pressed) -> None:
        """Clear the source input field.

        Parameters
        ----------
        _event : Button.Pressed
            The button pressed event.
        """
        with contextlib.suppress(Exception):
            self.query_one("#input-source", Input).value = ""

    @on(Button.Pressed, "#btn-clear-dest")
    def clear_dest(self, _event: Button.Pressed) -> None:
        """Clear the destination input field.

        Parameters
        ----------
        _event : Button.Pressed
            The button pressed event.
        """
        with contextlib.suppress(Exception):
            self.query_one("#input-destination", Input).value = ""

    @on(Button.Pressed, "#btn-clear-files")
    def clear_files(self, _event: Button.Pressed) -> None:
        """Clear the files input field.

        Parameters
        ----------
        _event : Button.Pressed
            The button pressed event.
        """
        with contextlib.suppress(Exception):
            self.query_one("#input-files", Input).value = ""

    async def action_quit(self) -> None:
        """Exit the app."""
        self.exit()


if __name__ == "__main__":  # pragma: no cover
    app = RobocopyInteractive()
    app.run()
