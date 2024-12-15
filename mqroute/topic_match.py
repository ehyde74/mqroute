from dataclasses import dataclass
from typing import Optional


@dataclass
class TopicMatch(object):
    """
    Represents the result of matching a topic within a particular context.

    This class encapsulates the details resulting from matching a specific
    topic, along with its associated node and any related parameters. It is
    useful in scenarios requiring the identification or validation of topics
    based on input criteria.

    :ivar node: The node associated with the matched topic.
    :type node: TopicNode
    :ivar parameters: A dictionary containing parameters relevant to the
        matched topic.
    :type parameters: dict[str, str]
    :ivar topic: The specific topic matched, if available.
    :type topic: Optional[str]
    """
    node: "TopicNode"
    parameters: dict[str, str]
    topic: Optional[str] = None
