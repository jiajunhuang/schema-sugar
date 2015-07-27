from setuptools import setup

setup(name='cmd_ex',
      include_package_data=True,
      py_modules=['cmd_app'],
      entry_points={
          'console_scripts': [
              'rest-cmd = cmd_app:cmd',
              'rest-server = cmd_app:run_server',
          ],
      },
      )
