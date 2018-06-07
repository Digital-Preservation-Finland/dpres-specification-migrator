"""Module for migrating an information package METS document into a
newer version of the specifications for the Finnish National Digital
Preservation Services.
"""

import os
import sys
import argparse
import datetime

from uuid import uuid4

import mets
import xml_helpers.utils as h
from dpres_specification_migrator.utils import RECORD_STATUS_TYPES


NAMESPACES = {
    'mets': 'http://www.loc.gov/METS/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'fi': 'http://www.kdk.fi/standards/mets/kdk-extensions',
    'premis': 'info:lc/xmlns/premis-v2',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'dcmitype': 'http://purl.org/dc/dcmitype/',
    'addml': 'http://www.arkivverket.no/standarder/addml',
    'audiomd': 'http://www.loc.gov/audioMD/',
    'videomd': 'http://www.loc.gov/videoMD/',
    'textmd': 'info:lc/xmlns/textMD-v3',
    'textmd': 'http://www.kdk.fi/standards/textmd',
    'mix': 'http://www.loc.gov/mix/v20',
    'marc21': 'http://www.loc.gov/MARC21/slim',
    'mods': 'http://www.loc.gov/mods/v3',
    'ead': 'urn:isbn:1-931666-22-9',
    'eac': 'urn:isbn:1-931666-33-4',
    'ead3': 'http://ead3.archivists.org/schema/',
    'vra': 'http://www.vraweb.org/vracore4.htm',
    'lido': 'http://www.lido-schema.org',
    'ddicb21': 'http://www.icpsr.umich.edu/DDI',
    'ddicb25': 'ddi:codebook:2_5',
    'ddilc31': 'ddi:instance:3_1',
    'ddilc32': 'ddi:instance:3_2'
}

VERSIONS = {
    '1.4': {
        'order': 1,
        'fix_old': True,
        'supported': False,
        'KDK': True
        },
    '1.5': {
        'order': 2,
        'fix_old': False,
        'supported': True,
        'KDK': True
        },
    '1.6': {
        'order': 3,
        'fix_old': False,
        'supported': True,
        'KDK': True
        },
    '1.7': {
        'order': 4,
        'fix_old': False,
        'supported': True,
        'KDK': False
        }
    }


