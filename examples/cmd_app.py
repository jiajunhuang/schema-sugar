#!/usr/bin/env python
# coding=utf-8
import click
from flask import Flask
from flask_cmd import FlaskAPIGenerator
from flask_cmd import FlaskAPI


# run code and register
app = FlaskAPI(__name__, Flask(__name__))

cmd = app.entry_point

@app.register
class ExampleGenerator(FlaskAPIGenerator):
    schema = {
        "help": "command to show how this api-maker works",
        "type": "object",
        "properties":{
            "price": {"type": "number"},
            "name": {"type": "string"}
        }
    }
    url = "/pools"

    @classmethod
    def cli_response(cls, result):
        print("This data is from cli: %s" % result)
        return result

    @classmethod
    def process(cls, data, web_request):
        # execute api and parse response
        return {"data": "processed by backend!"}


def run_server():
    app.run(debug=True)
