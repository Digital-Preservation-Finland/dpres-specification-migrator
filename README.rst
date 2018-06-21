Specification Migration Tools
=============================

This tool is intended to be used for migrating an OAIS Information Package
METS document according to the specifications of the Finnish National Digital
Preservation Services (http://digitalpreservation.fi/specifications). The tool
contains code for modifying and updating the information package METS document
to a newer version of the national specifications. The tool also supports
creating Dissemination Information Packages (DIP) by modifying the METS
document's RECORDSTATUS attribute and producing a DIP METS according to the
national specifications.


Installation
------------

Installation and usage require Python 2.7.
The software is tested with Python 2.7 with Centos 7.x / RHEL 7.x releases.

For running in a tested and isolated environment, get python-virtuelenv
software::

    pip install virtualenv

Run the following to activate the virtual environment::

    virtualenv .venv
    source ./.venv/bin/activate

Install the required software with the command::

    pip install -r requirements_github.txt


Scripts
-------

transform_mets
    for modifying the METS document by updating the metadata to a newer
    version of the specifications and optionally creating a Dissemination
    Information Package from the METS document.


Usage
-----

Run the script transform_mets as follows::

    python dpres_specification_migrator/transform_mets.py [input_file]
    [options]

The script can take the following options:

* ``--output_filename``: specify the name of the created METS document
* ``--to_version``: specify the version of the specifications to migrate to
* ``--contractid``: the value of the contract ID (mandatory when migrating to
  version 1.7.0 of the specifications from an older version)
* ``--record_status``: set the RECORDSTATUS of the document, the value
  'dissemination' will create a DIP METS document
* ``--objid``: specify the OBJID when migrating to a DIP METS document
* ``--workspace``: the workspace directory

The script produces a mets.xml file in the parametrized folder 'workspace'
unless the '--output_filename' argument is used to specify the name of the
file.

To migrate a METS document located in the tests/data/mets folder to a newer
version of the Finnish national specifications use the script as follows::

    python dpres_specification_migrator/transform_mets.py
    tests/data/mets/mets_1_4.xml --workspace ./workspace
    --contractid <contract id>

The script will update the METS document so that it conforms to the version
1.7.0 of the specifications of the Finnish National Digital Preservation
Services. The updated file is written into the workspace directory.
The 'contractid' argument is mandatory when migrating to version '1.7.0'.

Optionally the version of the specifications to migrate the METS document to
can be specified by using the '--to_version' argument::

    python dpres_specification_migrator/transform_mets.py
    tests/data/mets/mets_1_4.xml --to_version 1.6 --workspace ./workspace

The argument '--to_version' accepts values from a predifined list only. Please
note that it is not possible to convert a document to an older version of the
specifications than the document's version itself.

To transform the METS into a DIP METS use the '--record_status' argument::

    python dpres_specification_migrator/transform_mets.py
    tests/data/mets/mets_1_4.xml --record_status dissemination --workspace
    ./workspace --contractid <contract ID> --objid <objid>

This will create a DIP METS document from the input file as well as migrating
it to a newer version if possible.

When creating a DIP METS it is possible to specify the METS OBJID of the DIP
METS with the '--objid' argument. If the OBJID isn't specified, the script
will generate a random unique ID for the DIP METS. Note that this argument is
ignored if the '--record_status' is not 'dissemination' (the OBJID of the METS
document is not changed when migrating to a newer version of the specifications
without migrating to a DIP).


Copyright    
---------
All rights reserved to CSC - IT Center for Science Ltd.

