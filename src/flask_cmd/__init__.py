#!/usr/bin/env python
# coding=utf-8
from abc import abstractmethod
from functools import wraps

import click
from flask import Flask, request, jsonify
from jsonschema import Draft4Validator
import jsonschema



class JsonForm(object):

    schema = {}

    def __init__(self, json_data):
        if not hasattr(json_data, '__getitem__'):
            raise TypeError('json_data must be a dict.')
        if not self.schema:
            raise NotImplementedError('schema not implemented!')
        Draft4Validator.check_schema(self.schema)

        self.data = {}
        self._filter_data(json_data, self.schema['properties'], self.data)
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
                    self._filter_data(data[key], properties[key]['properties'], output[key])
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
conv_map = {
    "number": lambda name: click.argument(name, type=click.INT),
    "string": lambda name: click.argument(name, type=click.STRING)
}


class APIGeneratorBase(object):

    url = None
    schema = None

    @classmethod
    @abstractmethod
    def resource_maker(cls, ):
        pass

    @classmethod
    def cli_maker(cls, parent_command):

        def command_entity(**kwargs):
            return cls._api_run(kwargs)

        command = parent_command.command(name=cls.url, help=cls.schema['help'])(command_entity)
        for property in cls.schema['properties'].items():
            command = conv_map[property[1]["type"]](property[0])(command)
        return command

    @classmethod
    def cli_response(cls, result):
        return jsonify(result)

    @classmethod
    def web_response(cls, result):
        return jsonify(result), 200

    @classmethod
    @abstractmethod
    def process(cls, data, **kwargs):
        pass

    @classmethod
    def _api_run(cls, data, web_request=None, **kwargs):
        data = cls._pre_processing(data, web_request, **kwargs)

        result = cls.process(data, web_request, **kwargs)
        if web_request is not None:
            return cls.web_response(result)
        else:
            return cls.cli_response(result)

    @classmethod
    def _pre_processing(cls, data, web_request, **kwargs):
        # check user permission or something else

        # validation
        class FormClass(JsonForm):
            schema = cls.schema
        form = FormClass(data)
        if not form.validate():
            raise ValueError("ValueError :%s " % form.errors)
        return form.data

    @classmethod
    def get_doc(cls):
        return "This is the example doc data:\n" + str(cls.schema)


class FlaskAPIGenerator(APIGeneratorBase):

    methods = ['GET']

    @classmethod
    def resource_maker(cls, app, methods, decorators=()):

        def resource():
            if request.method == "POST":
                data = request.get_json(force=True)
            else:
                data = request.args
            return cls._api_run(data, web_request=request)

        app.route(cls.url, methods=methods)(resource)
        app.route(cls.url + "/meta", methods=["GET"])(cls.get_doc)

class RobotAPPBase(object):

    def __init__(self, name):
        self.name = name
        self.registry = set()

    @abstractmethod
    def run(self):
        pass

    @staticmethod
    @click.group()
    def entry_point():
        pass

    @abstractmethod
    def register(self, api_generator):
        pass

class FlaskAPI(RobotAPPBase):
    def __init__(self, name, flask_app, **kwargs):
        super(FlaskAPI, self).__init__(name)
        self.app = flask_app

    def run(self, *args, **kwags):
        self.app.run(*args, **kwags)

    def register(self, api_generator):
        self.registry.add(api_generator)
        api_generator.cli_maker(self.entry_point)
        api_generator.resource_maker(self.app, api_generator.methods)