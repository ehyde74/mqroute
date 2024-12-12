import copy

from .callback_request import CallbackRequest
from .mqtt_message import MQTTMessage

from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class TopicMatch(object):
    node: "TopicNode"
    parameters: dict[str, str]
    topic: Optional[str] = None


class MatchState(Enum):
    NoMatch = auto()
    RootNode = auto()
    PartialTopic = auto()
    FullTopic = auto()


@dataclass
class TopicNode(object):
    # None for the root node, others possibly with empty string
    part: Optional[str]
    parameter: Optional[str] = None
    callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None] = None
    nodes: dict[str, "TopicNode"] = field(default_factory=dict)


    def register(self,
                 parts: list[str],
                 callback_method: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]):
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
    def __init__(self):
        self.__nodes = TopicNode(part=None)

    def register(self, topic: str, callback: Callable[[str, MQTTMessage, Optional[dict[str, str]]], None]):
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
        return self.__nodes

    def get_matching_nodes(self, topic: str) -> list[TopicMatch]:
        match_list = self.__nodes.get_matching_nodes(topic.split("/"))
        for match in match_list:
            match.topic = topic
        return match_list



    def callbacks(self, topic) -> list[CallbackRequest]:
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
