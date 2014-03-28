#!/usr/bin/python
# -*- coding: utf-8 -*-

from distutils.core import setup
import py2exe  # @UnresolvedImport

setup(name='Hurón',
      version='1.0',
      description='Descarga cualquier playlist desde 8tracks.',
      author='José Cols',
      author_email='josecolsg@gmail.com',
      url='https://github.com/josecols/huron/',
      packages=['huron'],
      install_requires=['requests>=2.2.1', 'mutagen>=1.2'],
      data_files=['huron/cacert.pem'],
      console=['huron/huron.py']
)