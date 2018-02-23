#!/usr/bin/env python
from setuptools import setup


if __name__ == '__main__':
    setup(
        author='Barak Alon',
        author_email='barak.s.alon@gmail.com',
        description='Flask-Rebar combines flask, marshmallow, and swagger for robust REST services.',
        long_description=open('README.rst').read(),
        keywords=['flask', 'rest', 'marshmallow', 'openapi', 'swagger'],
        name='flask-rebar',
        packages=['flask_rebar'],
        install_requires=[
            'Flask>=0.12.1',
            'marshmallow>=2.13.5',
        ],
        version='0.1.0',
        zip_safe=True,
        url='https://github.com/plangrid/flask-rebar'
    )
