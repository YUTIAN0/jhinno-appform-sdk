#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from setuptools import find_packages, setup

VERSION_FILE = Path(__file__).resolve().parent / "appform_sdk" / "VERSION"
version = VERSION_FILE.read_text(encoding="utf-8").strip()

setup(
    name="jhinno-appform-sdk",
    version=version,
    description="Python SDK for Appform 6.0-6.6 API",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Appform SDK Developer",
    author_email="developer@example.com",
    url="https://github.com/YUTIAN0/jhinno-appform-sdk",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "appform_sdk": ["*.yaml", "*.yml", "*.json", "VERSION"],
    },
    install_requires=[
        "requests>=2.28.0",
        "pycryptodome>=3.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "appform=appform_sdk.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    keywords="appform api sdk hpc cluster jhinno",
)
