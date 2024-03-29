"""
Install dpres-specification-migrator
"""

from setuptools import setup, find_packages
from version import get_version


def main():
    """Install dpres-specification-migrator"""
    setup(
        name='dpres-specification-migrator',
        packages=find_packages(exclude=['tests', 'tests.*']),
        include_package_data=True,
        version=get_version(),
        install_requires=[
            "lxml"
        ],
        entry_points={'console_scripts':
                      [('transform-mets = '
                        'dpres_specification_migrator.transform_mets:main')]})


if __name__ == '__main__':
    main()
