#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import codecs
import os
import re

from setuptools import setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
script = os.path.join(ROOT, 'lazo.py')

rel = lambda *args: os.path.join(ROOT, 'src', 'requirements', *args)

with open(script, 'rb') as f:
    content = f.read().decode('utf-8')
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    version = str(ast.literal_eval(_version_re.search(content).group(1)))

setup(name='lazo',
      version=version,
      description="""small utility to iteract with Rancher API""",
      long_description=codecs.open('README.md').read(),
      long_description_content_type='text/markdown',
      author='Stefano Apostolico',
      author_email='s.apostolico@gmail.com',
      url='https://github.com/saxix/lazo',
      py_modules=['lazo'],
      install_requires=['click==7.0',
                        'colorama==0.4.1',
                        'requests==2.21.0'],
      entry_points={
          'console_scripts': [
              'lazo = lazo:cli',
          ],
      },
      license='MIT',
      zip_safe=False,
      keywords='rancher',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6'
      ])
