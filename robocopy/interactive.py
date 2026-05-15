"""Interactive TUI for Robocopy configuration using Textual."""

import contextlib
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

from .config import RobocopyConfig
from .runner import RobocopyRunner


class RobocopyInteractive(App[None]):
    """A polished and compact Textual app for interactive Robocopy configuration."""

    CSS_PATH: ClassVar[str] = "interactive.tcss"
    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
    ]

    command_str = reactive("robocopy ...")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
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
                                    ("Subdirs (/S)", "S", "Copy Subdirectories, but not empty ones."),
                                    ("Empty (/E)", "E", "Copy subdirectories, including Empty ones."),
                                    ("Restart (/Z)", "Z", "Copy files in restartable mode."),
                                    ("Backup (/B)", "B", "Copy files in Backup mode."),
                                    (
                                        "Mirror (/MIR)",
                                        "MIR",
                                        "Mirror a directory tree (equivalent to /E plus /PURGE).",
                                    ),
                                    (
                                        "Purge (/PURGE)",
                                        "PURGE",
                                        "Delete dest files/dirs that no longer exist in source.",
                                    ),
                                    ("FAT (/FFT)", "FFT", "Assume FAT File Times (2-second granularity)."),
                                ],
                            )

                    with TabPane("Selection"), ScrollableContainer():
                        yield Label("Selection Filters", classes="section-title")
                        with Vertical(classes="option-group"):
                            yield from self._compact_options(
                                [
                                    ("Older (/XO)", "XO", "Exclude Older files."),
                                    ("Extra (/XX)", "XX", "Exclude Extra files and directories."),
                                    ("Archive (/A)", "A", "Copy only files with the Archive attribute set."),
                                    (
                                        "Reset (/M)",
                                        "M",
                                        "Copy only files with Archive attribute and reset it.",
                                    ),
                                ],
                            )

                    with TabPane("Logging"), ScrollableContainer():
                        yield Label("Output & Logging", classes="section-title")
                        with Vertical(classes="option-group"):
                            yield from self._compact_options(
                                [
                                    ("Verbose (/V)", "V", "Produce verbose output, showing skipped files."),
                                    ("NoFile (/NFL)", "NFL", "No File List - don't log file names."),
                                    ("NoDir (/NDL)", "NDL", "No Directory List - don't log directory names."),
                                    ("Time (/TS)", "TS", "Include source file Timestamps in the output."),
                                    ("Path (/FP)", "FP", "Include Full Pathname of files in the output."),
                                    ("Bytes (/BYTES)", "BYTES", "Print sizes as bytes."),
                                    ("Tee (/TEE)", "TEE", "Output to console window, as well as the log file."),
                                ],
                            )

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

    def _compact_options(self, options: list[tuple[str, str, str]]) -> ComposeResult:
        """Create a list of horizontal option rows."""
        for label, flag, desc in options:
            with Horizontal(classes="compact-option"):
                with Vertical(classes="label-container"):
                    yield Label(label, classes="compact-label")
                    yield Label(desc, classes="compact-desc")
                yield Switch(id=f"flag-{flag}")

    def on_mount(self) -> None:
        """Initialize command on mount."""
        self.handle_generate(None)

    def watch_command_str(self, new_val: str) -> None:
        """Update the UI when command_str changes."""
        with contextlib.suppress(Exception):
            self.query_one("#command-text", Static).update(new_val)

    def _get_path_parts(self) -> list[str]:
        """Get the base path and file filter parts of the command."""
        source = self.query_one("#input-source", Input).value
        destination = self.query_one("#input-destination", Input).value
        files = self.query_one("#input-files", Input).value or "*.*"
        return ["robocopy", f'"{source}"', f'"{destination}"', files]

    def _get_flag_parts(self) -> list[str]:
        """Get the active flags from all switches."""
        flags = []
        for switch in self.query(Switch):
            if switch.value and switch.id and switch.id.startswith("flag-"):
                flag = f"/{switch.id.replace('flag-', '')}"
                flags.append(flag)
        return flags

    @on(Button.Pressed, "#btn-generate-cmd")
    def handle_generate(self, _event: Button.Pressed | None) -> None:
        """Construct the command and update the reactive string when button is pressed."""
        with contextlib.suppress(Exception):
            parts = self._get_path_parts() + self._get_flag_parts()
            self.command_str = " ".join(parts)

    @on(Button.Pressed, "#btn-run")
    def handle_execute(self, event: Button.Pressed) -> None:
        """Handle the Execute Sync button press."""
        event.button.disabled = True
        self.notify("Starting Robocopy sync...", title="Sync Started")
        self.execute_sync()

    @work(exclusive=True, thread=True)
    def execute_sync(self) -> None:
        """Run the Robocopy synchronization in a background thread."""
        try:
            # Re-generate command string to be absolutely sure we have latest UI state
            self.call_from_thread(self.handle_generate, None)
            # Build config from the command string
            config = RobocopyConfig.from_command_line(self.command_str)
            runner = RobocopyRunner(config)
            result = runner.run()
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
        """Clear the source input field."""
        with contextlib.suppress(Exception):
            self.query_one("#input-source", Input).value = ""

    @on(Button.Pressed, "#btn-clear-dest")
    def clear_dest(self, _event: Button.Pressed) -> None:
        """Clear the destination input field."""
        with contextlib.suppress(Exception):
            self.query_one("#input-destination", Input).value = ""

    @on(Button.Pressed, "#btn-clear-files")
    def clear_files(self, _event: Button.Pressed) -> None:
        """Clear the files input field."""
        with contextlib.suppress(Exception):
            self.query_one("#input-files", Input).value = ""

    async def action_quit(self) -> None:
        """Exit the app."""
        self.exit()


if __name__ == "__main__":  # pragma: no cover
    app = RobocopyInteractive()
    app.run()
