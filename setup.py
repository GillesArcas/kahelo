#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

def readme():
    with open('README.md') as readme_file:
        return readme_file.read()

setup(
    name = 'kahelo',
    version = '1.10',
    description = 'kahelo - tile management for GPS maps',
    long_description=readme(),
    download_url = 'https://github.com/GillesArcas/kahelo',
    url = 'https://github.com/GillesArcas/kahelo',
    author = 'Gilles Arcas',
    author_email = 'gilles.arcas@gmail.com',
    packages = ['kahelo'],
    license = "MIT",
    install_requires = ['Pillow'],
    entry_points='''
        [console_scripts]
        kahelo = kahelo.kahelo:kahelo
    ''',
    )
