"""Module for migrating an information package METS document into a
newer version of the specifications for the Finnish National Digital
Preservation Services. Also possible to change the RECORDSTATUS of the
METS document to create a dissemination information package.
"""
from __future__ import print_function, unicode_literals

import argparse
import copy
import datetime
import io
import os
import sys
from uuid import uuid4

import six

import mets
import xml_helpers.utils
from dpres_specification_migrator.dicts import (ATTRIBS_TO_DELETE,
                                                MDTYPEVERSIONS, NAMESPACES,
                                                RECORD_STATUS_TYPES, VERSIONS)


def main(arguments=None):
    """The main method for transform_mets."""
    args = parse_arguments(arguments)

    root = xml_helpers.utils.readfile(args.filepath).getroot()

    full_version = root.xpath('@*[local-name() = "CATALOG"] | '
                              '@*[local-name() = "SPECIFICATION"]')[0]
    version = full_version[:3]

    supported_versions = []
    for key, value in VERSIONS.items():
        if value['supported']:
            supported_versions.append(key)

    if args.to_version not in supported_versions:
        print(
            'Error: Unable to migrate METS document '
            'to METS catalog version %s. Supported '
            'versions are %s.' % (
                args.to_version,
                ', '.join(supported_versions)
            ),
            file=sys.stderr
        )
        return 117

    elif VERSIONS[args.to_version]['order'] < VERSIONS[version]['order']:
        print(
            'Error: Unable to migrate METS document to an '
            'older catalog version. Current METS catalog '
            'version is %s, while version %s was '
            'requested.' % (version, args.to_version),
            file=sys.stderr
        )
        return 117

    elif not VERSIONS[args.to_version]['KDK'] and VERSIONS[version]['KDK'] \
            and not args.contractid:
        print(
            'Error: CONTRACTID required when migrating '
            'to catalog version %s' % args.to_version,
            file=sys.stderr
        )
        return 117

    if args.objid and args.record_status != 'dissemination':
        print('Warning: the argument objid with the value "%s" was ignored. '
              'METS OBJID was not changed in the migration to a newer '
              'version of the specifications.' % args.objid)

    NAMESPACES['textmd'] = 'info:lc/xmlns/textMD-v3'

    if VERSIONS[version]['fix_old']:
        root = fix_1_4_mets(root)

    (migrated_mets, objid) = migrate_mets(
        root=root, full_cur_catalog=full_version,
        to_catalog=args.to_version, contract=args.contractid)



    if args.record_status == 'dissemination':
        migrated_mets, objid = transform_to_dip(
            migrated_mets, cur_catalog=version,
            to_catalog=args.to_version, objid=args.objid)

    mets_b = serialize_mets(migrated_mets)

    filename = args.filename
    with io.open(os.path.join(args.workspace, filename), 'wb+') as outfile:
        outfile.write(mets_b)
        print('Wrote METS file as %s with OBJID: %s' % (outfile.name, objid))

    return 0


def parse_arguments(arguments):
    """Create arguments parser and return parsed command line arguments."""
    parser = argparse.ArgumentParser(description='Transform METS')
    parser.add_argument('filepath', type=str, help='Path to METS file')
    parser.add_argument('--output_filename', dest='filename',
                        type=str, default='mets.xml',
                        help='The file name of the transformed METS document')
    parser.add_argument('--objid', dest='objid', type=str, help='New mets '
                        'OBJID for transformed mets file')
    parser.add_argument('--to_version', dest='to_version', type=str,
                        default='1.7', help='Catalog version of METS output '
                        'file')
    parser.add_argument('--contractid', dest='contractid', type=str,
                        help='ContractID of METS file')
    parser.add_argument('--record_status', dest='record_status',
                        choices=RECORD_STATUS_TYPES, type=str,
                        help='list of record status types:%s' %
                        RECORD_STATUS_TYPES)
    parser.add_argument('--workspace', dest='workspace', type=str,
                        default='./workspace', help='Workspace directory')

    return parser.parse_args(arguments)


