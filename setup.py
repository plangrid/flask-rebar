#!/usr/bin/env python
from setuptools import setup, find_packages


if __name__ == "__main__":
    setup(
        name="flask-rebar",
        version="1.8.1",
        author="Barak Alon",
        author_email="barak.s.alon@gmail.com",
        description="Flask-Rebar combines flask, marshmallow, and swagger for robust REST services.",
        long_description=open("README.rst").read(),
        keywords=["flask", "rest", "marshmallow", "openapi", "swagger"],
        license="MIT",
        packages=find_packages(exclude=("test*", "examples")),
        include_package_data=True,
        install_requires=["Flask>=0.10,<2", "marshmallow>=2.13,<4"],
        url="https://github.com/plangrid/flask-rebar",
        classifiers=[
            "Environment :: Web Environment",
            "Framework :: Flask",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
            "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
            "Topic :: Software Development :: Libraries :: Application Frameworks",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
