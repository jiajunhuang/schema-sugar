# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

from flask import Flask, Blueprint, jsonify
from schema_sugar import action
from schema_sugar.contrib import FlaskJar, FlaskSugar
flask_app = Flask(__name__)
jar = FlaskJar(__name__, flask_app)

cmd = jar.entry_point

bl = Blueprint("api", __name__, url_prefix="/api")
bl2 = Blueprint("bl2", "bl2", url_prefix="/api")

# registered with blue print
@jar.register(blue_print=bl)
class DiskSugar(FlaskSugar):
    config_dict = {
        "schema": {
            "create": {
                "help": "command to show how this api-maker works",
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "size": {"type": "string"},
                },
                # required field for "create" operation
                "required": ["name", "size"]
            },
            # params requires for index operation
            # because "index" maps to http "GET",
            # the params check will run on url-params
            # not the json-request-body
            "index": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        },
        # singular resource and resources will be generated automatically
        # for a "resources", "index", "create" maps to "GET /disks" and
        # "POST /disks", "show", "delete", "update" maps to
        # "GET /disks/<id>", "DELETE /disks/<id>", "PUT /disks/<id>"
        "resources": "disks",

        "version": 1,
    }

    def cli_response(self, result, **kwargs):
        # define response to cli
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

    # action support for a single resource
    # will be registered to "/disks/<id>/edit"
    # for "resources", it will be "/earth/edit"
    @action("edit", http_method="GET")
    def edit(self, data, web_request, id, **kwargs):
        return {
            "pools": [
                {'name': "pool edit view"}
            ],
        }


@jar.register(blue_print=bl)
class SingularSugar(FlaskSugar):
    config_dict = {
        "schema": {
            "delete": {
                "type": "object",
                "help": "this is the help"
            }
        },
        "resource": "cluster",
        "out_fields": {
            "show": ["field1"],
        }
    }

    def create(self, data, web_request, **kwargs):
        return {"hello": "this a standalone cluster"}

    # out_put filter works, the field2 will not be displayed
    # out_fields only works for a dict, other response type
    # will be returned as it was.
    def show(self, data, web_request, **kwargs):
        return {
            "field1": "hello",
            "field2": "field2, will not be displayed",
        }

    def delete(self, data, web_request, **kwargs):
        pass

def run_server():
    flask_app.register_blueprint(bl)
    flask_app.register_blueprint(bl2)
    flask_app.run(debug=True, host="0.0.0.0", port=7001)


if __name__ == "__main__":
    run_server()