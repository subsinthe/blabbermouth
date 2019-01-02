#!/usr/bin/env python

from setuptools import find_packages, setup

name = "blabbermouth"
version = "1.1"

with open("requirements.install.txt", "rt") as f:
    install_requires = f.read()

setup(
    name=name,
    version=version,
    author="Vladimir Golubev",
    author_email="subsinthe@gmail.com",
    description=(
        "Chatting telegram bot powered by your talks and markov chains"
    ),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    entry_points={"console_scripts": ["blabbermouth = blabbermouth.cli:main"]},
    install_requires=install_requires,
)
