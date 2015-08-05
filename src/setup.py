# -*- coding: utf-8 -*-
# Copyright (c) 2013-2015, SMARTX
# All rights reserved.

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(name='schema-sugar',
      packages=find_packages(here, include=['schema_sugar']),
      include_package_data=True,
      install_requires=[
          'jsonschema',
          'flask',
          'click',
      ],
      entry_points={
          'console_scripts': [
              'sugar-gen = schema_sugar:gen_code',
          ],
      },
      )
