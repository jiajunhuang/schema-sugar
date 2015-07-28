#!/usr/bin/env python
# coding=utf-8
from flask import Flask
from schema_sugar.contrib import FlaskJar, FlaskSugar

jar = FlaskJar(__name__, Flask(__name__))

cmd = jar.entry_point

@jar.register
class ExampleSugar(FlaskSugar):
    schema = {
        "help": "command to show how this api-maker works",
        "type": "object",
        "properties":{
            "price": {"type": "number"},
            "name": {"type": "string"}
        }
    }
    url = "/pools"

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
    schema = {
        "help": "show disk list and create disk, etc",
        "type": "object",
        "properties":{
            "pool_id": {"type": "number"},
        }
    }
    url = "/disks"

    def cli_response(self, result, **kwargs):
        print("Api running got: %s" % result)
        return result

    def show(self, data, web_request, **kwargs):
        return {
            "disks": [
                {'name': "disk1"}
            ],
        }

def run_server():
    app.run(debug=True)
