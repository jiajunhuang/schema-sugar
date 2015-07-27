import os
from setuptools import setup, find_packages

setup(name='flask_cmd',
      packages=find_packages(".", include=['flask_cmd']),
      include_package_data=True,
      install_requires=[
          'jsonschema',
          'flask',
      ]
      )
