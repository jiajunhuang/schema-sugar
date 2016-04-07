# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
from copy import deepcopy
from argparse import Namespace

import mock
import pytest


@pytest.fixture
def cmd_node():
    return {
        "name": "new_cmd",
        "cmd": "cmd_obj",
        "children": {}
    }


@pytest.fixture
def cmd_node2():
    return {
        "name": "child_cmd",
        "cmd": "cmd_obj",
        "children": {}
    }


@pytest.fixture
def required_fields():
    return [
        "name",
        "replica_num",
        "thin_provision"
    ]


@pytest.fixture
def create_schema(required_fields):
    return {
        "help": "create new datastore",
        "properties": {
            "description": {
                "type": "string"
            },
            "name": {
                "type": "string"
            },
            "replica_num": {
                "enum": [
                    1,
                    2,
                    3
                ],
                "type": "number"
            },
            "thin_provision": {
                "type": "boolean"
            }
        },
        "required": required_fields,
        "type": "object"
    }


@pytest.fixture
def one_schema(create_schema):
    return {
        "instance": {
            "extra_actions": {},
            "out_fields": {},
            "resources": "datastores",
            "schema": {
                "create": create_schema,
                "index": {
                    "help": "list all datastore",
                    "properties": {},
                    "type": "object"
                },
                "show": {
                    "help": "show a datastore",
                    "properties": {},
                    "type": "object"
                },
                "support_operations": [
                    "create",
                    "delete",
                    "index",
                    "show",
                    "update"
                ],
                "update": {
                    "help": "update a datastore",
                    "properties": {
                        "description": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "replica_num": {
                            "enum": [
                                1,
                                2,
                                3
                            ],
                            "type": "number"
                        },
                        "thin_provision": {
                            "type": "boolean"
                        }
                    },
                    "required": [
                        "name",
                        "replica_num",
                        "thin_provision"
                    ],
                    "type": "object"
                }
            }
        },
        "url_prefix": "/api/v2"
    }


@pytest.fixture
def sample_schemas(one_schema):
    return {
        "/api/v2  datastores": one_schema
    }


@pytest.fixture
def client(sample_schemas):
    client = mock.Mock()
    client.meta = sample_schemas
    client.parse_url.return_value = [
        ("default", None, "mock_arg"),
        (None, None, "not_arg"),
    ]
    return client


@pytest.fixture
def mocked_resource():
    return mock.Mock()


@pytest.fixture
def cmd_tree(mocked_resource):
    from schema_sugar.client.parser import CmdTree
    return CmdTree(mocked_resource)


@pytest.fixture
def cmd_tree_with_tree(cmd_tree, cmd_node, cmd_node2):
    cmd_tree._add_node(
        cmd_node, ['new_cmd']
    )
    cmd_tree._add_node(
        cmd_node2, ['new_cmd', 'child_cmd']
    )
    return cmd_tree


def test01_should_func_called():
    from schema_sugar.client.parser import Resource
    status = {"is_run": False}

    def func(**kwargs):
        status["is_run"] = True

    with mock.patch(
        "sys.argv",
        ["script", "disks"]
    ):
        cmd = Resource()
        cmd.add_cmd("disks", func=func)
        cmd.run()

    assert status['is_run']


def test02_should_sub_cmd_object_is_resource():
    from schema_sugar.client.parser import Resource

    with mock.patch.object(
        Resource,
        "parse_args",
        return_value=Namespace(disks="", list=""),
    ):
        cmd = Resource()
        sub = cmd.add_cmd("disks")
        assert isinstance(sub, Resource)


def test10_should_mk_cmd_meta_return_right_meta(one_schema):
    from schema_sugar.client.parser import _mk_cmd_meta
    from schema_sugar import SugarConfig
    meta = _mk_cmd_meta(
        SugarConfig(one_schema['instance']),
        "/api/v2",
        "/api/v2",
    )
    assert meta["cmd_path"] == ["datastores"]
    assert not meta["is_singular"]
    assert meta["operations"] == [
        'create', 'delete', 'index', 'show', 'update'
    ]


