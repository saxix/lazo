#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import codecs
import os
import re

from setuptools import find_packages, setup

setup(name='lazo',
      version='1.0',
      description="""small utility to iteract with Rancher API""",
      author='Stefano Apostolico',
      author_email='s.apostolico@gmail.com',
      url='https://github.com/saxix/lazo',
      py_modules=['lazo'],
      install_requires=['click', 'colorama', 'requests'],
      entry_points={
          'console_scripts': [
              'lazo = lazo:cli',
          ],
      },
      license='MIT',
      zip_safe=False,
      keywords='',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6'
      ])
