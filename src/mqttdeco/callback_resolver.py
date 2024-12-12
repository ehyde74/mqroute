import copy

from .callback_request import CallbackRequest
from .mqtt_message import MQTTMessage

from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass, field
from functools import lru_cache


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


class MatchState(Enum):
    """
    Represents the state of a matching operation in a hierarchical system.

    This enumeration defines various possible states during a matching process
    in scenarios such as topic hierarchies and data structures. Commonly used in
    applications that involve partial or complete matches within a layered or
    node-based system.

    """
    NoMatch = auto()
    RootNode = auto()
    PartialTopic = auto()
    FullTopic = auto()


@dataclass
class TopicNode(object):
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
    nodes: dict[str, "TopicNode"] = field(default_factory=dict)


    def register(self,
                 parts: list[str],
                 callback_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]):
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
        :return: None
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
        else:
            node.register(parts[1:], callback_method)


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
        match: MatchState = MatchState.NoMatch

        if self.part == "#":
            match = MatchState.FullTopic
        elif self.part == "+":
            if self.parameter:
                parameters[self.parameter] = parts[0]
            if len(parts) == 1 and not self.nodes:
                match = MatchState.FullTopic
            elif len(parts) == 1 and self.nodes:
                match = MatchState.NoMatch
            else:
                match = MatchState.PartialTopic
        elif self.part == parts[0]:
            if len(parts) == 1 and not self.nodes:
                match = MatchState.FullTopic
            elif len(parts) == 1 and self.nodes:
                match = MatchState.NoMatch
            else:
                match = MatchState.PartialTopic

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
            match = MatchState.RootNode
        else:
            match, node_parameters = self.__check_topic(topic_parts)

            local_parameters.update(node_parameters)

        if match == MatchState.FullTopic:
            topic_match = TopicMatch(node=self,
                                    parameters=local_parameters)
            return [topic_match]
        elif match == MatchState.PartialTopic:
            match_nodes = []
            for node in self.nodes.values():
                local_nodes = node.get_matching_nodes(topic_parts[1:], local_parameters)
                match_nodes.extend(local_nodes)
            return match_nodes
        elif match == MatchState.RootNode:
            match_nodes = []
            for node in self.nodes.values():
                local_nodes = node.get_matching_nodes(topic_parts, local_parameters)
                match_nodes.extend(local_nodes)

            return match_nodes

        return []



class CallbackResolver(object):
    """
    Manages the registration and resolution of callbacks bound to topics. It acts as a route
    handler for topics, allowing dynamic registration of callback functions which are invoked
    based on topic matches. This is particularly useful in systems handling message-based
    communication, such as MQTT.

    Attributes and methods within this class ensure that topics comply with certain patterns
    and assist in retrieving appropriate callbacks for a given topic.

    :ivar __nodes: Root node of the topic tree structure, used to store and resolve callbacks.
    :type __nodes: TopicNode
    """
    def __init__(self):
        self.__nodes = TopicNode(part=None)

    def register(self, topic: str, callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]):
        """
        Registers a callback function for a specific MQTT topic. This function processes
        a topic string by splitting it into parts, registering the callback function with
        the nodes, and constructing the real topic string for subscription. Standard MQTT
        wildcards are supported:
           - "#" matches any topics under the current level, including multilevel matches.
           - "+" matches exactly one level.
           - If there is a need to capture the value of single level wildcard matched
             by + a parameter can be created. This is achieved by using - instead of
             single + as MQTT standard - syntax like +<parameter_name>+
             The CallbackResolver will then create a parameter <parameter_name> that is
             assigned with value found in the matched topic.

        :param topic: The MQTT topic string to register the callback with. Contains
            segments delimited by '/' where wildcards '+' or '#' might be used.
        :type topic: str

        :param callback: The function to be invoked when a message matching the given
            topic is received. It must accept three parameters: the string representation
            of the topic, the MQTTMessage object, and an optional dictionary of string
            parameters.
        :type callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]

        :return: The normalized topic string with proper wildcard adjustments, ready
            for MQTT subscription.
        :rtype: str
        """
        topic_parts = topic.split("/")
        self.__nodes.register(topic_parts, callback)

        real_topic = []
        for part in topic_parts:
            if part.startswith("+"):
                part = "+"
            elif part.startswith("#"):
                part = "#"
            real_topic.append(part)
        return "/".join(real_topic)

    @property
    def nodes(self) -> TopicNode:
        """
        Gets the `nodes` property for the associated TopicNode instance.

        The `nodes` property allows retrieval of the internal TopicNode
        structure used within this context. This enables interaction with
        the associated TopicNode in a controlled and standardized manner.

        :rtype: TopicNode
        :return: The TopicNode instance associated with this object.
        """
        return self.__nodes

    @lru_cache(maxsize=128)
    def get_matching_nodes(self, topic: str) -> list[TopicMatch]:
        """
        Fetches and returns a list of matching nodes for the provided topic. This method interacts with
        the internal nodes structure to find matches based on the topic split by `/`. The retrieved matching
        nodes will have their `topic` attribute updated with the provided topic string.

        The method is using caching in order to reduce the lookup time needed to
        traverse over the nodes. This is based on fact that single topic should
        always bring same nodes as an result of lookup.

        :param topic: Topic string used to search for matching nodes.
        :type topic: str
        :return: A list of TopicMatch objects that correspond to the nodes matching the given topic.
        :rtype: list[TopicMatch]
        """
        match_list = self.__nodes.get_matching_nodes(topic.split("/"))
        for match in match_list:
            match.topic = topic
        return match_list



    def callbacks(self, topic) -> list[CallbackRequest]:
        """
        Processes the given topic to determine matching nodes and creates a list of
        callback requests. This function resolves topic matches using the internal
        method ``get_matching_nodes`` and maps each match to a corresponding callback
        request.

        :param topic: The topic to process for matching and generating callback
            requests.
        :type topic: str
        :return: A list of ``CallbackRequest`` objects, where each represents a
            callback request for a matching topic and its parameters.
        :rtype: list[CallbackRequest]
        """
        topic_matches = self.get_matching_nodes(topic)

        return [CallbackRequest(topic=match.topic,
                                cb_method=match.node.callback,
                                parameters=match.parameters)
                for match in topic_matches]


if __name__ == "__main__":
    import pprint

    def cb_method(_: str, __: MQTTMessage, ___: dict[str, str]):
        pass

    resolver = CallbackResolver()
    resolver.register("car/dog/cat", cb_method)
    resolver.register("car/+/cat", cb_method)
    resolver.register("car/+/+", cb_method)
    resolver.register("car/#", cb_method)

    resolver.register("bus/train/ship", cb_method)
    resolver.register("bus/+vehicle+/ship", cb_method)
    resolver.register("bus/+vehicle+/#", cb_method)
    resolver.register("bus/+vehicle+/+boat+", cb_method)

    pprint.pprint(resolver.nodes, indent=2)

    nodes = resolver.get_matching_nodes("car/dog/cat")
    pprint.pprint(nodes)

    nodes = resolver.get_matching_nodes("bus/train/ship")
    pprint.pprint(nodes)

    nodes = resolver.get_matching_nodes("bus/bike/ferry")
    pprint.pprint(nodes)

    nodes = resolver.get_matching_nodes("church/bike/ferry")
    pprint.pprint(nodes)

    nodes = resolver.get_matching_nodes("car/dog/cat/zeppelin")
    pprint.pprint(nodes)

    nodes = resolver.get_matching_nodes("car")
    pprint.pprint(nodes)
