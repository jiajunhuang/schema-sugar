#!/usr/bin/env python
# coding=utf-8
from flask import Flask
from schema_sugar.contrib import FlaskJar, FlaskSugar

jar = FlaskJar(__name__, Flask(__name__))

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


@jar.register
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
    jar.run(debug=True, host="0.0.0.0")
