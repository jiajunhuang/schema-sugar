#!/usr/bin/env python
# coding=utf-8
from flask import Flask, Blueprint
from schema_sugar.contrib import FlaskJar, FlaskSugar
flask_app = Flask(__name__)
jar = FlaskJar(__name__, flask_app)

cmd = jar.entry_point

bl = Blueprint("api", __name__, url_prefix="/api")

@jar.register(blue_print=bl)
class DiskSugar(FlaskSugar):
    config = {
        "schema": {
            "create": {
                "help": "command to show how this api-maker works",
                "type": "object",
                "properties":{
                    "name": {"type": "string"},
                    "size": {"type": "string"},
                },
                "required": ["username", "password"]
            },
            "support_operations": ('create', "show", "delete"),
        },
        "url": "/disk/<int:disk_id>",
        "version": "1"
    }

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def show(self, data, web_request, disk_id, **kwargs):
        return {
            "disks": [
                {'name': "disk.%s" % disk_id}
            ],
        }

def run_server():
    flask_app.register_blueprint(bl)
    flask_app.run(debug=True, host="0.0.0.0", port=7001)

if __name__ == "__main__":
    run_server()