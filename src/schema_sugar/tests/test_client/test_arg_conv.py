# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
import pytest


@pytest.fixture
def conv2bool():
    from schema_sugar.client.arg_conv import conv2bool
    return conv2bool


def test01_conv2bool_should_return_false_as_default(conv2bool):
    assert conv2bool("unknown") == False


def test02_conv2bool_should_handle_true(conv2bool):
    assert conv2bool("true") == True
    assert conv2bool("True") == True