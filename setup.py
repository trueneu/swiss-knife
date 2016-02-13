from setuptools import setup, find_packages
from os import symlink
import os.path
from setuptools.command.install import install
import warnings

version = {}
with open('swk/version.py') as f:
    exec(f.read(), version)

url = 'https://github.com/trueneu/swiss-knife'


class SymlinkConfig(install):
    def run(self):
        install.run(self)
        try:
            import swk
            filename = "swk.ini"
            user_home = os.path.expanduser("~")
            target_dir = "{user_home}/.swk/".format(user_home=user_home)
            try:
                os.unlink(os.path.join(os.path.dirname(target_dir), filename))
            except:
                pass

            symlink(os.path.join(os.path.dirname(swk.__file__), filename),
                    os.path.join(os.path.dirname(target_dir), filename))
        except:
            warnings.warn("WARNING: An issue occured while symlinking config file to $HOME/.swk .")


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
      package_data={'swk': ['swk/swk.ini']},
      cmdclass={'install': SymlinkConfig}
      )
