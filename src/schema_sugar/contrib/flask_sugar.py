#!/usr/bin/env python
# coding: utf-8
from functools import wraps
from flask import request, jsonify, Blueprint
from schema_sugar import SugarJarBase, SchemaSugarBase

__all__ = (
    "FlaskSugar", "FlaskJar"
)

class FlaskSugar(SchemaSugarBase):

    def make_resource(self, decorators=()):
        """
        register resource to flask, if blue_print is not None, it will be
         registered to blue_print, else the app.
        :param app: flask app
        :param decorators: flask_decorators, pass it here
        :param blue_print:
        :return:
        """

        def resource(*args, **kwargs):
            if request.method == "POST":
                data = request.get_json(force=True)
            else:
                data = request.args
            return self._api_run(data, request.method, web_request=request, **kwargs)

        for decorator in decorators:
            resource = decorator(resource)
        return resource

    def web_response(self, result, http_code=200):
        return jsonify(result), http_code


class FlaskJar(SugarJarBase):
    def __init__(self, name, flask_app):
        """
        :type flask_app: flask.Flask
        """
        super(FlaskJar, self).__init__(name)
        self.registry = set()
        self.app = flask_app

    def run(self, *args, **kwags):
        self.app.run(*args, **kwags)

    def register(self, schema_sugar_class=None, blue_print=None, args=(), kwargs={}):
        """
        :type schema_sugar_class: schema_sugar.contrib.flask_sugar.FlaskSugar
        """
        if schema_sugar_class is not None and not issubclass(schema_sugar_class, FlaskSugar):
            raise TypeError(
                "schema_sugar_class parameter expects %s, got %s" %
                (FlaskSugar, schema_sugar_class)
            )
        if blue_print is not None and not isinstance(blue_print, Blueprint):
            raise TypeError("expect %s, got %s" % (Blueprint, schema_sugar_class))

        if blue_print or args or kwargs:
            def wrapper(schema_class):
                return self._register(schema_class(*args, **kwargs), blue_print=blue_print)
            return wrapper
        else:
            return self._register(schema_sugar_instance=schema_sugar_class())

    def _register(self, schema_sugar_instance, blue_print=None):
        """
        :type schema_sugar_instance: schema_sugar.contrib.flask_sugar.FlaskSugar
        """
        schema_sugar = schema_sugar_instance
        self.registry.add(schema_sugar)
        schema_sugar.make_cli(self.entry_point)

        resource = schema_sugar.make_resource()
        if blue_print is not None:
            route_proxy = blue_print
        else:
            route_proxy = self.app

        route_proxy.add_url_rule(
            schema_sugar.url, endpoint=schema_sugar.url+"-endpoint",
            view_func=resource, methods=schema_sugar.http_methods,
        )
        route_proxy.add_url_rule(
            schema_sugar.url + "/meta", endpoint=schema_sugar.url+"-doc",
            view_func=schema_sugar.get_doc, methods=("GET", ),
        )