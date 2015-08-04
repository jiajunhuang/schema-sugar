#!/usr/bin/env python
# coding=utf-8
import inspect
import json
import click
import jsonschema
from abc import abstractmethod
from jsonschema import Draft4Validator
from jsonschema.exceptions import ValidationError
from .constant import SHOW_OP, OPERATIONS, CREATE_OP, UPDATE_OP, method2op, resources_method2op, \
    RESOURCES_HTTP2OP_MAP, CLI2OP_MAP, HTTP_GET
from schema_sugar.exceptions import ConfigError

__version__ = "0.0.1"


def is_abs_method(method):
    if hasattr(method, "__isabstractmethod__") \
            and method.__isabstractmethod__ is True:
        return True
    else:
        return False


class JsonForm(object):

    schema = {}

    def __init__(self, json_data, strict=False, live_schema=None):
        self.live_schema = live_schema
        if not hasattr(json_data, '__getitem__'):
            raise TypeError('json_data must be a dict.')
        if (not self.schema) and (live_schema is None):
            raise NotImplementedError('schema not implemented!')
        if live_schema is not None:
            if not self.schema:
                self.schema = live_schema
            else:
                self.schema['properties'].update(live_schema['properties'])
                if "required" in self.schema and "required" in live_schema:
                    self.schema['required'] = list(
                        set(self.schema['required']) | set(live_schema["required"]))

        Draft4Validator.check_schema(self.schema)

        self.data = {}
        if not strict:
            self._filter_data(json_data, self.schema['properties'], self.data)
        else:
            self.data = json_data
        self.validator = Draft4Validator(self.schema)
        self.errors = None

    def validate(self):
        try:
            self.validator.validate(self.data, self.schema)
            return True
        except jsonschema.ValidationError as e:
            self.errors = str(e)
            return False

    def _filter_data(self, data, properties, output):
        for key in data:
            if key in properties:
                if properties[key]['type'].lower() == 'object':
                    output[key] = {}
                    self._filter_data(data[key], properties[key][
                                      'properties'], output[key])
                elif properties[key]['type'].lower() == 'number':
                    try:
                        output[key] = int(data[key])
                    except (ValueError, TypeError):
                        output[key] = data[key]
                elif properties[key]['type'].lower() == 'string':
                    try:
                        output[key] = str(data[key])
                    except UnicodeEncodeError:
                        output[key] = data[key]
                else:
                    output[key] = data[key]


# more adapter is required for "optional", "default", etc

ARG_CONV_MAP = {
    "number": lambda name: click.argument(name, type=click.INT),
    "string": lambda name: click.argument(name, type=click.STRING),
    "boolean": lambda name: click.option("--" + name, is_flag=True, default=True),
    "default": lambda name: click.argument(name, type=click.STRING),
}


def cli_arg_generator(arg_type):
    """
    Return click argument generator function
    :param arg_type: argument type such as `string` , `number`, etc
    :type arg_type: basestring
    :rtype callable
    """
    if not isinstance(arg_type, (str, unicode)):
        raise ValueError("arg_type shoud be a string, got %s" % type(arg_type))
    return ARG_CONV_MAP.get(arg_type, ARG_CONV_MAP['default'])


class SugarConfig(object):
    _validation_schema = {
        "type": "object",
        "properties": {
            "help": {"type": "string"},
            "schema": {
                "type": "object",
            },
            "resources": {"type": "string"},
            "resource": {"type": "string"},
            "version": {"type": "number"},
            "extra_actions": {"type": "object"},
        },
        "oneOf": [
            {"required": ['resources']},
            {"required": ['resource']},
        ],
        "required": ("schema",),
        "additionalProperties": "true",
    }
    _form_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "help": {"type": "string"},
            "properties": {"type": "object"},
            "required": {"type": 'array'},
        },
        "required": ("properties", ),
    }

    def __init__(self, config_dict):
        """
        :type config_dict: dict
        """
        self.config = config_dict
        if not self.schema.get("extra_actions", None):
            self.config['extra_actions'] = {}
        self._check_config(self.config)

    @classmethod
    def _check_config(cls, config_dict):
        try:
            validator = Draft4Validator(cls._validation_schema)
            validator.validate(config_dict)
            # check validation schema
            form_validator = Draft4Validator(cls._form_schema)
            for method_schema in config_dict['schema'].values():
                form_validator.validate(method_schema)
        except ValidationError as e:
            msg = "Syntax Error in your config_dict:\n" + str(e)
            raise ConfigError("%s\n Your config is: %s" % (msg, config_dict))

    @property
    def is_plural(self):
        if "resources" in self.config:
            return True

    def add_action(self, action_name, http_method):
        self.extra_actions[action_name] = {
            "http_method": http_method,
        }

    @property
    def support_operations(self):
        return self.schema.get("support_operations")

    @property
    def resource_root(self):
        if self.config.get("resources"):
            return "/" + self.config['resources']
        else:
            return "/" + self.config['resource']

    @property
    def schema(self):
        return self.config['schema']

    @property
    def version(self):
        return self.config.get('version', 0)

    @property
    def extra_actions(self):
        return self.config['extra_actions']

    @property
    def cli_methods(self):
        return self.config.get('cli_methods', CLI2OP_MAP.keys())

    @property
    def http_methods(self):
        return self.config.get('http_methods', RESOURCES_HTTP2OP_MAP.keys())

    @classmethod
    def from_string(cls, config_string):
        """
        Create a new instance from given serialized schema string.
        :param config_string:
        """
        config = json.loads(config_string)
        return cls(config)

    def dumps(self):
        return self.config


