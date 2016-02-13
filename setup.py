from setuptools import setup, find_packages
from os.path import expanduser

version = {}
with open('swk/version.py') as f:
    exec(f.read(), version)

user_home = expanduser("~")
url = 'https://github.com/trueneu/swiss-knife'

setup(name='swk',
      version=version['__version__'],
      description='Extendable command line utility for sysadmins',
      author="Pavel Gurkov",
      author_email="true.neu@gmail.com",
      url=url,
      download_url='https://github.com/trueneu/swiss-knife/archive/v{vers}.zip'.format(vers=version['__version__']),
      packages=find_packages(),
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
      keywords='cli ssh pssh swiss-knife sysadmin zabbix foreman',
      install_requires=[
          'exrex>=0.9.4',
          'paramiko>=1.16.0',
          'scp>=0.10.2',
          'pypsi>=1.3.0'
      ],
      long_description='''
An extendable utility for doing everything with self-defined hosts/hostgroups, utilizing API of your environment,
with parallel ssh out of the box with a shell mode.

Examples:
::

    swk pssh 'frontend([0-1][0-9]|2[0-5]),-frontend00' grep '/api/do_something' /var/log/nginx/access.log
    swk gather ^frontend /var/log/nginx/access.log ./nginx-logs-from-production
    swk ssh foohost,barhost,zeehost uptime

Shell mode:
::

    swk> pssh ^mysql mysql -e 'show variables like "read_only"' >> ./read_only.tmp
    swk> pssh ^mysql mysql -e 'show variables like "%format%"' | grep innodb

For more examples, please refer to README at {0}

'''.format(url),
      entry_points={
          'console_scripts': [
              'swk = swk.main:main'
          ],
      },
      data_files=[
          ('{0}/.swk'.format(user_home), ['swk/swk.ini'])
      ]
      )