def fix_1_4_mets(root):
    """Migrates from catalog version 1.4 or 1.4.1 to newer by writing
    the following changes into the mets file:
    - adds the @MDTYPEVERSION attribute to all mets:mdWrap elements
    - writes charset from textMD to premis:formatName for text files
    - moves MIX metadata blocks from  the
      premis:objectCharacteristicsExtension metadata to an own techMD
      metadata block
    - adds a new div as parent div if structmap has several child divs
    - sets METSRIGHTS as OTHERMDTYPE
    """
    NAMESPACES['textmd'] = 'http://www.kdk.fi/standards/textmd'

    for elem in root.xpath("./mets:amdSec/*/mets:mdWrap | ./mets:dmdSec/"
                           "mets:mdWrap", namespaces=NAMESPACES):
        mdtype = elem.get('MDTYPE')
        if mdtype == 'OTHER':
            mdtype = elem.get('OTHERMDTYPE')
        version = MDTYPEVERSIONS[mdtype]
        # MODS version has to comply with version given in MODS metadata
        # If missing, use the default value already given.
        if mdtype == "MODS":
            mods_version = elem.xpath("./mets:xmlData/mods:mods/@version",
                                      namespaces=NAMESPACES)
            if mods_version and mods_version[0].strip():
                version = mods_version[0].strip()
        elem.set('MDTYPEVERSION', version)

    root = set_charset_from_textmd(root)

    for premis_mix in root.xpath(
            './mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/'
            'premis:objectCharacteristics/'
            'premis:objectCharacteristicsExtension/mix:mix',
            namespaces=NAMESPACES):

        root = move_mix(root, premis_mix)

    list_amdsec = []
    mets_amdsec = root.xpath('./mets:amdSec', namespaces=NAMESPACES)[0]
    for elem in mets_amdsec:
        list_amdsec.append(copy.deepcopy(elem))
        mets_amdsec.remove(elem)

    list_amdsec.sort(key=mets.order)

    for elem in list_amdsec:
        mets_amdsec.append(elem)

    structmap = root.xpath('./mets:structMap', namespaces=NAMESPACES)[0]
    if len(root.xpath('./mets:structMap/mets:div',
                      namespaces=NAMESPACES)) > 1:
        div_elements = []

        for div in structmap:
            div_elements.append(div)
            div.getparent().remove(div)

        div1 = mets.div(type_attr='WRAPPER', div_elements=div_elements)
        structmap.append(div1)

    for rightsmd in root.xpath('./mets:amdSec/mets:rightsMD',
                               namespaces=NAMESPACES):
        mdwrap = rightsmd.xpath("./mets:mdWrap", namespaces=NAMESPACES)[0]
        if mdwrap.get('MDTYPE') == 'METSRIGHTS':
            mdwrap.set('MDTYPE', 'OTHER')
            mdwrap.set('OTHERMDTYPE', 'METSRIGHTS')
            mdwrap.set('MDTYPEVERSION', MDTYPEVERSIONS['METSRIGHTS'])

    return root


def set_charset_from_textmd(root):
    """Appends the charset from textMD metadata to the
    premis:formatName element if it is missing.
    The function will search for textMD metadata both
    as a separate techMD metadata block within mets:amdSec
    and within the premis:objectCharacteristicsExtension
    metadata for the techMD in question."""
    textmds = {}
    for techmd in root.xpath('./mets:amdSec/mets:techMD',
                             namespaces=NAMESPACES):
        if techmd.xpath("./mets:mdWrap[@MDTYPE='TEXTMD']",
                        namespaces=NAMESPACES):
            charset = techmd.xpath(".//*[local-name() = 'charset']")[0].text
            techmd_id = techmd.get('ID')
            textmds[techmd_id] = charset

    textfiles = {}
    for mets_file in root.xpath('./mets:fileSec//mets:file',
                                namespaces=NAMESPACES):
        for key in textmds:
            if key in mets_file.get('ADMID'):
                charset = textmds[key]
                for admid in mets_file.get('ADMID').split(' '):
                    textfiles[admid] = charset

    count = 0
    for textfile in root.xpath('./mets:amdSec/mets:techMD',
                               namespaces=NAMESPACES):
        if (textfile.get('ID') in textfiles.keys() and
                textfile.xpath("./mets:mdWrap[@MDTYPE='PREMIS:OBJECT']",
                               namespaces=NAMESPACES)):
            count += 1
            file_id = textfile.get('ID')
            charset = textfiles[file_id]
            formatname = textfile.xpath('.//premis:formatName',
                                        namespaces=NAMESPACES)[0]
            if '; charset' not in formatname.text:
                formatname.text = formatname.text + '; charset=' + charset

    for premis_textmd in root.xpath(
            './mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/'
            'premis:objectCharacteristics/'
            'premis:objectCharacteristicsExtension/textmd:textMD',
            namespaces=NAMESPACES):
        charset = premis_textmd.xpath(".//*[local-name() = 'charset']")[0].text
        format_name = premis_textmd.xpath(
            './ancestor::premis:objectCharacteristics//premis:formatName',
            namespaces=NAMESPACES)[0]
        if '; charset' not in format_name.text:
            format_name.text = format_name.text + '; charset=' + charset

    return root


