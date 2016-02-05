#!/bin/sh

find sk-modules-bundle -type f -name '*.py' | while read plugin ; do ln -s "${plugin}" `basename "${plugin}"` ; done
