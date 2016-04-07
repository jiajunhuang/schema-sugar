# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
import json
import logging

from urlparse import urljoin
import re

from argparse import ArgumentParser
try:
    from simplejson import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from schema_sugar.client.arg_conv import conv2bool
from schema_sugar.client.client import RestClient
from schema_sugar import SugarConfig
from schema_sugar.constant import INDEX_OP, CREATE_OP, HTTP_GET
from schema_sugar.utils import op2cli, cli2http


class Resource(ArgumentParser):
    """
    Arg-parse wrapper for sub command and convenient arg parse.
    """
    def __init__(self, *args, **kwargs):
        self.subparsers = None

        super(Resource, self).__init__(*args, **kwargs)

    def add_cmd(self, name, help="", func=None):
        """
        :rtype: Resource
        """
        if self.subparsers is None:
            self.subparsers = self.add_subparsers(help='sub-commands')

        parser = self.subparsers.add_parser(name, help=help)
        if func is not None:
            parser.set_defaults(_func=func)
        return parser

    def run(self):
        args = self.parse_args()
        logging.debug("Got arguments: %s" % args)
        if args._func:
            return args._func(**vars(args))
        else:
            return args


def _mk_cmd_meta(sugar_config, prefix2ignore, prefix):
    """
    Generate command line generation's required info.
    :type sugar_config: schema_sugar.SugarConfig
    :type prefix2ignore: unicode or str
    :param prefix2ignore: If given, the command that we generate
     will remove the prefix, we will get got "command datastores"
     instead of "command api v2 datastores".
    :type prefix: unicode or str
    :param prefix: api-prefix
    :return: a dict like
     ```
        {
            "cmd_path": cmd_path,
            "raw_prefix": prefix,
            "is_singular": detail["is_singular"],
            "operations": ['index', 'create']
        }
     ```
    """
    operations = sugar_config.support_operations
    detail = sugar_config.resource_detail

    handled_prefix = prefix.replace(prefix2ignore, "")
    cmd_path = [part for part in handled_prefix.split("/") if part]
    cmd_path.append(detail["name"])

    return {
        "cmd_path": cmd_path,
        "raw_prefix": prefix,
        "is_singular": detail["is_singular"],
        "operations": operations,
        "name": detail['name'],
        "operation_detail": sugar_config.schema
    }


def _add_sub_cmd(parent, child_name, help, func=None):
    """
    :type parent: schema_sugar.client.parser.Resource
    """
    return parent.add_cmd(child_name, help, func)


def _parse_url_by_args(url_template, arguments):
    """
    :type arguments: dict
    :return:
    """
    # TODO(winkidney): support more url pattern(such as "<int:id>)"
    used_kwargs = re.findall(r"<(.*?)>", url_template)
    new_template = url_template.replace("<", "{").replace(">", "}")
    return used_kwargs, new_template.format(**arguments)


def _get_arg_converter(type_description):
    """
    Get arg type then return the converter factory method.
    :param type_description: dict
    :rtype: callable
    """
    if "type" in type_description:
        type_ = type_description["type"]
        if type_ == "number":
            return float
        elif type_ == "integer":
            return int
        elif type_ == "object":
            return json.loads
        elif type_ == "boolean":
            return conv2bool
        elif type == "string":
            return unicode
    elif "enum" in type_description:
        enum = type_description['enum']
        if enum:
            return type(enum[0])

    # fallback to unicode type
    return unicode


def _convert_arg_type(arg_value, type_description):
    converter = _get_arg_converter(type_description)
    return converter(arg_value)


def _mk_request_json_body(data, schema):
    new_data = {}
    for arg, value in data.iteritems():
        if arg in schema['properties']:
            new_value = _convert_arg_type(
                value,
                schema['properties'][arg]
            )
            new_data[arg] = new_value
        else:
            new_data[arg] = value

    return new_data


def _mk_cmd_func(
    client, method, url, op_schema, headers=None,
):
    """
    Make a cmd func that binds to a command.
    :type client: RestClient
    """
    def request_func(**arguments):
        params, data = {}, {}
        args = dict(
            (key, value)
            for key, value in arguments.iteritems()
            if not key.startswith("_")
        )
        kwargs_to_pop, formated_url = _parse_url_by_args(
            url,
            arguments,
        )
        # pop the url arguments
        # (leave query-string or json data alone)
        for kw in kwargs_to_pop:
            args.pop(kw)

        if method == HTTP_GET:
            params = args
        else:
            data = _mk_request_json_body(args, op_schema)

        return client.send_request(
            formated_url, method, params, data, headers=headers or {}
        )

    request_func._schema_meta = op_schema
    return request_func


def _mk_url(res_name, prefix, is_singular, operation):
    """
    Generate a resource url via its resource name and
    operation name(create, update, etc).
    """
    if prefix[-1] != "/":
        prefix += "/"
    if is_singular:
        return urljoin(prefix, res_name)
    if operation not in (INDEX_OP, CREATE_OP):
        return urljoin(prefix, "%s/<id>" % res_name)
    else:
        return urljoin(prefix, res_name)


def _mk_required_params(single_schema):
    if "required" not in single_schema:
        return []
    return [
        {"name": name, "help": str(single_schema['properties'][name])}
        for name in single_schema["required"]
        ]


def _mk_optional_params(single_schema):
    if "required" not in single_schema.keys():
        required = []
    else:
        required = single_schema['required']
    return [
        {"name": "--" + name, "help": str(single_schema['properties'][name])}
        for name in single_schema["properties"].keys()
        if name not in required
    ]