def move_mix(root, premis_mix):
    """Moves current MIX metadata block from
    premis:objectCharacteristicsExtension to an own mets:techMD
    block and appends the created ID of the the new techMD block
    to the file's AMDID attribute in the mets:fileSec.

    :root: the METS data as XML
    :premis_mix: the MIX metadata within premis

    :returns: the METS data root
    """

    mix_id = '_' + six.text_type(uuid4())
    techmd_id = premis_mix.xpath('./ancestor::mets:techMD',
                                 namespaces=NAMESPACES)[0].get('ID')
    amdsec = root.xpath('.//mets:amdSec', namespaces=NAMESPACES)[0]

    xml_data = mets.xmldata(child_elements=[copy.deepcopy(premis_mix)])
    md_wrap = mets.mdwrap('NISOIMG', '2.0', child_elements=[xml_data])
    techmd = mets.techmd(mix_id, child_elements=[md_wrap])
    amdsec.append(techmd)

    for mets_file in root.xpath('./mets:fileSec//mets:file',
                                namespaces=NAMESPACES):
        if techmd_id in mets_file.get('ADMID'):
            mets_file.set('ADMID', mets_file.get('ADMID') + ' ' + mix_id)

    premis_extension = premis_mix.xpath(
        './ancestor::premis:objectCharacteristicsExtension',
        namespaces=NAMESPACES)[0]
    premis_extension.getparent().remove(premis_extension)

    return root


