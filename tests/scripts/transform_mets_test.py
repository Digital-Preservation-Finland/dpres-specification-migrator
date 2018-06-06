"""Tests for the transform_mets module."""

import os
from uuid import uuid4
import copy
import pytest

import lxml.etree as ET

import mets as m
import premis as p
import xml_helpers.utils as h

from dpres_specification_migrator.scripts.transform_mets import main, \
        fix_1_4_mets, remove_attributes, parse_arguments, set_dip_metshdr, \
        migrate_mets, serialize_mets, get_fi_ns


TESTAIP_1_4 = 'tests/data/mets/mets_1_4.xml'
TESTAIP_1_6 = 'tests/data/mets/mets_1_6.xml'
TESTAIP_1_7 = 'tests/data/mets/mets_1_7.xml'


def test_parse_arguments():
    """test for argument parser"""
    args = parse_arguments(
        [TESTAIP_1_4, '--output_filename=mets_1_5.xml', '--objid=testid',
         '--to_version=1.5', '--workspace=workspace'])
    assert args.filepath == 'tests/data/mets/mets_1_4.xml'
    assert args.filename == 'mets_1_5.xml'
    assert args.objid == 'testid'
    assert args.to_version == '1.5'
    assert args.workspace == 'workspace'


@pytest.mark.parametrize(
    ["metsfile", "objid", "catalog", "contract", "valid"],
    [
        # Migrate 1.4 source, catalog not set, should pass
        (TESTAIP_1_4, "testid1", None, True, True),
        # Migrate 1.4 source to set version, should pass
        (TESTAIP_1_4, "testid2", '1.5', True, True),
        # Migrate 1.6 source, catalog not set, should pass
        (TESTAIP_1_6, "testid3", None, True, True),
        # Migrate 1.6 source to same version set excplicitly, should pass
        (TESTAIP_1_6, "testid4", '1.6', True, True),
        # Migrate 1.7 source to same version set excplicitly, should pass
        (TESTAIP_1_7, "testid5", '1.7', False, True),
        # Migrate mets to older version, should fail
        (TESTAIP_1_6, "testid6", '1.5', True, False),
        # Migrate mets to deprecated version, should fail
        (TESTAIP_1_6, "testid7", '1.4', True, False),
        # Migrate old mets to same but deprecated version, should fail
        (TESTAIP_1_4, "testid8", '1.4', True, False),
        # Migrate mets to unknown version, should fail
        (TESTAIP_1_6, "testid9", 'foo', True, False),
        # Migrate to version 1.7 without contractid, should fail
        (TESTAIP_1_6, "testid10", '1.7', False, False),
    ])