def _mk_positional_params(parse_url, full_path):
    return [
        {"name": arg[2]}
        for arg in parse_url(full_path)
        if arg[0] is not None
    ]


def _mk_arguments(client, full_path, single_schema=None):
    """
    :type client: RestClient
    """
    positional_args = _mk_positional_params(
        client.parse_url, full_path
    )
    required_arguments = []
    optional_arguments = []
    if single_schema is not None:
        required_arguments = _mk_required_params(single_schema)
        optional_arguments = _mk_optional_params(single_schema)
    return positional_args, required_arguments, optional_arguments


def add_operation_cmd(parent, meta, client):
    """
    Add CRUD sub-commands for a given resource(like `session`).
    :type parent: Resource
    """
    for operation in meta["operations"]:
        cmd_name = op2cli(operation)
        http_method = cli2http(cmd_name)
        url = _mk_url(
           meta["name"], meta['raw_prefix'], meta["is_singular"], operation
        )
        operation_schema = meta['operation_detail'].get(operation)
        if operation_schema is None:
            help_msg = operation
            logging.debug(
                "Schema access failed for operation [%s], meta schema is: %s"
                % (operation, meta['operation_detail'])
            )
        else:
            help_msg = operation_schema.get("help", operation)

        func = _mk_cmd_func(
            client=client,
            method=http_method,
            url=url,
            op_schema=operation_schema,
        )

        child = parent.add_cmd(cmd_name, help_msg, func=func)

        pargs, rargs, oargs = _mk_arguments(
            client,
            url,
            operation_schema,
        )
        for arg in pargs:
            child.add_argument(
                arg["name"], help=arg.get("help", "positional arg")
            )
        for arg in rargs:
            child.add_argument(
                arg["name"], help=arg.get("help", "required arg")
            )
        for arg in oargs:
            child.add_argument(
                arg["name"], help=arg.get("help", "optional arg")
            )


class CmdTree(object):
    """
    A tree that manages the command references by cmd path like
    ['parent_cmd', 'child_cmd'].
    """

    def __init__(self, root_resource):
        """
        :type root_resource: Resource
        """
        self.root = root_resource
        self.cmd_tree = {
            "name": "root",
            "cmd": self.root,
            "children": {}
        }

    @staticmethod
    def _gen_cmd_node(cmd_name, cmd_obj):
        return {
            "name": cmd_name,
            "cmd": cmd_obj,
            "children": {}
        }

    def get_cmd_by_path(self, existed_cmd_path):
        """
        :return:
        {
            "name": cmd_name,
            "cmd": Resource instance,
            "children": {}
        }
        """
        parent = self.cmd_tree
        for cmd_name in existed_cmd_path:
            try:
                parent = parent['children'][cmd_name]
            except KeyError:
                raise ValueError(
                    "Given key [%s] in path %s does not exist in tree."
                    % (cmd_name, existed_cmd_path)
                )
        return parent

    def _add_node(self, cmd_node, cmd_path):
        """
        :type cmd_path: list or tuple
        """
        parent = self.cmd_tree
        for cmd_key in cmd_path:
            if cmd_key not in parent['children']:
                break
            parent = parent['children'][cmd_key]
        parent["children"][cmd_node['name']] = cmd_node
        return cmd_node

    @staticmethod
    def _get_paths(full_path, end_index):
        return full_path[end_index:], full_path[:end_index]

    def add_parent_commands(self, cmd_path):
        """
        Create parent command object in cmd tree then return
        the last parent command object.
        :rtype: dict
        """
        existed_cmd_end_index = self.index_in_tree(cmd_path)
        new_path, existed_path = self._get_paths(
            cmd_path,
            existed_cmd_end_index,
        )
        parent_node = self.get_cmd_by_path(existed_path)
        for cmd_name in new_path:
            sub_cmd = _add_sub_cmd(
                parent_node['cmd'], cmd_name, cmd_name
            )
            parent_node = self._gen_cmd_node(cmd_name, sub_cmd)
            self._add_node(
                parent_node,
                existed_path + new_path[:new_path.index(cmd_name)]
            )
        return parent_node

    def index_in_tree(self, cmd_path):
        """
        Return the start index of which the element is not in cmd tree.
        :type cmd_path: list or tuple
        :return: None if cma_path already indexed in tree.
        """
        current_tree = self.cmd_tree
        for key in cmd_path:
            if key in current_tree['children']:
                current_tree = current_tree['children'][key]
            else:
                return cmd_path.index(key)
        return None


def run_cmds(rest_client, prefix2ignore=None):
    """
    :param rest_client: a resource client
    :type rest_client: schema_sugar.client.client.RestClient
    :param prefix2ignore: prefix will be ignored when resource generated.
    :type prefix2ignore: basestring
    """
    # TODO(Add cmd index to avoid register a command multiple-times)
    root_resource = Resource()
    tree = CmdTree(root_resource)
    prefix2ignore = prefix2ignore or "/api/v2"
    for schema in rest_client.meta.values():
        config = SugarConfig(config_dict=schema["instance"])
        meta = _mk_cmd_meta(config, prefix2ignore, schema["url_prefix"])
        parent_node = tree.add_parent_commands(meta['cmd_path'])
        add_operation_cmd(parent_node['cmd'], meta, rest_client)

    response = root_resource.run()
    try:
        return response.json()
    except JSONDecodeError:
        logging.error("Response is not an json object.")
        return response.text