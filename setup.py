#!/usr/bin/env python

from setuptools import setup

setup(
    name='edx-oauth2-provider',
    version='0.5.2',
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
    packages=['oauth2_provider'],
    dependency_links=[
        'git+https://github.com/edx/django-oauth2-provider@0.2.7-fork-edx-5#egg=django-oauth2-provider-0.2.7-fork-edx-5',
    ],
    install_requires=[
        'django-oauth2-provider==0.2.7-fork-edx-5',
        'PyJWT==1.0.1'
    ]
)
