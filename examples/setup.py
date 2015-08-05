# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

from setuptools import setup

setup(name='cmd_app',
      include_package_data=True,
      py_modules=['cmd_app'],
      entry_points={
          'console_scripts': [
              'rest-cmd = cmd_app:cmd',
              'rest-server = cmd_app:run_server',
          ],
      },
      )
