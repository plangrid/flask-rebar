#!/usr/bin/env python
from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        author='PlanGrid',
        description='Tools for quickly getting a Flask service up and running',
        name='plangrid.flask-toolbox',
        packages=find_packages(where=".", exclude=['tests*', 'examples']),
        install_requires=[
            'bugsnag[flask]~=3.4.0',
            'Flask==0.12.1',
            'flask-swagger-ui==3.0.12a0',
            'marshmallow==2.13.5',
            'newrelic==2.46.0.37'
        ],
        version='2.7.0',
        zip_safe=True,
        namespace_packages=['plangrid'],
        url='https://github.com/plangrid/flask-toolbox'
    )
