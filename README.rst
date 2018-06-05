Specification Migration Tools
==================

These tools are intended to be used for migrating an OAIS Information Package
according to the specifications of the Finnish National Digital
Preservation Services. The tool contains code for modifiying and updating
the information package METS document to a newer version of the finnish
national specifications, as well as modifying the contents of the information
package for the contents defined in the specifications. These tools also
support creating Dissemination Information Packages (DIP) by modifying the
METS document's RECORDSTATUS aatribute.


Installation
------------

Installation and usage require Python 2.7.
The software is tested with Python 2.7 with Centos 7.x / RHEL 7.x releases.

For running in a tested and an isolated environment, get python-virtuelenv
software::

    pip install virtualenv

Run the following to activate the virtual environment::

    virtualenv .venv
    source ./.venv/bin/activate

Install the required software with command::

    pip install -r requirements_github.txt


Scripts
-------

transform_mets
    for modifying the METS document by removing unsupported metadata,
    updating the metadata to a newer version of the specifications and 
    optionally changing the RECORDSTATUS of the document.



Usage
-----

The script produces a mets.xml file in the parametrized folder 'workspace'.

To migrate a METS document located in the tests/data/mets folder to a newer
version of the finnish national specifications use the script as follows::

    python dissemination/scripts/transform_mets.py tests/data/mets/mets_1_4.xml
    --to_version 1.6 --workspace ./workspace

The script will update the METS document so that it conforms to the
specification version 1.6.0 of the Finnsih National Digital Preservation
Services and remove unsupported metadata from the METS document. The updated
file is written into the workspace directory as 'mets_new.xml'.

Optionally the version of the specifications to migrate the METS document to
can be specified by using the '--to_version' attribute::

    python dissemination/scripts/transform_mets.py tests/data/mets/mets_1_4.xml
    --to_version 1.4 --workspace ./workspace

The argument '--to_version' accepts values from a predifined list only. Please
note that it is not possible to convert a document to an older version of the
specifications than the document's version itself.

To transform the METS into a DIP by altering the RECORDSTATUS attribute in the
metsHdr use the '--record_status' attribute::

    python dissemination/scripts/transform_mets.py tests/data/mets/mets_1_4.xml
    --record_status dissemination --workspace ./workspace

This will create a DIP METS document from the input file.


Copyright    
---------
All rights reserved to CSC - IT Center for Science Ltd.

