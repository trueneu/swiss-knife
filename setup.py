from setuptools import setup, find_packages

version = {}
with open('swk/version.py') as f:
    exec(f.read(), version)

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
      long_description=open("README.rst").read(),
      entry_points={
          'console_scripts': [
              'swk = swk.main:main'
          ],
      },
      include_package_data=True,
      package_data={'swk': ['swk/swk.ini']},
      )
