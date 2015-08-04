#!/usr/bin/env python
# coding=utf-8
from flask import Flask, Blueprint, jsonify
from schema_sugar import action
from schema_sugar.contrib import FlaskJar, FlaskSugar
flask_app = Flask(__name__)
jar = FlaskJar(__name__, flask_app)

cmd = jar.entry_point

bl = Blueprint("api", __name__, url_prefix="/api")
bl2 = Blueprint("bl2", "bl2", url_prefix="/api")

@jar.register(blue_print=bl)
class DiskSugar(FlaskSugar):
    config_dict = {
        "schema": {
            "create": {
                "help": "command to show how this api-maker works",
                "type": "object",
                "properties":{
                    "name": {"type": "string"},
                    "size": {"type": "string"},
                },
                "required": ["name", "size"]
            },
            "index": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        },
        "resources": "disks",
        # single resource and resources will be generated automatically
        "version": 1,
    }

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def index(self, data, web_request, **kwargs):
        # if you visit /api/disks?name=value&hello=world
        # this data will be {"name":"value"} because JsonForm will
        # delete extra data not in schema.
        return {
            "received_filters": data,
            "data": "this is test disk api",
        }

    def show(self, data, web_request, id, **kwargs):
        return {
            "disks": [
                {'name': "disk.%s" % id}
            ],
        }

    def create(self, data, web_request, **kwargs):
        return {"result": "create_successfully!"}



@jar.register(blue_print=bl)
class EarthSugar(FlaskSugar):
    config_dict = {
        "schema": {
            "create": {
                "help": "command to show how this api-maker works",
                "type": "object",
                "properties":{
                    "name": {"type": "string"},
                    "size": {"type": "string"},
                },
                "required": ["name", "size"]
            },
        },
        "resource": "earth",
        # single resource and resources will be generated automatically
        "version": 1,
    }

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def show(self, data, web_request, **kwargs):
        return {
            "pools": [
                {'name': "earth.%s" % data}
            ],
        }

    @action("edit")
    def edit(self, data, web_request, **kwargs):
        return {
            "pools": [
                {'name': "pool edit view"}
            ],
        }


@jar.register(blue_print=bl)
class SingleSugar(FlaskSugar):
    config_dict = {
        "schema": {},
        "resource": "cluster",
        "out_fields": {
            "show": ["field1"],
        }
    }

    def create(self, data, web_request, **kwargs):
        return {"hello": "this a standalone cluster"}

    def show(self, data, web_request, **kwargs):
        return {
            "field1": "hello",
            "field2": "field2, will not be displayed",
        }

def run_server():
    flask_app.register_blueprint(bl)
    flask_app.register_blueprint(bl2)
    flask_app.run(debug=True, host="0.0.0.0", port=7001)


if __name__ == "__main__":
    run_server()