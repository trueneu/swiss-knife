from setuptools import setup, find_packages

setup(name='swk_example_plugin',
      version='1.0',
      packages=find_packages(),
      install_requires=[
          'swk>=0.0.4a0'
      ],
      entry_points={
          'swk_plugin': [
              'swk_example_plugin = swk_example_plugin.command_example:main'
          ],
      },
      )
