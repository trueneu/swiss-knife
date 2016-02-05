#!/usr/bin/env python

from distutils.core import setup

version = {}
with open('sk/version.py') as f:
    exec(f.read(), version)

setup(name='sk',
      version=version['__version__'],
      description='Extendable command line utility for sysadmins',
      author="Pavel Gurkov",
      author_email="true.neu@gmail.com",
      url='https://github.com/trueneu/swiss-knife',
      packages=['sk'],
      license='GPLv3',
      platforms='Posix; MacOS X',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'Intended Audience :: End Users/Desktop',
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
      long_description='Please use pip install sk -r requirements_all.txt to get all plugins up and running'
      )
