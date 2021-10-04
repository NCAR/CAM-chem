from distutils.core import setup
from setuptools import find_packages

with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="vivaldi_a",
    version="0.2.6",
    description="Visualization Validation and Diagnostics for Atmospheric chemistry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rebecca Buchholz;Duseong Jo",
    author_email="cdswk@ucar.edu",
    url='https://ncar.github.io/CAM-chem/',
    packages=find_packages(),
    keywords=['atmospheric chemistry', 'cesm', 'cam-chem', 'air quality', 'emission'],
    install_requires=[
        'numpy',
        'matplotlib',
        'xarray',
        'cartopy',
        'cftime',
        'ESMPy>=8.1.0',
        'netCDF4' ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Utilities"
    ]
)
