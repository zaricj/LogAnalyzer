from datetime import datetime
from pathlib import Path

def str_to_path(object: str) -> Path:
    """If the object is of type 'str', it gets converted to an object of type 'Path' of the pathlib module.

    Args:
        object (str): Object of type 'str'.

    Returns:
        Path: The converted object as the 'Path' type.
    """
    if isinstance(object, str):
        object = Path(object)
        return object
    else:
        return object
    

def epoch_to_timestamp(epoch_time: float) -> str:
    """
    Converts epoch time (in seconds) and formats it as DD.MM.YYYY - HH:MM:SS.

    Args:
        epoch_time_sec: The epoch time in seconds.

    Returns:
        A string representing the formatted date,
        or an error message if the input is invalid.
    """
    try:
        # Create a datetime object from the epoch time
        dt_object = datetime.fromtimestamp(epoch_time)
        # Format the datetime object as DD.MM.YYYY - HH:MM:SS
        formatted_time = dt_object.strftime('%d.%m.%Y - %H:%M:%S')
        return formatted_time
    except (TypeError, ValueError) as e:
        return f"Error: Invalid epoch time provided. {e}"