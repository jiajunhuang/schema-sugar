# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

from collections import namedtuple
import flask
from flask import (
    request,
    jsonify,
    Blueprint,
    Response,
)

from schema_sugar import SugarJarBase, SchemaSugarBase, MethodNotImplement
from schema_sugar.client.parser import _mk_url
from schema_sugar.constant import RESOURCES_HTTP2OP_MAP, RESOURCE_HTTP2OP_MAP, OP2HTTP_MAP

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
                if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                    # TODO(winkidney): To improve. User should always
                    # know if the  data is "request body" or just "query string"
                    data = request.get_json(force=True, silent=True) or {}
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
            for name, action in self.config.extra_actions.items():
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
        if isinstance(result, Response):
            return result
        return jsonify(result), http_code


class FlaskJar(SugarJarBase):

    def __init__(self, name, flask_app):
        """
        :type flask_app: flask.Flask
        """
        super(FlaskJar, self).__init__(name)
        self.registry = set()
        self._registry = set()
        self.app = flask_app
        self.app.add_url_rule(
            "/meta", endpoint="site_map",
            view_func=self.sitemap_view
        )

        self.app.register_error_handler(
            MethodNotImplement, self.not_support_view
        )

        self._sitemap = {}

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
                self._register(
                    schema_class(*args, **kwargs),
                    blue_print=blue_print,
                    decorators=decorators,
                )
                return schema_class
            return wrapper
        else:
            return self._register(schema_sugar_class(), decorators=decorators)

    @staticmethod
    def _get_end_point(url):
        """
        Wach url to flask end_point string.
        :type url: str
        :rtype: str
        """
        return url.replace(".", "_")

    def _register(self, schema_sugar_instance, blue_print=None, decorators=None):
        """
        :type schema_sugar_instance: schema_sugar.contrib.flask_sugar.FlaskSugar
        :type blue_print: Blueprint
        """
        schema_sugar = schema_sugar_instance
        if schema_sugar.__class__.__name__ in self._registry:
            return
        self._registry.add(schema_sugar.__class__.__name__)
        self.registry.add(schema_sugar)

        rules = schema_sugar.make_resources(decorators=decorators)

        url_prefix = "/"
        if blue_print is not None:
            route_proxy = blue_print
            url_prefix = route_proxy.url_prefix
        else:
            route_proxy = self.app
        for rule in rules:
            route_proxy.add_url_rule(
                rule.url,
                endpoint=self._get_end_point(rule.url) + "_endpoint",
                methods=rule.methods,
                view_func=rule.res_func,
            )
        res_name = schema_sugar.config.resource_detail["name"]
        is_singular = schema_sugar.config.resource_detail["is_singular"]
        self._add2index(
            url_prefix,
            res_name,
            schema_sugar.config.dumps(),
            dict(
                (
                    op,
                    {
                        "url": _mk_url(res_name, url_prefix, is_singular, op),
                        "method": OP2HTTP_MAP[op]
                    }
                ) for op in schema_sugar.config.support_operations
            )
        )

        return rules

    def has_no_empty_params(self, rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    def _add2index(self, prefix, resource_name, sugar_dump, rules):
        """
        Put the rule into the index.
        """
        self._sitemap[self._get_key(prefix, resource_name)] = {
            "name": resource_name,
            "instance": sugar_dump,
            "url_prefix": prefix,
            "rules": rules
        }

    @staticmethod
    def _get_key(prefix, resource_name):
        """
        Get index key for given resource
        :rtype: str
        """
        return "%s %s" % (prefix, resource_name)

    def sitemap_view(self):
        return jsonify(self._sitemap)
