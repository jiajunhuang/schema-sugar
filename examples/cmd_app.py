#!/usr/bin/env python
# coding=utf-8
from flask import Flask, Blueprint
from schema_sugar.contrib import FlaskJar, FlaskSugar
flask_app = Flask(__name__)
jar = FlaskJar(__name__, flask_app)

cmd = jar.entry_point

@jar.register
class ExampleSugar(FlaskSugar):
    config = {
        "schema": {
            "help": "command to show how this api-maker works",
            "type": "object",
            "properties":{
                "price": {"type": "number"},
                "name": {"type": "string"}
            }
        },
        "url": "/pools",
        "version": "1"
    }

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def show(self, data, web_request, **kwargs):
        return {
            "pools": [
                {'name': "pool1"}
            ],
        }

bl = Blueprint("api", __name__, url_prefix="/api")

@jar.register(blue_print=bl)
class DiskSugar(FlaskSugar):
    config = {
        "schema": {
            "help": "show disk list and create disk, etc",
            "type": "object",
            "properties":{
                "pool_id": {"type": "number"},
            }
        },
        "url": "/disks/<int:disk_id>",
        "version": "1",
    }

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def show(self, data, web_request, disk_id):
        return {
            "disks": [
                {'name': "disk.%s" % disk_id}
            ],
        }

def run_server():
    flask_app.register_blueprint(bl)
    flask_app.run(debug=True, host="0.0.0.0")

if __name__ == "__main__":
    run_server()