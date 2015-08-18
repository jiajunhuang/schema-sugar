# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

from collections import namedtuple
from flask import request, jsonify, Blueprint, url_for
from werkzeug.datastructures import MultiDict
from schema_sugar import SugarJarBase, SchemaSugarBase, MethodNotImplement
from schema_sugar.constant import RESOURCES_HTTP2OP_MAP, RESOURCE_HTTP2OP_MAP

__all__ = (
    "FlaskSugar", "FlaskJar"
)

ResRule = namedtuple("UrlRule", ("url", "methods", "res_func"))


class FlaskSugar(SchemaSugarBase):

    def make_resources(self, decorators=None):
        """
        register resource to flask, if blue_print is not None, it will be
         registered to blue_print, else the app.
        :param decorators: flask_decorators, pass it here
        :rtype: list
        """
        rules = []

        def make_resource(api_function):
            def resource(**kwargs):
                if request.method in ("POST", "PUT", "PATCH"):
                    data = request.get_json(force=True)
                else:
                    data = request.args
                return api_function(
                    request.method, data,
                    web_request=request, **kwargs
                )

            if decorators is not None:
                for decorator in decorators:
                    resource = decorator(resource)
            return resource

        if self.config.is_plural:
            rules.append(
                ResRule(
                    url=self.config.resource_root,
                    methods=[x.upper() for x in RESOURCES_HTTP2OP_MAP.keys()],
                    res_func=make_resource(self.resources_api)
                )
            )
            rules.append(
                ResRule(
                    url=self.config.resource_root + "/<id>",
                    methods=[x.upper() for x in RESOURCE_HTTP2OP_MAP.keys()],
                    res_func=make_resource(self.crud_api)
                )
            )
            for name, action in self.config.extra_actions:
                rules.append(
                    ResRule(
                        url=self.config.resource_root + "/<id>/" + name,
                        methods=(action['http_method'], ),
                        res_func=make_resource(self.action_api(name)),
                    )
                )
        else:
            rules.append(
                ResRule(
                    url=self.config.resource_root,
                    methods=[x.upper() for x in RESOURCE_HTTP2OP_MAP.keys()],
                    res_func=make_resource(self.crud_api)
                )
            )
            for name, action in self.config.extra_actions.items():
                rules.append(
                    ResRule(
                        url=self.config.resource_root + "/" + name,
                        methods=(action['http_method'], ),
                        res_func=make_resource(self.action_api(name)),
                    )
                )

        rules.append(
            ResRule(
                url=self.config.resource_root + "/meta",
                methods=('GET', ), res_func=self.get_doc
            )
        )

        return rules

    def web_response(self, result, http_code=200):
        if isinstance(result, (dict, MultiDict)):
            return jsonify(result), http_code
        else:
            return result, http_code


class FlaskJar(SugarJarBase):

    def __init__(self, name, flask_app):
        """
        :type flask_app: flask.Flask
        """
        super(FlaskJar, self).__init__(name)
        self.registry = set()
        self._registry = set()
        self.app = flask_app
        self.app.add_url_rule("/meta", endpoint="site_map",
                              view_func=self.site_map)

        self.app.register_error_handler(
            MethodNotImplement, self.not_support_view
        )

    @staticmethod
    def not_support_view(exception):
        return str(exception), 501

    def run(self, *args, **kwags):
        self.app.run(*args, **kwags)

    def register(
            self, schema_sugar_class=None, blue_print=None,
            decorators=None, args=None, kwargs=None):
        """
        :param args: args passed to schema_sugar_class
        :param kwargs: kwargs passed to schema_sugar_class
        :type args: list or tuple
        :type kwargs: dict
        :type schema_sugar_class: schema_sugar.contrib.flask_sugar.FlaskSugar
        :type decorators: a list of flask view decorator
        """
        if schema_sugar_class is not None \
                and not issubclass(schema_sugar_class, FlaskSugar):
            raise TypeError(
                "schema_sugar_class parameter expects %s, got %s" %
                (FlaskSugar, schema_sugar_class)
            )
        if blue_print is not None \
                and not isinstance(blue_print, Blueprint):
            raise TypeError("expect %s, got %s" %
                            (Blueprint, schema_sugar_class))

        if blue_print or args or kwargs:
            args = args or []
            kwargs = kwargs or {}

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
        if schema_sugar.__class__.__name__ in self._registry:
            return
        self._registry.add(schema_sugar.__class__.__name__)
        self.registry.add(schema_sugar)
        schema_sugar.make_cli(self.entry_point)

        rules = schema_sugar.make_resources(decorators=decorators)
        if blue_print is not None:
            route_proxy = blue_print
        else:
            route_proxy = self.app
        for rule in rules:
            route_proxy.add_url_rule(
                rule.url, endpoint=rule.url + "_endpoint",
                methods=rule.methods, view_func=rule.res_func
            )
        return rules

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
