# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
from schema_sugar.client.support.flask import parse_rule


def test00_should_parse_rule_return_right_pattern():

    assert list(parse_rule("/api/v2")) == [
        (None, None, "/api/v2"),
    ]
    assert list(parse_rule("/api/<id>")) == [
        (None, None, "/api/"),
        ("default", None, "id"),
    ]
    assert list(parse_rule("/api/<id>/create")) == [
        (None, None, "/api/"),
        ("default", None, "id"),
        (None, None, "/create"),
    ]
    assert list(parse_rule("/api/<int:id>/create")) == [
        (None, None, "/api/"),
        ("int", None, "id"),
        (None, None, "/create"),
    ]


def test01_should_parse_rule_return_no_pattern():
    assert list(parse_rule("")) == []

