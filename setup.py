#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for ProjetImo - Application de Gestion Immobilière
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="projetimo",
    version="1.0.0",
    author="ProjetImo Team",
    author_email="contact@projetimo.com",
    description="Application Django complète pour la gestion immobilière",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/projetimo",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/projetimo/issues",
        "Documentation": "https://github.com/yourusername/projetimo/wiki",
        "Source Code": "https://github.com/yourusername/projetimo",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Real Estate",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Topic :: Office/Business :: Financial",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Office/Business :: Financial :: Real Estate",
    ],
    keywords="immobilier, gestion, location, propriété, Django, Python",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.0.0",
        ],
        "production": [
            "gunicorn>=21.0.0",
            "psycopg2-binary>=2.9.0",
            "redis>=4.5.0",
            "celery>=5.3.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.png", "*.jpg", "*.gif", "*.ico"],
    },
    entry_points={
        "console_scripts": [
            "projetimo=manage:main",
        ],
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
)
