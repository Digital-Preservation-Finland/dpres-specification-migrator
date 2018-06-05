"""
Install dpres-specification-migrator
"""

import os
from setuptools import setup, find_packages


def scripts_list():
    """Return list of command line tools from package scripts"""
    scripts = []
    for modulename in os.listdir('dpres_specification_migrator/scripts'):
        if modulename == '__init__.py':
            continue
        if not modulename.endswith('.py'):
            continue
        modulename = modulename.replace('.py', '')
        scriptname = modulename.replace('_', '-')
        scripts.append('%s = dpres_specification_migrator.scripts.%s:main' % (scriptname, modulename))
    print scripts
    return scripts


def main():
        """Install dpres-specification-migrator"""
        setup(
            name='dpres-specification-migrator',
            packages=find_packages(exclude=['tests', 'tests.*']),
            version='dev',
            entry_points={'console_scripts': scripts_list()})


if __name__ == '__main__':
    main()
