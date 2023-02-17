"""Global variables concerning the METS metadata and migration options."""
from __future__ import unicode_literals


RECORD_STATUS_TYPES = [
    'submission',
    'update',
    'dissemination'
]


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
        'KDK': True,
        'catalog_version': '1.4.0',
        'newest_specification': '1.4.0'
    },
    '1.5': {
        'order': 2,
        'fix_old': False,
        'supported': True,
        'KDK': True,
        'catalog_version': '1.5.0',
        'newest_specification': '1.5.0'
    },
    '1.6': {
        'order': 3,
        'fix_old': False,
        'supported': True,
        'KDK': True,
        'catalog_version': '1.6.0',
        'newest_specification': '1.6.1'
    },
    '1.7': {
        'order': 4,
        'fix_old': False,
        'supported': True,
        'KDK': False,
        'catalog_version': '1.7.5',
        'newest_specification': '1.7.5'
    }
}


MDTYPEVERSIONS = {'PREMIS:OBJECT': '2.3', 'PREMIS:RIGHTS': '2.3',
                  'PREMIS:EVENT': '2.3', 'PREMIS:AGENT': '2.3',
                  'TEXTMD': '3.01', 'DC': '2008', 'NISOIMG': '2.0',
                  'AudioMD': '2.0', 'VideoMD': '2.0', 'EAD': '2002',
                  'MODS': '3.7', 'MARC': 'marcxml=1.2; marc=marc21',
                  'DDI': '2.5.1', 'EAC-CPF': '2010_revised', 'VRACore': '4.0',
                  'LIDO': '1.0', 'METSRIGHTS': 'n/a'}


ATTRIBS_TO_DELETE = {'.': ['ID', 'TYPE',
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
                         'ID', 'XPTR', 'MIMETYPE', 'SIZE', 'CREATED',
                         'CHECKSUM', 'CHECKSUMTYPE', 'LABEL',
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
                     'mets:structMap//mets:div/mets:fptr': [
                         'ID', 'CONTENTIDS'],
                     'mets:structMap//mets:div/mets:mptr': [
                         'ID', 'CONTENTIDS',
                         '{http://www.w3.org/1999/xlink}role',
                         '{http://www.w3.org/1999/xlink}arcrole',
                         '{http://www.w3.org/1999/xlink}title',
                         '{http://www.w3.org/1999/xlink}show',
                         '{http://www.w3.org/1999/xlink}actuate']}
