"""
This module contains utilities and functions for handling and processing
various payload formats. It provides functionalities to encode, decode,
and manipulate data structures for use in different application contexts.

Classes, functions, and tools defined in this module are optimized for
working with structured data commonly used in API payloads or data
serialization.

Author: [Your Name]
Date: [Today's Date]
Project: [Your Project Name]
"""
from enum import Enum, auto


class PayloadFormat(Enum):
    """
    Enumeration representing different payload formats.

    Provides enumeration members to denote different formats, which can be
    used for defining or parsing payload data in respective formats.
    """
    RAW = auto()
    JSON = auto()
