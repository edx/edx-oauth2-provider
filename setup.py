#!/usr/bin/env python

from setuptools import setup, find_packages

import edx_oauth2_provider

setup(
    name='edx-oauth2-provider',
    version=edx_oauth2_provider.__version__,
    description='Provide OAuth2 access to edX installations',
    author='edX',
    url='https://github.com/edx/edx-oauth2-provider',
    license='AGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'django>=1.8.7,<1.9',
        'edx-django-oauth2-provider>=0.3.0,<2.0.0',
        'PyJWT>=1.4.0,<2.0.0'
    ]
)