def test_mets_migration(testpath, metsfile, objid, catalog, contract, valid):
    """Tests that the script transform_mets outputs a METS document
    and migrates the contents to a newer fi:CATALOG
    version as specified in the command line arguments.
    """
    version = '1.7.0'

    old_root = h.readfile(metsfile).getroot().attrib
    old_elem_count = len(h.readfile(metsfile).getroot().xpath('./*'))
    for attrib in old_root:
        if len(attrib.split('}')) > 1:
            old_root[attrib.split('}')[1]] = old_root[attrib]
            del old_root[attrib]

    if h.readfile(metsfile).getroot().xpath('@*[local-name() = "CATALOG"]'):
        cat_spec = 'CATALOG'
    else:
        cat_spec = 'SPECIFICATION'

    if contract:
        contractid = 'urn:uuid:' + str(uuid4())
        if catalog:
            returncode = main([metsfile, '--objid', objid, '--to_version',
                               catalog, '--workspace', testpath,
                               '--contractid', contractid])
        else:
            returncode = main([metsfile, '--objid', objid,
                               '--workspace', testpath,
                               '--contractid', contractid])
    else:
        returncode = main([metsfile, '--objid', objid, '--to_version',
                           catalog, '--workspace', testpath])

    if valid:
        new_mets = os.path.join(testpath, 'mets.xml')
        assert os.path.isfile(new_mets)

        root = ET.parse(new_mets).getroot()
        assert len(root.xpath('./*')) == old_elem_count
        if catalog:
            version = catalog + '.0'

        new_root = copy.deepcopy(root)
        new_attribs = new_root.attrib
        for attrib in new_attribs:
            if len(attrib.split('}')) > 1:
                new_attribs[attrib.split('}')[1]] = new_attribs[attrib]
                del new_attribs[attrib]
        for attrib in old_root:
            assert attrib in new_attribs
            if attrib not in ['CATALOG', 'SPECIFICATION', 'PROFILE']:
                assert old_root[attrib] == new_attribs[attrib]

        assert 'MDTYPEVERSION' in root.xpath(
            './/mets:mdWrap', namespaces=m.NAMESPACES)[1].attrib

        assert root.xpath('./mets:metsHdr/@LASTMODDATE',
                          namespaces=m.NAMESPACES)

        assert root.xpath('./mets:metsHdr/@LASTMODDATE',
                          namespaces=m.NAMESPACES) > root.xpath(
                              './mets:metsHdr/@CREATEDATE',
                              namespaces=m.NAMESPACES)

        if version == '1.7.0':
            assert 'CONTRACTID' in new_attribs
            assert root.get('{http://digitalpreservation.fi/schemas/'
                            'mets/fi-extensions}%s' % cat_spec) == version
            assert root.get('{http://digitalpreservation.fi/schemas/'
                            'mets/fi-extensions}CONTRACTID')
            assert root.get('PROFILE') == 'http://digitalpreservation.fi/' \
                                          'mets-profiles/cultural-heritage'
        else:
            assert root.get('{http://www.kdk.fi/standards/'
                            'mets/kdk-extensions}%s' % cat_spec) == version
            assert '{http://www.kdk.fi/standards/' \
                   'mets/kdk-extensions}CONTRACTID' not in root.attrib
            assert '{http://digitalpreservation.fi/schemas/' \
                   'mets/fi-extensions}CONTRACTID' not in root.attrib
            assert root.get('PROFILE') == 'http://www.kdk.fi/kdk-mets-profile'
            assert 'CONTRACTID' not in new_attribs

    else:
        assert returncode == 117


@pytest.mark.parametrize(
    ["metsfile", "objid", "catalog", "valid"],
    [
        # Migrate 1.4 source, catalog not set, should pass
        (TESTAIP_1_4, "testid11", None, True),
        # Migrate 1.4 source to set version, should pass
        (TESTAIP_1_4, "testid2", '1.5', True),
        # Migrate 1.6 source, catalog not set, should pass
        (TESTAIP_1_6, "testid13", None, True),
        # Migrate 1.6 source to same version set excplicitly, should pass
        (TESTAIP_1_6, "testid14", '1.6', True),
        # Migrate 1.7 source to same version set excplicitly, should pass
        (TESTAIP_1_7, "testid5", '1.7', True),
    ])
def test_dip_migration(testpath, metsfile, objid, catalog, valid):
    """Tests that the script transform_mets outputs a METS document
    and migrates the contents to a newer fi:CATALOG
    version as specified in the command line arguments.
    """
    version = '1.7.0'
    filename = objid + '.xml'

    old_elem_count = len(h.readfile(metsfile).getroot().xpath('./*'))

    contractid = 'urn:uuid:' + str(uuid4())
    if catalog:
        returncode = main([metsfile, '--objid', objid, '--to_version',
                           catalog, '--workspace', testpath,
                           '--contractid', contractid,
                           '--record_status', 'dissemination',
                           '--output_filename', filename])
    else:
        returncode = main([metsfile, '--objid', objid,
                           '--workspace', testpath,
                           '--contractid', contractid,
                           '--record_status', 'dissemination',
                           '--output_filename', filename])

    if valid:
        new_mets = os.path.join(testpath, filename)
        assert os.path.isfile(new_mets)

        root = ET.parse(new_mets).getroot()
        assert len(root.xpath('./*')) == old_elem_count
        if catalog:
            version = catalog + '.0'

        assert root.get('OBJID') == objid

        assert 'MDTYPEVERSION' in root.xpath(
            './/mets:mdWrap', namespaces=m.NAMESPACES)[1].attrib

        assert 'ID' not in root.attrib
        assert not root.xpath('@*[local-name() = "SPECIFICATION"]')
        assert root.xpath('@*[local-name() = "CATALOG"]')

        assert root.xpath('./mets:metsHdr/@RECORDSTATUS',
                          namespaces=m.NAMESPACES)[0] == 'dissemination'

        assert root.xpath('./mets:metsHdr/@CREATEDATE',
                          namespaces=m.NAMESPACES)

        assert not root.xpath('./mets:metsHdr/@LASTMODDATE',
                              namespaces=m.NAMESPACES)

        if version == '1.7.0':
            assert root.get('{http://digitalpreservation.fi/schemas/'
                            'mets/fi-extensions}CATALOG') == version
            assert root.get('{http://digitalpreservation.fi/schemas/'
                            'mets/fi-extensions}CONTRACTID')
            assert root.get('PROFILE') == 'http://digitalpreservation.fi/' \
                                          'mets-profiles/cultural-heritage'
        else:
            assert root.get('{http://www.kdk.fi/standards/'
                            'mets/kdk-extensions}CATALOG') == version
            assert '{http://www.kdk.fi/standards/' \
                   'mets/kdk-extensions}CONTRACTID' not in root.attrib
            assert '{http://digitalpreservation.fi/schemas/' \
                   'mets/fi-extensions}CONTRACTID' not in root.attrib
            assert root.get('PROFILE') == 'http://www.kdk.fi/kdk-mets-profile'

    else:
        assert returncode == 117


