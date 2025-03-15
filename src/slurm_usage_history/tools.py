import functools
import re
import time
from datetime import datetime, timedelta

import pandas as pd


def natural_sort_key(s):
    """
    Natural sorting function that handles numeric parts in strings properly.
    For example: "cpu2" will come before "cpu11" with natural sorting.

    Args:
        s: String to convert to a natural sort key

    Returns:
        A list that can be used as a sort key with proper numeric ordering
    """
    # If the input is not a string (e.g., None or already numeric), return it
    if not isinstance(s, str):
        return s

    # Split the string into text and numeric parts
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def get_time_column(date_str1, date_str2):
    """
    Calculate the timespan in days between two dates provided in ISO format strings.

    Args:
        date_str1 (str): The first date in ISO format (YYYY-MM-DD).
        date_str2 (str): The second date in ISO format (YYYY-MM-DD).

    Returns:
        int: The number of days between the two dates.
    """
    # Parse the input strings into datetime objects
    date1 = datetime.strptime(date_str1, "%Y-%m-%d")
    date2 = datetime.strptime(date_str2, "%Y-%m-%d")

    # Calculate the difference in days
    timespan = abs((date2 - date1).days)

    if timespan < 66:
        return "SubmitDay"
    if timespan < (365 * 1.5):
        return "SubmitYearWeek"
    return "SubmitYearMonth"


def week_to_date(year_week_str):
    # Parse the year and week from the input string
    year, week = map(int, year_week_str.split("-"))

    # Define the first day of the year
    first_day_of_year = datetime(year, 1, 1)

    # Find the start of the first week (Monday)
    first_week_start = first_day_of_year - timedelta(days=first_day_of_year.weekday())

    # Calculate the start date of the given week
    return first_week_start + timedelta(weeks=week - 1)


def month_to_date(year_month_str):
    # Parse the year and month from the input string
    year, month = map(int, year_month_str.split("-"))

    # Construct the first day of the given month
    return datetime(year, month, 1)


def print_column_info_in_markdown(df: pd.DataFrame):
    """
    Prints the column data types and an example value for each
    column in markdown format.

    Parameters:
        df (pd.DataFrame): The dataframe to inspect.
    """

    # Create a list to store the column data type and example value
    column_info = []

    for column in df.columns:
        dtype = df[column].dtype
        example_value = df[column].iloc[0]  # Get the first value as example
        column_info.append([column, str(dtype), example_value])

    # Create a DataFrame from the list to display in markdown format
    column_info_df = pd.DataFrame(column_info, columns=["Column", "Data Type", "Example Value"])

    # Print the markdown representation of the dataframe
    print(column_info_df.to_markdown(index=False))


def categorize_time(hours):
    """
    Categorize time in hours into predefined categories.

    Args:
    - hours (float or int): Time in hours to categorize.

    Returns:
    - str: The category corresponding to the given time.
    """
    if hours < (5 / 3600):
        return "<5s"
    if hours < (1 / 60):
        return "<1min"
    if hours < (5 / 60):
        return "<5min"
    if hours < (30 / 60):
        return "<30min"
    if hours < 1:
        return "<1h"
    if hours < 5:
        return "<5h"
    if hours < 10:
        return "<10h"
    if hours < 24:
        return "<24h"
    # > 24 hours
    return ">=24h"


def categorize_time_series(hours_series):
    """
    Categorize a Pandas Series of time in hours into predefined categories.

    Args:
    - hours_series (pd.Series): A Pandas Series with time in hours.

    Returns:
    - pd.Series: A Pandas Series of categorical type with the corresponding categories.
    """
    categories = [
        "<5s",
        "<1min",
        "<15min",
        "<30min",
        "<1h",
        "<5h",
        "<10h",
        "<24h",
        ">=24h",
    ]
    bins = [0, 5 / 3600, 1 / 60, 15 / 60, 30 / 60, 1, 5, 10, 24, float("inf")]

    # Use pd.cut to bin and categorize
    categorized_series = pd.cut(hours_series, bins=bins, labels=categories, right=False, ordered=True)

    return categorized_series.astype("category")


def unpack_nodelist_string(nodelist_str):
    """
    Unpacks a GPU string into a list of individual components.
    Handles ranges (e.g., gpu[08-09,11,14]) and single items (e.g., gpu16).
    """

    if not nodelist_str or nodelist_str == "None assigned":
        return []

    # Initialize a list to collect unpacked values
    unpacked_list = []

    # Match patterns for ranges and list items
    range_pattern = re.compile(r"(\d+)-(\d+)")
    list_pattern = re.compile(r"(\w+)\[(.*?)\]")

    # Check for list patterns (e.g., gpu[08-09,11,14])
    list_match = list_pattern.search(nodelist_str)
    if list_match:
        base, range_str = list_match.groups()
        ranges = range_str.split(",")
        for r in ranges:
            if "-" in r:
                start, end = map(int, r.split("-"))
                for num in range(start, end + 1):
                    unpacked_list.append(f"{base}{num:02d}")
            else:
                unpacked_list.append(f"{base}{r}")
    else:
        # If no list pattern, check if there are single items or other cases
        parts = nodelist_str.split(",")
        for part in parts:
            # Check for ranges in single items (e.g., gpu01,03])
            range_match = range_pattern.search(part)
            if range_match:
                base, _ = part.split("[")
                start, end = map(int, range_match.groups())
                for num in range(start, end + 1):
                    unpacked_list.append(f"{base}{num:02d}")
            else:
                # Handle regular items
                unpacked_list.append(part)

    # Ensure no invalid items like trailing ']'
    return [item.strip("]") for item in unpacked_list]


def timeit(func):
    """Measure execution time of a function."""

    @functools.wraps(func)
    def wrapper_timeit(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
        return result

    return wrapper_timeit
