from distutils.core import setup

setup(
    name = 'GoRDB',
    packages = ['GoRDB'],
    version = 'v.0.1',  # Ideally should be same as your GitHub release tag varsion
    description = 'A lightweight python library for implementing GraphQL on Relational DB Tables in few steps using python dicts. The library is built over strawberry-graphql for creating graphQL schema from dataclasses',
    author = 'RajaGanapathyM',
    author_email = 'rganapathy6@gmail.com',
    url = 'https://github.com/RajaGanapathyM/GoRDB',
    download_url = 'https://github.com/RajaGanapathyM/GoRDB/archive/refs/tags/v.0.1.tar.gz',
    keywords = ['GraphQL', 'RDB'],
    classifiers = [],
)
