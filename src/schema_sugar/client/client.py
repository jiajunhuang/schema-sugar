# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.
import json
import logging
import requests

from schema_sugar.client.config import ClientConfig
from schema_sugar.client.constant import (
    DEFAULT_META_PATH,
)


class RestClient(object):
    def __init__(self, url_parser, config_file=None):
        """
        :param config_file: config_file path
        :type config_file: str
        :param url_parser: parse the url as arguments,
         we assume that the parser returns list like
         ((converter, arguments, variable), )
         variable is argument-name(in url),
         converter is the argument's for example 'int'.
         if converter is None, the argument is not an
         dynamic part in this url.
        """
        self.config = ClientConfig(config_file)
        self.parse_url = url_parser
        self.meta = self._fetch_meta()

    def _fetch_meta(self, meta_path=DEFAULT_META_PATH):
        url = self.config.gen_url(meta_path)
        response = requests.get(url)
        return response.json()

    def send_request(
        self, path, method, params=None, data=None, headers=None
    ):
        method, params, data, headers = self.before_request(
            method, params, data, headers
        )
        url = self.config.gen_url(path)
        logging.debug(
            "Rest cli request sending: %s %s" % (method.upper(), url)
        )
        if isinstance(data, dict):
            data = json.dumps(data)
        if method.lower() == "get":
            data = None
        return getattr(requests, method.lower())(
            url, params=params, data=data, headers=headers
        )

    def before_request(self, method, params, data, headers):
        return method, params, data, headers
