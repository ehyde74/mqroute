from enum import Enum

from mqroute.payload_formats import PayloadFormat
from .topic_node import TopicNode
from mqroute.topic_match import TopicMatch
from .callback_request import CallbackRequest
from .mqtt_message import MQTTMessage

from typing import Optional, Callable
from functools import lru_cache


class CallbackResolver(object):
    """
    Manages the registration and resolution of callbacks bound to topics. It acts as a route
    handler for topics, allowing dynamic registration of callback functions which are invoked
    based on topic matches. This is particularly useful in systems handling message-based
    communication, such as MQTT.

    Attributes and methods within this class ensure that topics comply with certain patterns
    and assist in retrieving appropriate callbacks for a given topic.

    :ivar __nodes: Root node of the topic tree structure, used to store and resolve callbacks.
    :type __nodes: mqroute.topic_node.TopicNode
    """
    def __init__(self):
        self.__nodes = TopicNode(part=None)

    def register(self,
                 topic: str,
                 callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None],
                 payload_format: Enum,
                 fallback: bool = False):
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
        :ivar payload_format: Expected payload format for payload (default is JSON).
            The type is any Enum type in order to allow customization of supported payload formats.
        :type payload_format: Enum
        :ivar fallback: If True, the callback will be matched only if no other matches are found
        :type fallback: bool

        :return: The normalized topic string with proper wildcard adjustments, ready
            for MQTT subscription.
        :rtype: str
        """
        topic_parts = topic.split("/")
        self.__nodes.register(topic_parts, callback, payload_format, fallback)

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
        always bring same nodes as a result of lookup.

        :param topic: Topic string used to search for matching nodes.
        :type topic: str
        :return: A list of TopicMatch objects that correspond to the nodes matching the given topic.
        :rtype: list[TopicMatch]
        """
        match_list = self.__nodes.get_matching_nodes(topic.split("/"))
        fallbacks = []
        normal_callbacks = []
        for match in match_list:
            match.topic = topic
            if match.node.fallback:
                fallbacks.append(match)
            else:
                normal_callbacks.append(match)

        if normal_callbacks:
            return normal_callbacks
        else:
            return fallbacks



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
                                payload_format=match.node.payload_format,
                                parameters=match.parameters)
                for match in topic_matches]


if __name__ == "__main__":
    import pprint

    def cb_method(_: str, __: MQTTMessage, ___: dict[str, str]):
        pass

    resolver = CallbackResolver()
    resolver.register("car/dog/cat", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("car/+/cat", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("car/+/+", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("car/#", cb_method, payload_format=PayloadFormat.JSON)

    resolver.register("bus/train/ship", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("bus/+vehicle+/ship", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("bus/+vehicle+/#", cb_method, payload_format=PayloadFormat.JSON)
    resolver.register("bus/+vehicle+/+boat+", cb_method, payload_format=PayloadFormat.JSON)

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