def migrate_mets(root, to_catalog, full_cur_catalog, contract=None):
    """Migrates the METS document from the METS data in XML.

    1) Collects all attributes from the METS root element
    2) Sets the correct profile for the METS document
    3) Sets the correct CATALOG or SPECIFICATION
    4) Updates the schemaLocation attribute
    5) Adds CONTRACTID and migrates old KDK specific profile data if
       to_catalog specifies a newer non-KDK profile
    6) Writes a new mets root element for the METS document
    7) Appends all child elements from the supplied root element
       to the new METS
    8) Modifies the LASTMODDATE in the metsHdr
    9) Updates no-file-format-validation key, if needed
    10) Writes the updated attribute set to the new root

    :root: the mets root as xml
    :to_catalog: the intended catalog version of the METS document
    :full_cur_catalog: the current full catalog version of the METS document
    :contract: the CONTRACTID of the METS document

    :returns: a METS root as xml
    """
    fi_ns = get_fi_ns(full_cur_catalog[:3])

    root_attribs = root.attrib

    if root_attribs['PROFILE'] == 'http://www.kdk.fi/kdk-mets-profile' \
            and not VERSIONS[to_catalog]['KDK']:
        root_attribs['PROFILE'] = 'http://digitalpreservation.fi/' \
                  'mets-profiles/cultural-heritage'

    if '{%s}CATALOG' % fi_ns in root_attribs:
        root_attribs['{%s}CATALOG' % fi_ns] = \
            VERSIONS[to_catalog]['catalog_version']
    if '{%s}SPECIFICATION' % fi_ns in root_attribs:
        root_attribs['{%s}SPECIFICATION' % fi_ns] = \
            VERSIONS[to_catalog]['newest_specification']

    root_attribs[
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = (
            'http://www.loc.gov/METS/ '
            'http://digitalpreservation.fi/schemas/mets/mets.xsd')

    contractid = ''
    if not VERSIONS[to_catalog]['KDK']:
        if '{%s}CONTRACTID' % fi_ns in root.attrib:
            contractid = root.get('{%s}CONTRACTID' % fi_ns)
            if contract:
                print(
                    'Warning: the argument contract with the value "%s" '
                    'was ignored. The existing @CONTRACTID of the METS '
                    'file, %s, was not overwritten.' % (contract,
                                                        contractid)
                )
        else:
            contractid = contract
        root_attribs['{%s}CONTRACTID' % fi_ns] = contractid

        for elem in root.xpath(
                './mets:amdSec/mets:digiprovMD/'
                'mets:mdRef[@OTHERMDTYPE="KDKPreservationPlan"]',
                namespaces=NAMESPACES):
            elem.set('OTHERMDTYPE', 'FiPreservationPlan')

    elif contract:
        print(
            'Warning: the argument contract %s was ignored. The requested '
            'catalog version %s does not support @CONTRACTID.' % (
                contract, to_catalog
            )
        )

    root.xpath('./mets:metsHdr', namespaces=NAMESPACES)[0].set(
        'LASTMODDATE', datetime.datetime.utcnow().replace(
            microsecond=0).isoformat() + 'Z')

    if not VERSIONS[to_catalog]['KDK']:
        for elem in root.xpath('./mets:dmdSec/mets:mdWrap[./@MDTYPE="MARC"]',
                               namespaces=NAMESPACES):
            attr = elem.attrib
            if 'marc=finmarc' in attr['MDTYPEVERSION']:
                attr['MDTYPE'] = 'OTHER'
                attr['OTHERMDTYPE'] = 'MARC'

    if VERSIONS[full_cur_catalog[:3]]['KDK'] or full_cur_catalog in [
            '1.7.0', '1.7.1', '1.7.2'] and not VERSIONS[to_catalog]['KDK']:
        for elem in root.xpath(
                './mets:fileSec/mets:fileGrp/mets:file[@USE='
                '"no-file-format-validation"]', namespaces=NAMESPACES):
            attr = elem.attrib
            if attr['USE'] == 'no-file-format-validation':
                attr['USE'] = 'fi-preservation-no-file-format-validation'

    elems = []
    for elem in root.xpath('./*'):
        elems.append(elem)

    if not VERSIONS[full_cur_catalog[:3]]['KDK']:
        NAMESPACES['fi'] = ('http://digitalpreservation.fi/schemas'
                            '/mets/fi-extensions')
    else:
        NAMESPACES['fi'] = 'http://www.kdk.fi/standards/mets/kdk-extensions'

    new_mets = mets.mets(profile=root_attribs['PROFILE'], child_elements=elems,
                         namespaces=NAMESPACES)

    for attrib in root_attribs:
        new_mets.set(attrib, root_attribs[attrib])

    return new_mets, root_attribs['OBJID']


def serialize_mets(root):
    """Serializes the METS XML data to byte string. Then replaces some
    namespace declarations, since that can't be done in lxml.

    :returns: METS data as byte string
    """

    mets_b = xml_helpers.utils.encode_utf8(xml_helpers.utils.serialize(root))

    mets_b = mets_b.replace(
        b'xmlns:textmd="http://www.kdk.fi/standards/textmd"',
        b'xmlns:textmd="info:lc/xmlns/textMD-v3"')

    version = root.xpath('@*[local-name() = "CATALOG"] | '
                         '@*[local-name() = "SPECIFICATION"]')[0]

    if version in ['1.7.0', '1.7.1', '1.7.2', '1.7.3']:
        mets_b = mets_b.replace(
            b'xmlns:fi="http://www.kdk.fi/standards/mets/kdk-extensions"',
            b'xmlns:fi="http://digitalpreservation.fi/'
            b'schemas/mets/fi-extensions"')

    return mets_b


def get_fi_ns(catalog):
    """Returns the namespace for the fi: extension. The value depends
    on catalog version of the METS document.
    """
    fi_ns = 'http://digitalpreservation.fi/schemas/mets/fi-extensions'

    if catalog in VERSIONS:
        if VERSIONS[catalog]['KDK']:
            fi_ns = 'http://www.kdk.fi/standards/mets/kdk-extensions'

    return fi_ns


def transform_to_dip(root, cur_catalog, to_catalog, objid=None):
    """
    1) Sets an @OBJID for the METS document
    2) Removes unsupported attributes from the XML data
    3) Updates / writes a new metsHdr block
    4) Sets the CATALOG attribute (because SPECIFICATION is removed)
    """
    fi_ns = get_fi_ns(cur_catalog)

    if not objid:
        objid = six.text_type(uuid4())

    root = remove_attributes(root)

    root = set_dip_metshdr(root)

    root.set('{%s}CATALOG' % fi_ns, VERSIONS[to_catalog]['catalog_version'])
    if '{%s}SPECIFICATION' % fi_ns in root.attrib:
        del root.attrib['{%s}SPECIFICATION' % fi_ns]
    root.set('OBJID', objid)

    return root, objid


def remove_attributes(root):
    """Removes unsupported attributes from METS file."""
    for key in ATTRIBS_TO_DELETE:
        for elem in root.xpath('./%s' % key, namespaces=NAMESPACES):
            for value in ATTRIBS_TO_DELETE[key]:
                if value in elem.attrib:
                    del elem.attrib[value]

    return root


def set_dip_metshdr(root):
    """Sets the new mets metsHdr. Changes the CREATEDATE attribute and
    optionally the RECORDSTATUS attribute. Sets the agent responsible for
    the creation of the transformed mets file. Removes other attributes
    for the metsHdr element.
    """
    for hdr in root.xpath('./mets:metsHdr', namespaces=NAMESPACES):
        for docid in hdr.xpath('./mets:metsDocumentID', namespaces=NAMESPACES):
            hdr.remove(docid)
        for agent in hdr.xpath('./mets:agent', namespaces=NAMESPACES):
            hdr.remove(agent)
        agent = mets.agent('CSC - IT Center for Science Ltd.')
        hdr.append(agent)

        hdr.set(
            'CREATEDATE',
            datetime.datetime.utcnow().replace(
                microsecond=0).isoformat() + 'Z')
        hdr.set('RECORDSTATUS', 'dissemination')
        if 'LASTMODDATE' in hdr.attrib:
            del hdr.attrib['LASTMODDATE']
    return root


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
