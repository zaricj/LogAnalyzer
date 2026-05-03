import json
from pathlib import Path
from typing import Any


def validate_file(file: Path | str) -> bool:
    """
    Validate if the provided file path exists.

    Args:
        file: File path as a string or Path object.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(file).exists()


def load_app_settings(settings_file: Path | str) -> dict[str, Any]:
    """
    Load application settings from a JSON file.

    Args:
        settings_file: Path to the JSON settings file.

    Returns:
        A dictionary containing the loaded settings, or an empty dictionary
        if the file doesn't exist or contains invalid JSON.
    """
    try:
        with open(settings_file, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        return {}


def save_app_settings(settings_file: Path | str, settings: dict[str, Any]) -> None:
    """
    Save application settings to a JSON file.

    Args:
        settings_file: Path to the JSON settings file.
        settings: Dictionary containing settings to save.

    Note:
        If the file already exists, it will be overwritten.
        Errors are logged to stdout rather than raised.
    """
    try:
        with open(settings_file, "w") as file:
            json.dump(settings, file, indent=4, ensure_ascii=False)
    except (IOError, OSError, json.JSONEncodeError) as e:
        print(f"Error saving settings to {settings_file}: {e}")


def set_setting_values(
    settings_data: dict[str, Any], setting_key: str, new_setting_value: Any
) -> None:
    """
    Set a configuration value, handling nested keys using dot notation.

    This function modifies the settings_data dictionary in-place and also
    saves the updated configuration to disk.

    Args:
        settings_data: The settings dictionary to modify.
        setting_key: The setting name key path using dot notation
            (e.g., 'key' or 'section.subsection.key').
        new_setting_value: The new value to assign to the key.

    Returns:
        None (but updates settings_data in-place).

    Examples:
        >>> settings_data = {}
        >>> set_setting_values(settings_data, 'app_version', '1.0.0')
        # Resulting config: {"app_version": "1.0.0"}

        >>> settings_data = {"app_version": "1.0.0"}
        >>> set_setting_values(settings_data, 'custom_paths.docs', '/home/user/documents')
        # Resulting config: {
        #     "app_version": "1.0.0",
        #     "custom_paths": {
        #         "docs": "/home/user/documents"
        #     }
        # }
    """
    # Handle empty string key
    if not setting_key:
        return

    keys = setting_key.split(".")
    current = settings_data
    for i, key in enumerate(keys):
        if i == len(keys) - 1:  # Last key in the path
            current[key] = new_setting_value
        else:  # Not the last key, ensure it's a dictionary
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

    # Save updated configuration to disk
    save_app_settings(APP_SETTINGS_FILE, settings_data)


def get_setting_values(
    settings_data: dict[str, Any], setting_key: str, default: Any = None
) -> Any:
    """
    Get a settings value, handling nested keys using dot notation.

    Args:
        settings_data: The settings dictionary to read from.
        setting_key: The setting name key path using dot notation
            (e.g., 'section.subsection.key').
        default: The value to return if the key doesn't exist or path is invalid.

    Returns:
        The value associated with the setting key, or the default value
        if the key doesn't exist.

    Examples:
        >>> settings_data = {"app_version": "1.0.0"}
        >>> get_setting_values(settings_data, 'app_version')
        '1.0.0'

        >>> get_setting_values(settings_data, 'missing_key', 'N/A')
        'N/A'

        >>> settings_data = {"app_version": "1.0.0", "SavedTasksSetting": {"TaskName1": "HTTP Requests"}}
        >>> get_setting_values(settings_data, 'SavedTasksSetting.TaskName1')
        'HTTP Requests'
    """
    if not setting_key:
        return default

    keys = setting_key.split(".")
    current = settings_data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def get_all_setting_keys(
    settings_data: dict[str, Any], setting_key: str | None = None
) -> list[str]:
    """
    Get all keys from the settings dictionary.

    If `setting_key` is provided (e.g., 'custom_paths'), returns keys of
    that nested dictionary. Otherwise, returns all top-level keys.

    Args:
        settings_data: The settings dictionary to inspect.
        setting_key: Optional nested key path (e.g., 'custom_paths').
            If provided, returns keys under this path.
            If set to None, returns top-level keys.

    Returns:
        A list of string keys from the settings dictionary.

    Examples:
        >>> settings_data = {"app_version": "1.0.0", "custom": {"path": "/tmp"}}
        >>> get_all_setting_keys(settings_data)
        ['app_version', 'custom']

        >>> get_all_setting_keys(settings_data, 'custom')
        ['path']

        >>> get_all_setting_keys(settings_data, 'missing_key')
        []
    """
    if setting_key:
        nested_data = get_setting_values(settings_data, setting_key, {})
        if isinstance(nested_data, dict):
            return list(nested_data.keys())
        return []

    return list(settings_data.keys())


# Application settings file path
APP_SETTINGS_FILE: Path = (
    Path().cwd().absolute() / "src" / "settings" / "app_settings.json"
)

# ============================================================================
# Debugging / Testing section - uncomment for local testing
# ============================================================================
# data = load_app_settings(APP_SETTINGS_FILE)
# print("Loaded data:\n", data)
# print("\nKeys for SavedTasksSetting:\n", get_all_setting_keys(data, "SavedTasksSetting"))
# print("\nSetting value for SavedTasksSetting.TaskName1:\n",
#       get_setting_values(data, "SavedTasksSetting.TaskName1", {}))
