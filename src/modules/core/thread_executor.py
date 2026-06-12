from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable
import os

"""
Threading sample usage:

    files = get_files_in_folder("logs")
    
    # Use executor.map() to parallelize work on multiple files
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(file_info, files))
        
    # Do something with the results list
"""

def run_with_threading(func: Callable, iterable: Iterable, max_workers: int = None) -> list:
    """Runs a function in parallel on an iterable of inputs using a thread pool.
    Args:
        func (callable): The function to be executed in parallel.
        iterable (iterable): The collection of inputs to pass to the function.
        max_workers (int, optional): The maximum number of threads to use. Defaults to None, which means the number of threads is determined by the system.
    Returns:
        list: A list of results from executing the function on each input in the iterable.

    Raises:
        Exception: Any exception raised by the function being executed.
    """
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 5)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, iterable))