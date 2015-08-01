#!/usr/bin/env python
# coding: utf-8
from flask import request, jsonify, Blueprint, url_for
from schema_sugar import SugarJarBase, SchemaSugarBase

__all__ = (
    "FlaskSugar", "FlaskJar"
)

class FlaskSugar(SchemaSugarBase):

    def make_resource(self, decorators=None):
        """
        register resource to flask, if blue_print is not None, it will be
         registered to blue_print, else the app.
        :param app: flask app
        :param decorators: flask_decorators, pass it here
        :param blue_print:
        :return:
        """

        def resource(*args, **kwargs):
            if request.method in ("POST", "PUT"):
                data = request.get_json(force=True)
            else:
                data = request.args
            return self._api_run(data, request.method, web_request=request, **kwargs)
        if decorators is not None:
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
        self.app.add_url_rule("/meta", endpoint="site_map", view_func=self.site_map)

    def run(self, *args, **kwags):
        self.app.run(*args, **kwags)

    def register(self, schema_sugar_class=None, blue_print=None, decorators=None, args=(), kwargs={}):
        """
        :param args: args passed to schema_sugar_class
        :param kwargs: kwargs passed to schema_sugar_class
        :type args: list or tuple
        :type kwargs: dict
        :type schema_sugar_class: schema_sugar.contrib.flask_sugar.FlaskSugar
        :type decorators: a list of flask view decorator
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
                return self._register(
                    schema_class(*args, **kwargs),
                    blue_print=blue_print,
                    decorators=decorators,
                )
            return wrapper
        else:
            return self._register(schema_sugar_class(), decorators=decorators)

    def _register(self, schema_sugar_instance, blue_print=None, decorators=None):
        """
        :type schema_sugar_instance: schema_sugar.contrib.flask_sugar.FlaskSugar
        """
        schema_sugar = schema_sugar_instance
        self.registry.add(schema_sugar)
        schema_sugar.make_cli(self.entry_point)

        resource = schema_sugar.make_resource(decorators=decorators)
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
        return resource

    def has_no_empty_params(self, rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    def site_map(self):
        links = []
        for rule in self.app.url_map.iter_rules():
            if "GET" in rule.methods and self.has_no_empty_params(rule):
                url = url_for(rule.endpoint)
                links.append((url, rule.methods, rule.endpoint))
        return "All api listed by url and name, " + \
            "view them with postfix `meta/`:<br>" + \
            "<br>".join(str(x) for x in links)