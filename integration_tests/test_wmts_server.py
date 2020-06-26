import pytest
from owslib.wmts import WebMapTileService
from urllib import request
from lxml import etree
from imghdr import what


def get_xsd(name):
    xsd_f = request.urlopen("http://schemas.opengis.net/wmts/1.0/" + name)
    schema_doc = etree.parse(xsd_f)
    return etree.XMLSchema(schema_doc)


def check_wmts_error(url, expected_error_message=None, expected_status_code=400):
    try:
        resp = request.urlopen(url, timeout=10)

        # Should not get here
        assert False
    except Exception as e:
        # Validate status code
        assert e.getcode() == expected_status_code

        resp_content = e.fp.read()
        assert expected_error_message in str(resp_content)
        resp_xml = etree.XML(resp_content)
        assert resp_xml is not None


def test_no_request(ows_server):
    # Make empty request to server:
    check_wmts_error(ows_server.url + "/wmts", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wmts_error(ows_server.url + "/wmts?request=NoSuchOperation", "Unrecognised operation: NOSUCHOPERATION", 400)


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wmts_error(ows_server.url + "/wmts?request=GetCapabilities&service=NotWMTS", "Invalid service", 400)


@pytest.mark.xfail(reason="OWS Getcaps don't pass XSD")
def test_getcap(ows_server):
    resp = request.urlopen(ows_server.url + "/wmts?request=GetCapabilities&service=WMTS&version=1.0.0", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("wmtsGetCapabilities_response.xsd")
    assert gc_xds.validate(resp_xml)


def test_wmts_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wmts = WebMapTileService(url=ows_server.url+"/wmts")

    assert wmts.identification.type == "OGC WMTS"
    assert wmts.identification.version == "1.0.0"

    # Ensure that we have at least some layers available
    contents = list(wmts.contents)
    assert contents