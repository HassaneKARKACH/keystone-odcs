from keystone_core import hello


def test_hello():
    assert hello() == "Hello from keystone!"
