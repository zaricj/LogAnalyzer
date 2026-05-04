from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import MainWindow


class ComboBoxEventHandler:
    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui

        # Init combobox
        self.populate_patterns_combobox()  # Fill the combobox with the available pattern configuration files

    def connect_signals(self):
        """Connect all combobox events to their handlers."""
        self.ui.combobox_configuration.currentTextChanged.connect(self.load_pattern)
        self.ui.combobox_time.currentTextChanged.connect(
            self.filter_file_content_by_date_time
        )

    # ===== UI Events =====

    def populate_patterns_combobox(self):
        profiles = self.main_window.log_pattern_handler.get("profiles")
        if isinstance(profiles, dict) and profiles:
            combobox = self.ui.combobox_configuration
            default_profile = self.main_window.log_pattern_handler.get("default_profile")
            combobox.clear()
            combobox.addItems(sorted(profiles.keys()))
            if isinstance(default_profile, str) and default_profile in profiles:
                combobox.setCurrentText(default_profile)
            selected_profile = combobox.currentText()
            self.ui.text_edit_program_output.setText(
                f"Loaded pattern profiles: {', '.join(sorted(profiles.keys()))}\n"
                f"Selected profile: {selected_profile}"
            )
        else:
            self.ui.text_edit_program_output.setText(
                "No parser profiles found under 'profiles' in log_patterns.json."
            )

    @Slot(str)
    def load_pattern(self, profile_name: str) -> None:
        self.ui.statusbar.showMessage(f"Selected parser profile: {profile_name}", 5000)

    @Slot(str)
    def filter_file_content_by_date_time(self, selected_date_time: str) -> None:
        file_content = self.main_window.dir_viewer.get_current_preview_content()
        if not file_content:
            return
        self.show_file_content_data_by_date(file_content, selected_date_time)

    def show_file_content_data_by_date(
        self, file_content: str, selected_date: str
    ) -> list[str]:
        selected_date = selected_date.strip()
        if not selected_date or selected_date == "All":
            self.ui.text_edit_log_preview.setPlainText(file_content)
            self.ui.text_edit_program_output.setText(
                "Loaded full log preview (no date/time filter)."
            )
            return file_content.splitlines()

        if ":" in selected_date:
            filtered_lines = [
                line for line in file_content.splitlines() if selected_date in line
            ]
        else:
            filtered_lines = [
                line
                for line in file_content.splitlines()
                if line.lstrip().startswith(selected_date)
            ]

        try:
            if self.ui.combobox_time.count() > 0:
                if filtered_lines:
                    self.ui.text_edit_log_preview.setPlainText(
                        "\n".join(filtered_lines)
                    )
                    self.ui.text_edit_program_output.setText(
                        f"Loaded log entries for selected value '{selected_date}' in file view."
                    )
                else:
                    self.ui.text_edit_log_preview.clear()
                    self.ui.text_edit_program_output.setText(
                        f"No log entries matched selected value '{selected_date}'."
                    )
            else:
                self.ui.text_edit_program_output.clear()
        except Exception as ex:
            self.ui.statusbar.showMessage(
                f"An error occurred while displaying the log entries: {str(ex)}", 10000
            )
        return filtered_lines
