# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

import json
import pytest
import fake_filesystem as fake_fs
from schema_sugar.client.constant import (
    DEFAULT_CFG_FILE)
from mock import patch


@pytest.fixture
def client_config():
    from schema_sugar.client.client import ClientConfig
    return ClientConfig()


@pytest.fixture
def fake_open():
    from schema_sugar.client.constant import DEFAULT_CFG_FILE
    mock_config = json.dumps(
        {
            "username": "root",
            "password": "111111",
            "server": "192.168.1.1",
            "port": 1080,
        }
    )
    fs = fake_fs.FakeFilesystem()
    fs.CreateFile(
        DEFAULT_CFG_FILE,
        contents=mock_config
    )
    return fake_fs.FakeFileOpen(fs)


def test00_config_should_gen_right_url(client_config):
    assert client_config.gen_url("/meta") == "http://localhost:10402/meta"
    assert client_config.gen_url("meta") == "http://localhost:10402/meta"
    assert client_config.gen_url("/meta/hello") == "http://localhost:10402/meta/hello"


def test01_config_file_load_correct_properties(fake_open):
    from schema_sugar.client.client import ClientConfig
    with patch("__builtin__.open", fake_open):
        cfg = ClientConfig(DEFAULT_CFG_FILE)
        assert cfg.base_url == "http://192.168.1.1:1080/"
        assert cfg.username == "root"
        assert cfg.password == "111111"