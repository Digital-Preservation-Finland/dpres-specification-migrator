ROOT = /
PREFIX = /usr

PYTHON ?= python3

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Use Python setuptools
	${PYTHON} setup.py build ; \
	    ${PYTHON} ./setup.py install \
	    -O1 --prefix="${PREFIX}" --root="${ROOT}" --record=INSTALLED_FILES

test:
	${PYTHON} -m pytest -svvvv \
	    --junitprefix=dpres-specification-migrator --junitxml=junit.xml \
	    tests

coverage:
	${PYTHON} -m pytest tests \
	    --cov=dpres-specification-migrator --cov-report=html

	coverage report -m
	coverage html
	coverage xml

clean: clean-rpm
	find . -iname '*.pyc' -type f -delete
	find . -iname '__pycache__' -exec rm -rf '{}' \; | true

clean-rpm:
	rm -rf rpmbuild

rpm: clean-rpm
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel7
	build-rpm.sh
