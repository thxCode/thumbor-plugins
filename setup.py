#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 664647065@qq.com
# Copyright (c) 2015 Thumbor-Community
# Copyright (c) 2011 globo.com timehome@corp.globo.com

import os
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = 'Thumbor plugins'


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="thumbor_thxcode",
    version="0.0.1",
    author="MaiWJ",
    description=("Thumbor plugins"),
    license="MIT",
    keywords="thumbor smart mongodb mongo",
    url="https://github.com/thxCode/thumbor",
    packages=[
        'thumbor_thxcode',
        'thumbor_thxcode.plugins'
    ],
    long_description=long_description,
    classifiers=[
        'Development Status :: 1 - Develop/Unstable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'thumbor>=5.0.0',
        'pymongo'
    ]
)