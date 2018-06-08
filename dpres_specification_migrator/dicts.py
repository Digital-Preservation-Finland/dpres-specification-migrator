"""Global variables concerning the METS metadata and migration options."""


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
