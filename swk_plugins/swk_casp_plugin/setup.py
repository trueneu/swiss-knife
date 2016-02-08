#!/usr/bin/env python

from setuptools import setup, find_packages

with open('swk_casp_plugin/version.py') as f:
    exec(f.read(), version)

url = 'https://github.com/trueneu/swiss-knife'
setup(name='swk_casp_plugin',
      version=version['__version__'],
      packages=find_packages(),
      install_requires=[
          'swk>=0.0.4a1',
          'requests>=2.9.1'
      ],
      description='Plugin for swk, enabling casp api',
      long_description='This is not a standalone program nor a library.'
                       ' You should use it in conjunction with base program, swk.'
                       ' For more information, please refer to documentation that can be found at {0}'.format(url),
      author="Pavel Gurkov",
      author_email="true.neu@gmail.com",
      url=url,
      license='GPLv3',
      platforms='Posix; MacOS X',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'Intended Audience :: End Users/Deswktop',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Topic :: System :: Systems Administration',
            'Topic :: System :: Shells',
            'Topic :: Utilities'
      ],
      keywords='cli swiss-knife sysadmin casp',
      entry_points={
          'swk_plugin': [
              'swk_casp_plugin = swk_casp_plugin.swk_casp:main'
          ],
      },
      )
