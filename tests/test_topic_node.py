# test_topic_node.py

import pytest

from mqroute.topic_node import TopicNode

def test_register_creates_hierarchy():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "livingroom", "temperature"], test_callback)

    assert "home" in root.nodes
    assert "livingroom" in root.nodes["home"].nodes
    assert "temperature" in root.nodes["home"].nodes["livingroom"].nodes
    node = root.nodes["home"].nodes["livingroom"].nodes["temperature"]
    assert node.callback is test_callback


def test_register_with_plus_wildcard():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "+sensor+", "temperature"], test_callback)

    assert "+" in root.nodes["home"].nodes
    node = root.nodes["home"].nodes["+"].nodes["temperature"]
    assert node.callback is test_callback
    assert root.nodes["home"].nodes["+"].parameter == "sensor"


def test_register_with_hash_wildcard():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "#"], test_callback)

    assert "#" in root.nodes["home"].nodes
    node = root.nodes["home"].nodes["#"]
    assert node.callback is test_callback


def test_get_matching_nodes_full_topic():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "livingroom", "temperature"], test_callback)

    matches = root.get_matching_nodes(["home", "livingroom", "temperature"])
    assert len(matches) == 1
    assert matches[0].node.callback is test_callback


def test_get_matching_nodes_plus_wildcard():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "+sensor+", "temperature"], test_callback)

    matches = root.get_matching_nodes(["home", "livingroom", "temperature"])
    assert len(matches) == 1
    assert matches[0].node.callback is test_callback
    assert matches[0].parameters["sensor"] == "livingroom"


def test_get_matching_nodes_hash_wildcard():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "#"], test_callback)

    matches = root.get_matching_nodes(["home", "livingroom", "temperature"])
    assert len(matches) == 1
    assert matches[0].node.callback is test_callback


def test_no_matches_found():
    def test_callback(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "bedroom", "temperature"], test_callback)

    matches = root.get_matching_nodes(["home", "livingroom", "temperature"])
    assert len(matches) == 0

def test_multiple_matches():
    def test_callback1(topic, message, params):
        pass
    def test_callback2(topic, message, params):
        pass
    def test_callback3(topic, message, params):
        pass

    root = TopicNode(part=None)
    root.register(["home", "bedroom", "temperature"], test_callback1)
    root.register(["home", "+room+", "temperature"], test_callback2)
    root.register(["house", "+", "temperature"], test_callback3)

    matches = root.get_matching_nodes(["home", "bedroom", "temperature"])
    assert len(matches) == 2
