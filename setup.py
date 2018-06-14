"""
Install dpres-specification-migrator
"""

from setuptools import setup, find_packages


def main():
    """Install dpres-specification-migrator"""
    setup(
        name='dpres-specification-migrator',
        packages=find_packages(exclude=['tests', 'tests.*']),
        version='0.1',
        entry_points={'console_scripts':
                      [('transform-mets = '
                        'dpres_specification_migrator.transform_mets:main')]})


if __name__ == '__main__':
    main()