def test_fix_1_4_mets():
    """Tests the migrate_old_mets function by asserting that the
    function has modified the METS testdata properly.
    Asserts that the @MDTYPEVERSION attribute is written into
    mets:mdWrap elements, that the mets:structMap only has one child
    element and that charset is writtern into a text files
    premis:formatName element. Also checks that the METSRIGHTS
    attribute value is moved from MDTYPE to OTHERMDTYPE.
    """
    root = ET.parse(TESTAIP_1_4).getroot()
    fix_1_4_mets(root)

    assert 'MDTYPEVERSION' in root.xpath(
        './mets:dmdSec/mets:mdWrap', namespaces=m.NAMESPACES)[0].attrib
    assert 'MDTYPEVERSION' in root.xpath(
        './mets:amdSec/mets:techMD/mets:mdWrap',
        namespaces=m.NAMESPACES)[0].attrib

    assert root.xpath('./mets:amdSec/mets:rightsMD/mets:mdWrap/@MDTYPE',
                      namespaces=m.NAMESPACES)[0] == 'OTHER'
    assert root.xpath('./mets:amdSec/mets:rightsMD/mets:mdWrap/@OTHERMDTYPE',
                      namespaces=m.NAMESPACES)[0] == 'METSRIGHTS'

    assert len(root.xpath('./mets:structMap', namespaces=m.NAMESPACES)) == 1

    (format_name, _) = p.parse_format(root.xpath(
        './mets:amdSec/*/*/*/*', namespaces=m.NAMESPACES)[1])
    assert format_name == 'text/plain; charset=UTF-8'


def test_remove_attributes():
    """Tests the remove_attributes function by running the function with
    testdata and asserting that selected attributes have been removed
    from the testdata.
    """
    root = ET.parse(TESTAIP_1_4).getroot()
    remove_attributes(root)

    for mets_mdwrap in root.xpath('.//mets:mdWrap', namespaces=m.NAMESPACES):
        assert 'ID' not in mets_mdwrap.attrib

    for mets_file in root.xpath('./mets:fileSec/*/*', namespaces=m.NAMESPACES):
        assert 'SIZE' not in mets_file.attrib

    for mets_fptr in root.xpath('./mets:structMap//mets:fptr',
                                namespaces=m.NAMESPACES):
        assert 'ID' not in mets_fptr.attrib


def test_set_dip_metshdr():
    """Tests the set_methdr function by asserting that the
    @RECORDSTATUS attribute has been created and contains the correct
    value, that the mets:agent/mets:name element contains the correct
    text and that the LASTMODDATE attribute is not present.
    """
    root = ET.parse(TESTAIP_1_4).getroot()
    new_root = set_dip_metshdr(root)
    hdr = new_root.xpath('./mets:metsHdr', namespaces=m.NAMESPACES)[0]

    assert hdr.get('RECORDSTATUS') == 'dissemination'
    assert len(new_root.xpath('./mets:metsHdr/mets:agent',
                              namespaces=m.NAMESPACES)) == 1
    assert new_root.xpath(
        './mets:metsHdr/mets:agent/mets:name',
        namespaces=m.NAMESPACES)[0].text == 'CSC - IT Center for Science Ltd.'
    assert 'LASTMODDATE' not in hdr.attrib


