"""
Data parsing utilities
Pure functions with no external dependencies
"""

import io
import pandas as pd
from typing import Union


def robust_csv_parser(data_input: Union[str, io.BytesIO]) -> pd.DataFrame:
    """
    Parses CSV-like data from a string or uploaded file using pandas' auto-detection.

    Args:
        data_input: String or file-like object containing CSV data

    Returns:
        pd.DataFrame: Parsed data

    Raises:
        ValueError: If data cannot be parsed
    """
    if hasattr(data_input, 'getvalue'):
        text_data = data_input.getvalue().decode('utf-8')
    else:
        text_data = str(data_input)

    csv_file = io.StringIO(text_data)
    # Use sep=None and engine='python' to auto-detect separators
    df = pd.read_csv(csv_file, sep=None, engine='python')
    return df
