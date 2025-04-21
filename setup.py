"""
Script to setup the cli tool onto the host machine.
refernce: https://pythonhosted.org/an_example_pypi_project/setuptools.html 

To setup, navigate to the forensicx directory and run 
$ pip install -e .
"""
from setuptools import setup, find_packages

VERSION = "1.0"

try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except:
    long_description = "ForensicX - A forensic tool for FUSE-based file systems"

setup(
    name="forensicx",
    version=VERSION,
    author="Akhil Harikumar, Inzamam Sayyed, Shrawani Pagar",
    author_email="aharikum@andrew.cmu.edu",
    description="A forensic tool for FUSE-based file systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aharikum/forensicx",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "forensicx=forensicx.cli:main",
        ],
    },
)