# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
from contextlib import nested
from mock import (
    patch,
    Mock,
)
import pytest


@pytest.fixture
def mocked_requests():
    r = Mock()
    r.get.return_value = "hello_world"
    return r


@pytest.fixture
def mocked_parse():
    return Mock()


def test00_should_fetch_meta(mocked_parse):
    import requests
    from schema_sugar.client import RestClient

    with patch("requests.get") as get:
        return_meta = {
            "/api/v2 datastores": {},
        }
        response = get.return_value = Mock()
        response.json.return_value = return_meta
        client = RestClient(mocked_parse)
        assert client.meta == return_meta


def test10_should_use_correct_method(mocked_parse):
    from schema_sugar.client import RestClient

    status = {"method": None}

    def mocked_get(*arg, **kwargs):
        status["method"] = "get"

    def mocked_post(*arg, **kwargs):
        status["method"] = "post"

    with nested(
        patch("requests.get", mocked_get),
        patch("requests.post", mocked_post),
        patch.object(RestClient, "_fetch_meta", Mock())
    ):
        client = RestClient(mocked_parse)
        client.send_request(
            "/api/v2", "GET", params=None,
        )
        assert status["method"] == "get"
        client.send_request(
            "/api/v2", "PosT"
        )
        assert status["method"] == "post"