def test11_should_mk_cmd_meta_return_right_prefix(one_schema):
    from schema_sugar.client.parser import _mk_cmd_meta
    from schema_sugar import SugarConfig
    meta = _mk_cmd_meta(
        SugarConfig(one_schema['instance']),
        "/api/v2",
        "/api/v2/test_prefix",
    )
    assert meta["cmd_path"] == ["test_prefix", "datastores"]
    assert not meta["is_singular"]
    assert meta["operations"] == [
        'create', 'delete', 'index', 'show', 'update'
    ]


def test20_should_cmd_add_return_new_resource_instance():
    from schema_sugar.client.parser import Resource
    from schema_sugar.client.parser import _add_sub_cmd
    root_resource = Resource()
    new_resource = _add_sub_cmd(
        root_resource,
        "new",
        "help",
        lambda x:x
    )
    assert isinstance(new_resource, Resource)
    assert new_resource is not root_resource


def test30_should_run_cmds_raise_no_exception(client):
    from schema_sugar.client.parser import run_cmds
    with mock.patch("sys.argv", ['hello', 'datastores', 'list', "mock_arg"]):
        run_cmds(client)


def test40_should_mk_url_returns_right_url():
    from schema_sugar.client.parser import _mk_url as mk_url
    assert mk_url("res", "/api/v2", True, "index") == "/api/v2/res"
    assert mk_url("res", "/api/v2", False, "index") == "/api/v2/res"
    assert mk_url("res", "/api/v2", False, "create") == "/api/v2/res"
    assert mk_url("res", "/api/v2", False, "update") == "/api/v2/res/<id>"
    assert mk_url("res", "/api/v2", False, "show") == "/api/v2/res/<id>"
    assert mk_url("res", "/api/v2", False, "delete") == "/api/v2/res/<id>"


def test50_should_mk_positional_params_return_right_arg(client):
    from schema_sugar.client.parser import _mk_positional_params as mk
    assert mk(client.parse_url, "/api/v2/<mock_arg>") == [{"name": "mock_arg"}]


def test51_should_mk_positional_params_return_no_arg():
    from schema_sugar.client.parser import _mk_positional_params as mk
    parse_url = mock.Mock()
    parse_url.return_value = [(None, None, "not_arg")]
    assert mk(parse_url, "/api/v2/<mock_arg>") == []


def test60_should_mk_required_params_return_required(create_schema):
    from schema_sugar.client.parser import _mk_required_params as mk
    assert mk(create_schema) == [
        {'help': "{'type': 'string'}", 'name': 'name'},
        {'help': "{'enum': [1, 2, 3], 'type': 'number'}", 'name': 'replica_num'},
        {"help": "{'type': 'boolean'}", 'name': 'thin_provision'},
    ]


def test61_should_mk_required_params_return_null(create_schema):
    from schema_sugar.client.parser import _mk_required_params as mk
    create_schema["required"] = []
    assert mk(create_schema) == []


def test71_should_mk_optional_params_return_arg_list(create_schema):
    from schema_sugar.client.parser import _mk_optional_params as mk
    assert mk(create_schema) == [{"help": "{'type': 'string'}", 'name': '--description'}]


def test80_should_cmd_tree_gen_right_node(cmd_tree):
    ret = cmd_tree._gen_cmd_node("cmd", "cmd_obj")
    assert ret == {
        "name": "cmd",
        "cmd": "cmd_obj",
        "children": {}
    }


def test81_should_cmd_tree_add_node_create_right_index(
    cmd_tree, mocked_resource, cmd_node, cmd_node2
):
    cmd_tree._add_node(cmd_node, ['new_cmd'])
    assert cmd_tree.cmd_tree == {
        "name": "root",
        "cmd": mocked_resource,
        "children": {"new_cmd": cmd_node}
    }

    cmd_tree._add_node(cmd_node2, ['new_cmd', 'child_cmd'])
    expected_cmd_node = deepcopy(cmd_node)
    expected_cmd_node['children']['child_cmd'] = cmd_node2
    assert cmd_tree.cmd_tree == {
        "name": "root",
        "cmd": mocked_resource,
        "children": {"new_cmd": expected_cmd_node}
    }


