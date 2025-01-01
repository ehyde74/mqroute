"""
This module provides functionality for handling nodes related to topics
in MQTT-based communication. It includes structures and utilities
to define, publish, and subscribe to topics as well as to process
related messages efficiently.

Classes:
    MQTTMessage: Encapsulates information about a published or
    subscribed MQTT message, including its topic and message content.

The module aims to offer a flexible interface for dealing with MQTT topics
and associated messages, supporting multiple payload representations such
as dictionaries or plain text.
"""

import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable

from .mqtt_message import MQTTMessage
from .topic_match import TopicMatch


class MatchState(Enum):
    """
    Represents the state of a matching operation in a hierarchical system.

    This enumeration defines various possible states during a matching process
    in scenarios such as topic hierarchies and data structures. Commonly used in
    applications that involve partial or complete matches within a layered or
    node-based system.

    """
    NO_MATCH = auto()
    ROOT_NODE = auto()
    PARTIAL_TOPIC = auto()
    FULL_TOPIC = auto()


@dataclass
class TopicNode:
    """
    Represents a node in a hierarchical topic structure for MQTT.

    This class is designed to handle MQTT topic structures and match topics to
    specific callback methods. It supports hierarchical topic registration,
    wildcards for topics (+ for single levels and # for multi-level hierarchy),
    and maintains a tree-like structure for efficient matching of topic
    subscriptions to their corresponding handlers.

    :ivar part: The specific part of the topic this node represents. Can be a
        literal part of the topic, '+' for single-level wildcard, '#' for
        multi-level wildcard, or None for the root node.
    :type part: Optional[str]
    :ivar parameter: The parameter name associated with the wildcard ('+' or '#')
        part, if applicable. None if this is not a wildcard node.
    :type parameter: Optional[str]
    :ivar callback: A callable object (e.g., a function) associated with this
        topic node. Executed when this topic node fully matches a given topic.
    :type callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]
    :ivar nodes: A dictionary of child nodes, where keys are topic parts ('+',
        '#', or literal parts) and values are instances of TopicNode.
    :type nodes: dict[str, TopicNode]
    """
    # None for the root node, others possibly with empty string
    part: Optional[str]
    parameter: Optional[str] = None
    callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None] = None
    payload_format: Optional[Enum] = None
    fallback: Optional[bool] = None
    nodes: dict[str, "TopicNode"] = field(default_factory=dict)


    def register(self,
                 parts: list[str],
                 callback_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None],
                 payload_format: Enum,
                 fallback: bool = False):
        """
        Registers a callback method for a specific topic structure within a tree-like topic
        hierarchy. The method can handle both generic topics represented by "+", special topics
        represented by "#", or concrete parts of a topic string. Nodes are created or reused
        recursively to build the topic structure dynamically.

        :param parts: A list of strings representing each part of the topic path. Each element
            can represent a specific topic level, with "+" indicating a parameterized path,
            and "#" representing a wildcard for all lower-level topics.
        :type parts: list[str]
        :param callback_method: A callable method that gets triggered when a matching topic
            structure is encountered. This callable accepts the topic as a string, a message
            object of type MQTTMessage, and an optional dictionary of parameters (if present)
            extracted from the topic.
        :type callback_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]
        ivar payload_format: Expected payload format for payload (default is JSON).
            The type is any Enum type in order to allow customization of supported payload formats.
        :type payload_format: Enum
        :ivar fallback: If True, the callback will be matched only if no other matches are found
        :type payload_format: bool:return: None
        :rtype: None
        """
        part = parts[0]
        parameter = None

        if part.startswith("+"):
            part = "+"
            # parameter name
            parameter = parts[0][1:-1]
        elif part.startswith("#"):
            part = "#"

        try:
            node = self.nodes[part]
        except KeyError:
            node = TopicNode(part=part, parameter=parameter)
            self.nodes[part] = node

        if len(parts) == 1:
            node.callback = callback_method
            node.payload_format = payload_format
            node.fallback = fallback
        else:
            node.register(parts[1:], callback_method, payload_format, fallback)


    def __check_topic(self, parts: list[str]):
        """
        Evaluates the matching state for a given topic and extracts parameters if
        applicable. Depending on the nature of the current topic part and the
        provided parts list, this method determines the matching state of the
        topic (`FullTopic`, `PartialTopic`, or `NoMatch`) and updates the parameters
        dictionary accordingly.

        :param parts: The list of string segments representing parts of the topic.
        :type parts: list[str]
        :return: A tuple where the first item is the matching state of the topic,
         and the second is a dictionary of parameters extracted from the topic.
        :rtype: tuple[MatchState, dict[str, str]]
        """
        parameters = {}
        match: MatchState = MatchState.NO_MATCH

        if self.part == "#":
            match = MatchState.FULL_TOPIC
        elif self.part == "+":
            if self.parameter:
                parameters[self.parameter] = parts[0]
            if len(parts) == 1 and not self.nodes:
                match = MatchState.FULL_TOPIC
            elif len(parts) == 1 and self.nodes:
                match = MatchState.NO_MATCH
            else:
                match = MatchState.PARTIAL_TOPIC
        elif self.part == parts[0]:
            if len(parts) == 1 and not self.nodes:
                match = MatchState.FULL_TOPIC
            elif len(parts) == 1 and self.nodes:
                match = MatchState.NO_MATCH
            else:
                match = MatchState.PARTIAL_TOPIC

        return match, parameters

    def get_matching_nodes(self,
                           topic_parts: list[str],
                           parameters: Optional[dict[str, str]] = None) -> list[TopicMatch]:
        """
        Finds and returns a list of nodes that match the given topic parts.

        This method traverses the structure of nodes recursively, comparing the given
        `topic_parts` with the current node. Depending on the match status, it either
        appends a full topic match to the result or continues traversal for partial
        or root matches. If `parameters` are provided, they are merged and utilized
        in the matching process.

        :param topic_parts: A list of strings representing parts of a topic to
            match against.
        :param parameters: A dictionary containing parameter key-value pairs
            used during the matching process. Defaults to None.
        :return: A list of `TopicMatch` objects representing the matching nodes
            and their associated parameter mappings.
        """
        #for node in self.nodes.values():
        if parameters is None:
            local_parameters = {}
        else:
            local_parameters = copy.deepcopy(parameters)

        if self.part is None:
            match = MatchState.ROOT_NODE
        else:
            match, node_parameters = self.__check_topic(topic_parts)

            local_parameters.update(node_parameters)

        match_nodes = []
        if match == MatchState.FULL_TOPIC:
            topic_match = TopicMatch(node=self,
                                     parameters=local_parameters)
            match_nodes.append(topic_match)
        elif match == MatchState.PARTIAL_TOPIC:
            match_nodes = []
            for node in self.nodes.values():
                local_nodes = node.get_matching_nodes(topic_parts[1:], local_parameters)
                match_nodes.extend(local_nodes)
        elif match == MatchState.ROOT_NODE:
            match_nodes = []
            for node in self.nodes.values():
                local_nodes = node.get_matching_nodes(topic_parts, local_parameters)
                match_nodes.extend(local_nodes)

        return match_nodes
