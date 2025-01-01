"""
qos.py

This module is designed to handle operations related to Quality of Service (QoS) management.
It provides tools and utilities for prioritizing and managing data traffic to ensure
optimal performance and resource allocation in various network or system environments.

The module focuses on enabling QoS features such as bandwidth management, latency
optimization, and traffic prioritization. It is suitable for applications where efficient
resource utilization and service reliability are critical.

Dependencies:
- docutils
- pip
- pylint
- pytest
- requests
- wheel
"""

from enum import Enum

class QOS(Enum):
    """
    Quality of Service levels for message delivery in a messaging system protocol.

    The `QOS` class defines the levels of Quality of Service (QoS) that dictate how
    the message delivery process between clients and servers is handled, including
    reliability and intended guarantees. It is represented as an enumeration.

    :cvar AT_MOST_ONCE: Messages are delivered at most once and might be lost.
                        This is the lowest level of Quality of Service with no
                        guarantee of message delivery.
    :vartype AT_MOST_ONCE: int
    :cvar AT_LEAST_ONCE: Messages are delivered at least once, but duplicates
                         may occur. This level of Quality of Service ensures
                         message delivery but may introduce redundancy.
    :vartype AT_LEAST_ONCE: int
    :cvar EXACTLY_ONCE: Messages are delivered exactly once, ensuring reliability
                        and avoiding duplicates. This is the highest level of
                        Quality of Service with the strongest delivery guarantee.
    :vartype EXACTLY_ONCE: int
    """
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2