def main(arguments=None):
    """The main method for transform_mets."""
    args = parse_arguments(arguments)

    root = h.readfile(args.filepath).getroot()

    version = root.xpath('@*[local-name() = "CATALOG"] | '
                         '@*[local-name() = "SPECIFICATION"]')[0][:3]

    supported_versions = []
    for key, value in VERSIONS.items():
        if value['supported']:
            supported_versions.append(key)

    if args.to_version not in supported_versions:
        print >> sys.stderr, ('Error: Unable to migrate METS document '
                              'to METS catalog version %s. Supported '
                              'versions are %s.' % (
                                  args.to_version,
                                  ', '.join(supported_versions)))
        return 117

    elif VERSIONS[args.to_version]['order'] < VERSIONS[version]['order']:
        print >> sys.stderr, ('Error: Unable to migrate METS document to an '
                              'older catalog version. Current METS catalog '
                              'version is %s, while version %s was '
                              'requested.' % (
                                  version, args.to_version))
        return 117

    elif not VERSIONS[args.to_version]['KDK'] and VERSIONS[version]['KDK'] \
            and not args.contractid:
        print >> sys.stderr, ('Error: CONTRACTID required when migrating '
                              'to catalog version %s' % args.to_version)
        return 117

    if args.objid and args.record_status != 'dissemination':
        print ('Warning: the argument objid with the value "%s" was ignored. '
               'METS OBJID was not changed in the migration to a newer '
               'version of the specifications.' % args.objid)

    if VERSIONS[version]['fix_old']:
        root = fix_1_4_mets(root)

    (migrated_mets, objid) = migrate_mets(
        root=root, cur_catalog=version,
        to_catalog=args.to_version, contract=args.contractid)

    if args.record_status == 'dissemination':
        migrated_mets, objid = transform_to_dip(
            migrated_mets, cur_catalog=version,
            to_catalog=args.to_version, objid=args.objid)

    mets_str = serialize_mets(migrated_mets)

    filename = args.filename
    with open(os.path.join(args.workspace, filename), 'w+') as outfile:
        outfile.write(mets_str)
        print 'Wrote METS file as %s with OBJID: %s' % (outfile.name, objid)

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
    - adds a new div as parent div if structmap has several child divs
    - sets METSRIGHTS as OTHERMDTYPE
    """
    mdtypeversions = {'PREMIS:OBJECT': '2.3', 'PREMIS:RIGHTS': '2.3',
                      'PREMIS:EVENT': '2.3', 'PREMIS:AGENT': '2.3',
                      'TEXTMD': '3.01', 'DC': '1.1', 'NISOIMG': '2.0',
                      'AudioMD': '2.0', 'VideoMD': '2.0', 'EAD': '2002',
                      'MODS': '3.6', 'MARC': 'marcxml=1.2; marc=marc21',
                      'DDI': '2.5.1', 'EAC-CPF': '2010', 'VRACore': '4.0',
                      'LIDO': '1.0', 'METSRIGHTS': 'n/a'}

    for elem in root.xpath(".//mets:mdWrap", namespaces=NAMESPACES):
        mdtype = elem.get('MDTYPE')
        if mdtype == 'OTHER':
            mdtype = elem.get('OTHERMDTYPE')
        version = mdtypeversions[mdtype]
        elem.set('MDTYPEVERSION', version)

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

    for textfile in root.xpath('./mets:amdSec/mets:techMD',
                               namespaces=NAMESPACES):
        if (textfile.get('ID') in textfiles.keys() and
                textfile.xpath("./mets:mdWrap[@MDTYPE='PREMIS:OBJECT']",
                               namespaces=NAMESPACES)):
            file_id = textfile.get('ID')
            charset = textfiles[file_id]
            formatname = textfile.xpath('.//premis:formatName',
                                        namespaces=NAMESPACES)[0]
            new_formatname = formatname.text + '; charset=' + charset
            formatname.text = new_formatname

    for premis_textmd in root.xpath(
            './mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/'
            'premis:objectCharacteristics/'
            'premis:objectCharacteristicsExtension/textmd:textMD',
            namespaces=NAMESPACES):
        techmd_id = premis_textmd.xpath('./ancestor::mets:techMD',
                                        namespaces=NAMESPACES)[0].get('ID')
        charset = premis_textmd.xpath(".//*[local-name() = 'charset']")[0].text
        format_name = premis_textmd.xpath(
            './ancestor::premis:objectCharacteristics//premis:formatName',
            namespaces=NAMESPACES)[0]
        if ';' not in format_name.text:
            format_name.text = format_name.text + '; charset=' + charset

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
            mdwrap.set('MDTYPEVERSION', 'n/a')

    return root


def migrate_mets(root, to_catalog, cur_catalog, contract=None):
    """Migrates the METS document from the METS data in XML.

    1) Collects all attributes from the METS root element
    1) Sets the correct profile for the METS document
    2) Sets the correct CATALOG or SPECIFICATION
    3) Adds CONTRACTID and migrates old KDK specific profile data if
       to_catalog specifies a newer non-KDK profile
    4) Writes a new mets root element for the METS document
    5) Appends all child elements from the supplied root element
       to the new METS
    6) Modifies the LASTMODDATE in the metsHdr
    7) Writes the updated attribute set to the new root

    :root: the mets root as xml
    :to_catalog: the intended catalog version of the METS document
    :cur_catalog: the current catalog version of the METS document
    :contract: the CONTRACTID of the METS document

    :returns: a METS root as xml
    """
    fi_ns = get_fi_ns(cur_catalog)

    root_attribs = root.attrib

    if root_attribs['PROFILE'] == 'http://www.kdk.fi/kdk-mets-profile' \
            and not VERSIONS[to_catalog]['KDK']:
        root_attribs['PROFILE'] = 'http://digitalpreservation.fi/' \
                  'mets-profiles/cultural-heritage'

    if '{%s}CATALOG' % fi_ns in root_attribs:
        root_attribs['{%s}CATALOG' % fi_ns] = to_catalog + '.0'
    else:
        root_attribs['{%s}SPECIFICATION' % fi_ns] = to_catalog + '.0'

    contractid = ''
    if not VERSIONS[to_catalog]['KDK']:
        if '{%s}CONTRACTID' % fi_ns in root.attrib:
            contractid = root.get('{%s}CONTRACTID' % fi_ns)
            if contract:
                print ('Warning: the argument contract with the value "%s" '
                       'was ignored. The existing @CONTRACTID of the METS '
                       'file, %s, was not overwritten.') % (contract,
                                                            contractid)
        else:
            contractid = contract
        root_attribs['{%s}CONTRACTID' % fi_ns] = contractid

        for elem in root.xpath(
                './mets:amdSec/mets:digiprovMD/'
                'mets:mdRef[@OTHERMDTYPE="KDKPreservationPlan"]',
                namespaces=NAMESPACES):
            elem.set('OTHERMDTYPE', 'FiPreservationPlan')
    elif contract:
        print ('Warning: the argument contract %s was ignored. The requested '
               'catalog version %s does not support @CONTRACTID.') % (
                   contract, to_catalog)

    root.xpath('./mets:metsHdr', namespaces=NAMESPACES)[0].set(
        'LASTMODDATE', datetime.datetime.utcnow().replace(
            microsecond=0).isoformat() + 'Z')

    elems = []
    for elem in root.xpath('./*'):
        elems.append(elem)

    if not VERSIONS[cur_catalog]['KDK']:
        NAMESPACES['fi'] = ('http://digitalpreservation.fi/schemas'
                            '/mets/fi-extensions')
    else:
        NAMESPACES['fi'] = 'http://www.kdk.fi/standards/mets/kdk-extensions'

    new_mets = mets.mets(profile=root_attribs['PROFILE'], child_elements=elems,
                         namespaces=NAMESPACES)

    for attrib in root_attribs:
        new_mets.set(attrib, root_attribs[attrib])

    return new_mets, root_attribs['OBJID']


def remove_attributes(root):
    """Removes unsupported attributes from METS file."""
    del_attribs = {'.': ['ID', 'TYPE',
                         ('{http://www.kdk.fi/standards/mets/'
                          'kdk-extensions}SPECIFICATION')],
                   'mets:metsHdr': ['ID', 'ADMID'],
                   'mets:metsHdr/mets:agent': ['ID'],
                   'mets:dmdSec': ['ADMID', 'STATUS'],
                   'mets:amdSec': ['ID'],
                   'mets:amdSec/mets:techMD': ['ADMID', 'STATUS'],
                   'mets:amdSec/mets:rightsMD': ['ADMID', 'STATUS'],
                   'mets:amdSec/mets:sourceMD': ['ADMID', 'STATUS'],
                   'mets:amdSec/mets:digiprovMD': ['ADMID', 'STATUS'],
                   'mets:dmdSec/mets:mdWrap': [
                       'ID', 'MIMETYPE', 'SIZE', 'CREATED', 'CHECKSUM',
                       'CHECKSUMTYPE', 'LABEL'],
                   'mets:amdSec/*/mets:mdWrap': [
                       'ID', 'MIMETYPE', 'SIZE', 'CREATED', 'CHECKSUM',
                       'CHECKSUMTYPE', 'LABEL'],
                   'mets:amdSec/mets:digiprovMD/mets:mdRef': [
                       'ID', 'XPTR', 'MIMETYPE', 'SIZE', 'CREATED', 'CHECKSUM',
                       'CHECKSUMTYPE', 'LABEL',
                       '{http://www.w3.org/1999/xlink}role',
                       '{http://www.w3.org/1999/xlink}arcrole',
                       '{http://www.w3.org/1999/xlink}title',
                       '{http://www.w3.org/1999/xlink}show',
                       '{http://www.w3.org/1999/xlink}actuate'],
                   'mets:fileSec': ['ID'],
                   'mets:fileSec/mets:fileGrp': ['ID', 'ADMID', 'VERSDATE'],
                   'mets:fileSec/mets:fileGrp/mets:file': [
                       'MIMETYPE', 'SIZE', 'CREATED', 'CHECKSUM',
                       'CHECKSUMTYPE', 'SEQ', 'DMDID', 'BEGIN', 'END',
                       'BETYPE'],
                   'mets:fileSec/mets:fileGrp/mets:file/mets:FLocat': [
                       'ID', '{http://www.w3.org/1999/xlink}role',
                       '{http://www.w3.org/1999/xlink}arcrole',
                       '{http://www.w3.org/1999/xlink}title',
                       '{http://www.w3.org/1999/xlink}show',
                       '{http://www.w3.org/1999/xlink}actuate'],
                   'mets:structMap//mets:div': [
                       '{http://www.w3.org/1999/xlink}label'],
                   'mets:structMap//mets:div/mets:fptr': ['ID', 'CONTENTIDS'],
                   'mets:structMap//mets:div/mets:mptr': [
                       'ID', 'CONTENTIDS',
                       '{http://www.w3.org/1999/xlink}role',
                       '{http://www.w3.org/1999/xlink}arcrole',
                       '{http://www.w3.org/1999/xlink}title',
                       '{http://www.w3.org/1999/xlink}show',
                       '{http://www.w3.org/1999/xlink}actuate']}

    for key in del_attribs:
        for elem in root.xpath('./%s' % key, namespaces=NAMESPACES):
            for value in del_attribs[key]:
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


def serialize_mets(root):
    """Serializes the METS XML data to string. Then replaces some
    namespace declarations, since that can't be done in lxml.

    :returns: METS data as string
    """

    mets_str = h.serialize(root)

    if root.xpath("//mets:mdWrap[@MDTYPE='TEXTMD']",
                  namespaces=NAMESPACES):
        mets_str = mets_str.replace(
            'xmlns:textmd="http://www.kdk.fi/standards/textmd"',
            'xmlns:textmd="info:lc/xmlns/textMD-v3"')

    version = root.xpath('@*[local-name() = "CATALOG"] | '
                         '@*[local-name() = "SPECIFICATION"]')[0]

    if version == '1.7.0':
        mets_str = mets_str.replace(
            'xmlns:fi="http://www.kdk.fi/standards/mets/kdk-extensions"',
            'xmlns:fi="http://digitalpreservation.fi/'
            'schemas/mets/fi-extensions"')

    return mets_str


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
        objid = str(uuid4())

    root = remove_attributes(root)

    root = set_dip_metshdr(root)

    root.set('{%s}CATALOG' % fi_ns, to_catalog + '.0')
    if '{%s}SPECIFICATION' % fi_ns in root.attrib:
        del root.attrib['{%s}SPECIFICATION' % fi_ns]
    root.set('OBJID', objid)

    return root, objid


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