def action(action_name, http_method=HTTP_GET):
    """
    add an extra_action to a SchemaSugarBase object
    :param action_name: the action name in url(as postfix)
    :param http_method: how does this action been visited
    """
    def wrapper(func):
        func.__is_action__ = True
        func.__action_name__ = action_name
        func.__http_method__ = http_method
        return func
    return wrapper


class SchemaSugarBase(object):
    """
    Generate resource or blue print to web app and CLI app.
    """
    _default_operation = SHOW_OP

    def __init__(self, config_dict=None):
        """
        :type config_dict: dict
        :param config_dict: if config_dict already existed in class
            properties, this will be ignored.
        """
        if not hasattr(self, "config_dict") and config_dict is not None:
            # TODO(winkidney): config validation
            self.config_dict = config_dict
        elif hasattr(self, "config_dict"):
            pass
        else:
            raise ValueError(
                "config_dict can not be None, expect dict, got %s" % config_dict)
        self.config = SugarConfig(self.config_dict)
        self._make_registry()

    def _make_registry(self):
        # make extra action map
        operations = set(OPERATIONS)
        self.config.schema['support_operations'] = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "__is_action__"):
                self.config.add_action(
                    method.__action_name__,
                    method.__http_method__,
                )
            if not is_abs_method(method):
                if name in operations:
                    self.config.schema['support_operations'].append(name)

    @abstractmethod
    def make_resources(self, *args, **kwargs):
        pass

    def make_cli(self, parent_command):
        """
        Note: refine is needed because click does not support sub command
         in nested way.
        Register me to the parent_command and return the command function.
        :param parent_command: generated by click.command() function.
        :return: a click command function
        """
        # TODO(winkidney): to improve
        def make_command_entity(passed_operation):
            def command_entity(**kwargs):
                return self._api_run(passed_operation, kwargs)
            return command_entity
        command_list = []
        for support_operation in self.config.support_operations:
            command = parent_command.command(
                name=self.config.resource_root.split(
                    "/")[1] + "_" + support_operation
            )(make_command_entity(support_operation))
            operation = self.config.schema.get(support_operation, None)
            if operation is not None:
                for parameter in operation['properties'].items():
                    command = cli_arg_generator(
                        parameter[1]["type"])(parameter[0])(command)
            command_list.append(command)
        return command_list

    def make_client_cli(self, parent_cmd):
        """
        generate rest-client cli.
        """
        pass

    def cli_response(self, result, **kwargs):
        click.echo(result)
        return result

    @abstractmethod
    def web_response(self, result, *args, **kwargs):
        pass

    @abstractmethod
    def index(self, data, web_request, **kwargs):
        pass

    @abstractmethod
    def create(self, data, web_request, **kwargs):
        pass

    @abstractmethod
    def show(self, data, web_request, **kwargs):
        return data

    @abstractmethod
    def update(self, data, web_request, **kwargs):
        pass

    @abstractmethod
    def delete(self, data, web_request, **kwargs):
        pass

    def process(self, operation, data, web_request, **kwargs):
        validate_schema = self.config.schema.get(
            operation, {"type": "object", "properties": {}})
        processed_data = self.validate(validate_schema, data)
        return getattr(self, operation)(processed_data, web_request, **kwargs)

    def crud_api(self, raw_method_name, data, web_request=None, **kwargs):
        operation = method2op(raw_method_name)
        return self._api_run(operation, data, web_request, **kwargs)

    def resources_api(self, raw_method_name, data, web_request=None, **kwargs):
        operation = resources_method2op(raw_method_name)
        return self._api_run(operation, data, web_request, **kwargs)

    def action_api(self, raw_method_name):
        operation = raw_method_name
        return lambda passed_operation, data, web_request, **kwargs: \
            self._api_run(operation, data, web_request, **kwargs)

    def _api_run(self, operation, data, web_request=None, **kwargs):
        """
        :param operation: in self.config.schema.keys()
           (index, create, show, delete, update, etc)
        """
        data = self.pre_process(data, web_request, **kwargs)
        result = self.process(operation, data, web_request, **kwargs)
        if web_request is not None:
            if isinstance(result, (tuple, list)):
                return self.web_response(*result)
            else:
                return self.web_response(result)
        else:
            return self.cli_response(result)

    @staticmethod
    def validate(validate_schema, data):
        schema = validate_schema
        form = JsonForm(data, live_schema=schema)
        if not form.validate():
            raise ValueError("%s " % form.errors)
        return form.data

    def pre_process(self, data, web_request, **kwargs):
        return data

    def get_doc(self, *args, **kwargs):
        return "This is the example doc data:\n" \
               + str(self.config.schema)


class SugarJarBase(object):

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def run(self):
        pass

    @staticmethod
    @click.group(name="SugarJarEntry")
    def entry_point():
        pass

    @abstractmethod
    def register(self, schema_sugar):
        pass


@click.command(help="To implement")
@click.argument("code_type", type=click.Choice(['flask', ]))
@click.argument("-out", default="out.py", type=click.STRING)
def code_gen(code_type, out):
    pass
