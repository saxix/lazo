#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs

from setuptools import setup

setup(name='lazo',
      version='1.1',
      description="""small utility to iteract with Rancher API""",
      long_description=codecs.open('README.md').read(),
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
