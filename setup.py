from setuptools  import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name = 'GoRDB',
    packages = ['GoRDB'],
    version = 'V006.2',  # Ideally should be same as your GitHub release tag varsion
    description = 'A lightweight python library for implementing GraphQL on Relational DB Tables in few steps using python dicts. The library is built over strawberry-graphql for creating graphQL schema from dataclasses',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author = 'RajaGanapathyM',
    author_email = 'rganapathy6@gmail.com',
    url = 'https://github.com/RajaGanapathyM/GoRDB',
    download_url = 'https://github.com/RajaGanapathyM/GoRDB/archive/refs/tags/v.0.1.tar.gz',
    keywords = ['GraphQL', 'RDB'],
    classifiers = ['License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
)