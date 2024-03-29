"""Configure py.test default values and functionality"""

import os
import sys
import tempfile
import shutil

import pytest

# Prefer modules from source directory rather than from site-python
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                '..'))


@pytest.fixture(scope="function")
def testpath(request):
    """Creates temporary directory and clean up after testing.

    :request: Pytest request fixture
    :returns: Path to temporary directory

    """
    temp_path = tempfile.mkdtemp(prefix="tests.testpath.")

    def fin():
        """remove temporary path"""
        shutil.rmtree(temp_path)

    request.addfinalizer(fin)
    return temp_path
