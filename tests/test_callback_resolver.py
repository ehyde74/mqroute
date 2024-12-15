from mqroute import CallbackRequest
from mqroute import CallbackResolver
from mqroute import TopicMatch


def test_register_valid_topic_and_callback():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    topic = "home/livingroom/temperature"
    real_topic = resolver.register(topic, test_callback)

    assert real_topic == topic
    node = resolver.nodes.nodes["home"].nodes["livingroom"].nodes["temperature"]
    assert node.callback is test_callback


def test_register_with_wildcards():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    topic = "home/+/temperature"
    real_topic = resolver.register(topic, test_callback)

    assert real_topic == "home/+/temperature"
    node = resolver.nodes.nodes["home"].nodes["+"].nodes["temperature"]
    assert node.callback is test_callback


def test_get_matching_nodes():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    resolver.register("home/+/temperature", test_callback)

    matches = resolver.get_matching_nodes("home/livingroom/temperature")

    assert len(matches) == 1
    assert isinstance(matches[0], TopicMatch)
    assert matches[0].node.callback is test_callback
    assert matches[0].topic == "home/livingroom/temperature"


def test_get_matching_nodes_no_match():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    resolver.register("home/kitchen/temperature", test_callback)

    matches = resolver.get_matching_nodes("home/livingroom/temperature")

    assert len(matches) == 0


def test_callbacks_generates_correct_requests():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    resolver.register("home/+/temperature", test_callback)

    requests = resolver.callbacks("home/livingroom/temperature")

    assert len(requests) == 1
    assert isinstance(requests[0], CallbackRequest)
    assert requests[0].cb_method is test_callback
    assert requests[0].topic == "home/livingroom/temperature"
    assert requests[0].parameters == {}


def test_callbacks_no_match_returns_empty_list():
    def test_callback(topic, message, params):
        pass

    resolver = CallbackResolver()
    resolver.register("home/kitchen/temperature", test_callback)

    requests = resolver.callbacks("home/livingroom/temperature")

    assert requests == []
