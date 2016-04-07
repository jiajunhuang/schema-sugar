import json
import logging
from urlparse import urljoin

from schema_sugar.client.constant import (
    DEFAULT_SERVER,
    DEFAULT_PORT,
    REQUIRED_PROPERTIES,
)


class ClientConfig(object):
    def __init__(self, config_file=None):
        self._config = None
        self.username = None
        self.password = None
        self.base_url = None
        if config_file is not None:
            try:
                with open(config_file, "r") as config_fp:
                    self._config = json.load(config_fp)
            except IOError:
                logging.error(
                    "Can not open config file: %s" % config_file
                )
                raise
        else:
            self._config = {
                "username": "root",
                "password": "111111",
                "server": DEFAULT_SERVER,
                "port": DEFAULT_PORT,
            }
            logging.warn("No config file given, default config will be used")
        self._init_cfg(self._config)

    def _init_cfg(self, config):
        for field in REQUIRED_PROPERTIES:
            if field not in config:
                raise AttributeError(
                    "Field '%s' doesn't exist in config:\n '%s'"
                        % (field, config)
                    )
        self.username = config["username"]
        self.password = config["password"]
        self.base_url = "http://{host}:{port}/".format(
            host=config['server'],
            port=config['port'],
        )
        return config

    def gen_url(self, path):
        return urljoin(self.base_url, path)