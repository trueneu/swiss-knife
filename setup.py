#!/usr/bin/env python

from setuptools import setup, find_packages
from os.path import expanduser

version = {}
with open('swk/version.py') as f:
    exec(f.read(), version)

user_home = expanduser("~")

setup(name='swk',
      version=version['__version__'],
      description='Extendable command line utility for sysadmins',
      author="Pavel Gurkov",
      author_email="true.neu@gmail.com",
      url='https://github.com/trueneu/swiss-knife',
      packages=find_packages(),
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
      keywords='cli ssh pssh swiss-knife sysadmin',
      install_requires=[
          'exrex>=0.9.4',
          'paramiko>=1.16.0',
          'scp>=0.10.2'
      ],
      long_description='Please use pip install swk -r requirements_all.txt to get all plugins up and running',
      entry_points={
          'console_scripts': [
              'swk = swk.swk:main'
          ],
      },
      data_files=[
          ('{0}/.swk'.format(user_home), ['swk.ini'])
      ]
      )
