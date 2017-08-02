
import os
from setuptools import setup

version_file = 'VERSION'
version = open(version_file).read().strip()

readme_file = 'README'
desc = open(readme_file).read().strip()

changes_file = 'CHANGES'
changes = open(changes_file).read().strip()
long_description = desc + '\n\nChanges:\n========\n\n' + changes 

setup(     
    name = "cmorlight",
    version = version,
    author = "Hans Ramthun",
    author_email = "ramthun@dkrz.de",
    description = ("CMOR rewriting of RCM preprocessed output"),
    license = "BSD",
    keywords = "CMOR for RCM output",
    packages=['cmorlight'],
    long_description=long_description,
    install_requires=[
        'netCDF4',
        'numpy>=1.7.0',
# not used
#       'xray',
#       'cdo>=1.7.2',
    ],
    entry_points = {
        'console_scripts': [
        'cmorlight=cmorlight:main',
    ]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],     
)

