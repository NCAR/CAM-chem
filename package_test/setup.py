from distutils.core import setup

setup(
    name="cam_chem_python_package",
    version="1.0.0",
    description="Test for CAM-chem python collection package",
    author="Rebecca Buchholz;Duseong Jo",
    author_email="buchholz@ucar.edu;cdswk@ucar.edu",
    packages=["cam_chem_python_package"],
    install_requires=[
        'numpy',
        'matplotlib',
        'xarray',
        'cartopy'
    ]
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Atmospheric Chemistry"
    ]
)