def test82_should_cmd_tree_get_cmd_by_path_get_parent(
    cmd_tree_with_tree, cmd_node, cmd_node2
):
    tree = cmd_tree_with_tree
    ret = tree.get_cmd_by_path(['new_cmd'])
    expected_cmd_node = deepcopy(cmd_node)
    expected_cmd_node['children']['child_cmd'] = cmd_node2
    assert ret == expected_cmd_node


def test83_should_cmd_tree_get_cmd_by_path_get_child(
    cmd_tree_with_tree, cmd_node2
):
    tree = cmd_tree_with_tree
    ret = tree.get_cmd_by_path(['new_cmd', 'child_cmd'])
    assert ret == cmd_node2


def test84_should_cmd_tree_get_paths_works(
    cmd_tree
):
    ret = cmd_tree._get_paths([1, 2, 3], 2)
    assert ret == ([3, ], [1, 2])


def test85_should_cmd_tree_index_in_tree_get_right_index(
    cmd_tree_with_tree
):
    tree = cmd_tree_with_tree
    ret = tree.index_in_tree(['new_cmd', 'child_cmd'])
    assert ret is None
    assert tree.index_in_tree(['new_cmd']) is None
    ret = tree.index_in_tree(['new_cmd', 'hello'])
    assert ret == 1
    assert tree.index_in_tree(['child_cmd']) == 0
    assert tree.index_in_tree(['another_cmd_not_exist']) == 0


def test86_should_cmd_tree_add_parent_commands_return_the_last(
    cmd_tree
):
    cmd_tree.add_parent_commands(['new_cmd', 'hello'])
    assert "hello" in \
           cmd_tree.cmd_tree['children']['new_cmd']['children']
    assert {} == \
           cmd_tree.cmd_tree['children']['new_cmd']['children']["hello"]['children']


def test87_should_cmd_tree_get_cmd_by_path_got_obj(
    cmd_tree_with_tree
):
    assert cmd_tree_with_tree.get_cmd_by_path(['new_cmd']) is not None
    assert cmd_tree_with_tree.get_cmd_by_path(['new_cmd', "child_cmd"]) is not None
    with pytest.raises(ValueError) as excinfo:
        cmd_tree_with_tree.get_cmd_by_path(['new_cmd', "fuck"])
    msg = "Given key [fuck] in path ['new_cmd', 'fuck'] does not exist in tree."
    assert excinfo.value.message == msg


def test90_should_parse_url_by_args_works():
    from schema_sugar.client.parser import _parse_url_by_args as parse
    arg = {"hello": "world"}
    assert parse("/datastores", arg) == ([], '/datastores')
    assert parse("/ds/<hello>", arg) == (['hello'], '/ds/world')
    assert parse("/ds", arg) == ([], '/ds')


def test100_should_get_args_converter_works():
    import json

    from schema_sugar.client.parser import _get_arg_converter as gac
    from schema_sugar.client.arg_conv import conv2bool

    def mk_desc(type):
        return {
            "type": type,
        }

    assert gac(mk_desc("string")) is unicode
    assert gac(mk_desc("integer")) is int
    assert gac(mk_desc("number")) is float
    assert gac(mk_desc("boolean")) is conv2bool
    assert gac(mk_desc("object")) is json.loads


def test101_should_get_args_converter_works_with_enum():
    from schema_sugar.client.parser import _get_arg_converter as gac
    assert gac({"type": "string", "enum": [1]}) is unicode
    assert gac({"type": "integer", "enum": [1]}) is int
    assert gac({"enum": [1]}) is int
    assert gac({"enum": ["he"]}) is str
    assert gac({"enum": [u"he"]}) is unicode


def test110_should_mk_request_json_body_works():
    from schema_sugar.client.parser import _mk_request_json_body as mk_json
    data = {"t": "2", "json": '{"hello": "object"}'}
    schema = {
        "properties": {
            "t": {
                "type": "integer"
            },
            "json": {"type": "object"}
        }
    }
    assert mk_json(data, schema) == {"t": 2, "json": {"hello": "object"}}