#!/bin/sh

find swk_plugins_bundle -type f -name '*.py' | while read plugin ; do ln -s "${plugin}" `basename "${plugin}"` ; done
