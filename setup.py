#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

found_packages = find_packages(where=".")
packages = ["%s" % package for package in found_packages]

if __name__ == '__main__':
    setup(
        author='PlanGrid',
        description='Tools for quickly getting a Flask service up and running',
        name='plangrid.flask-toolbox',
        packages=packages,
        install_requires=[
            'bugsnag[flask]==3.1.0',
            'Flask==0.12.1',
            'flask-swagger-ui==3.0.12a0',
            'marshmallow==2.13.5',
            'newrelic==2.46.0.37'
        ],
        version='2.1.1',
        zip_safe=True,
        namespace_packages=['plangrid'],
        url='https://github.com/plangrid/flask-toolbox'
    )
