from distutils.core import setup
from setuptools import find_packages

setup(
    name="vivaldi_a",
    version="0.1.0",
    description="Visualization Validation and Diagnostics for Atmospheric chemistry",
    author="Rebecca Buchholz;Duseong Jo",
    author_email="cdswk@ucar.edu",
    url='https://ncar.github.io/CAM-chem/',
    packages=find_packages(),
    keywords=['atmospheric chemistry', 'cesm', 'cam-chem', 'air quality', 'emission'],
    install_requires=[
        'numpy',
        'matplotlib',
        'xarray',
        'cartopy'
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Atmospheric Science"
    ]
)