def test_migrate_mets():
    """Tests that the migrate_mets function changes the xml as intended
    by asserting that the attributes in the mets root element are present
    and that their values are correct.
    Alse asserts that the correct number of child elements are included
    in the new XML data.
    """
    fi_ns = 'http://www.kdk.fi/standards/mets/kdk-extensions'
    mets = '<mets:mets ' \
           'xmlns:mets="http://www.loc.gov/METS/" ' \
           'xmlns:xlink="http://www.w3.org/1999/xlink" ' \
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
           'xmlns:fi="http://www.kdk.fi/standards/mets/kdk-extensions" ' \
           'xsi:schemaLocation="http://www.loc.gov/METS/ ' \
           'http://www.loc.gov/standards/mets/mets.xsd" ' \
           'PROFILE="http://www.kdk.fi/kdk-mets-profile" OBJID="xxx" ' \
           'fi:CATALOG="1.6.0" LABEL="yyy"><mets:metsHdr></mets:metsHdr>' \
           '<mets:dmdSec/>' \
           '<mets:amdSec><mets:digiprovMD><mets:mdRef ' \
           'OTHERMDTYPE="KDKPreservationPlan"/></mets:digiprovMD>' \
           '</mets:amdSec></mets:mets>'
    mets_xml = ET.fromstring(mets)

    (dip, objid) = migrate_mets(mets_xml, '1.7', '1.6', contract='aaa')

    assert objid == 'xxx'
    assert len(dip.attrib) == 6
    assert dip.get('{%s}CONTRACTID' % fi_ns) == 'aaa'
    assert dip.get('{%s}CATALOG' % fi_ns) == '1.7.0'
    assert dip.get('OBJID') == 'xxx'
    assert dip.get('LABEL') == 'yyy'
    assert dip.get('PROFILE') == 'http://digitalpreservation.fi/' \
                                 'mets-profiles/cultural-heritage'
    assert len(dip) == 3
    assert dip.xpath('//mets:mdRef/@OTHERMDTYPE',
                     namespaces=m.NAMESPACES)[0] == 'FiPreservationPlan'


def test_serialize_mets():
    """Tests the serialize_mets function by passing XML data to the
    function and asserting that it's output is identical to the
    intended result.
    """
    mets_input = '<mets:mets ' \
        'xmlns:mets="http://www.loc.gov/METS/" ' \
        'xmlns:xlink="http://www.w3.org/1999/xlink" ' \
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
        'xmlns:fi="http://www.kdk.fi/standards/mets/kdk-extensions" ' \
        'xmlns:textmd="http://www.kdk.fi/standards/textmd" ' \
        'xsi:schemaLocation="http://www.loc.gov/METS/ ' \
        'http://www.loc.gov/standards/mets/mets.xsd" ' \
        'PROFILE="http://digitalpreservation.fi/' \
        'mets-profiles/cultural-heritage" ' \
        'OBJID="xxx" fi:CATALOG="1.7.0"/>'

    intended_result = '<mets:mets ' \
        'xmlns:mets="http://www.loc.gov/METS/" ' \
        'xmlns:xlink="http://www.w3.org/1999/xlink" ' \
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
        'xmlns:fi="http://digitalpreservation.fi/schemas/mets/fi-extensions"' \
        ' xmlns:textmd="info:lc/xmlns/textMD-v3" ' \
        'xsi:schemaLocation="http://www.loc.gov/METS/ '\
        'http://www.loc.gov/standards/mets/mets.xsd" ' \
        'PROFILE="http://digitalpreservation.fi/' \
        'mets-profiles/cultural-heritage" '\
        'OBJID="xxx" fi:CATALOG="1.7.0"/>'

    mets_xml = ET.fromstring(mets_input)
    mets_outcome = serialize_mets(mets_xml)

    assert h.compare_trees(ET.fromstring(intended_result),
                           ET.fromstring(mets_outcome)) is True


def test_get_fi_ns():
    """Tests the get_fi_ns function by asserting that it outputs a
    different namespace for catalog version 1.7 than the rest.
    """
    assert get_fi_ns(
        '1.7') == 'http://digitalpreservation.fi/schemas/mets/fi-extensions'
    assert get_fi_ns(
        '1.6') == 'http://www.kdk.fi/standards/mets/kdk-extensions'
    assert get_fi_ns(
        'foo') == 'http://digitalpreservation.fi/schemas/mets/fi-extensions'
