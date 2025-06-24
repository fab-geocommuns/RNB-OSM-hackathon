import pytest
import time
import requests_mock
from flask.testing import FlaskClient
from rnb_to_osm import app, db
from rnb_to_osm.database import Export
from rnb_to_osm.cities import City

# Sample OSM XML response that would come from Overpass API
SAMPLE_OSM_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <way id="123456789">
    <nd ref="1234567890"/>
    <nd ref="1234567891"/>
    <nd ref="1234567892"/>
    <tag k="building" v="yes"/>
  </way>
</osm>"""


@pytest.fixture
def mock_overpass_api():
    with requests_mock.Mocker() as m:
        # Mock the Overpass API endpoint
        m.post("https://overpass-api.de/api/interpreter", text=SAMPLE_OSM_RESPONSE)
        yield m


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Add a test city
            city = City.get_by_code_insee("75056")
            yield client
            db.drop_all()


def test_export_workflow(client: FlaskClient, mock_overpass_api):
    """Test the complete export workflow:
    1. Trigger an export
    2. Wait for it to complete
    3. Verify the result
    """
    # Trigger export
    response = client.post("/export", json={"code_insee": "75056"})
    assert response.status_code == 202
    data = response.get_json()
    assert data["status"] == "success"
    export_id = data["export_id"]

    # Poll until export is done or timeout
    timeout = time.time() + 30  # 30 seconds timeout
    while time.time() < timeout:
        response = client.get(f"/export/{export_id}")
        assert response.status_code == 200
        data = response.get_json()

        if data["status"] == "done":
            # Verify export result
            assert "result" in data
            assert isinstance(data["result"], str)
            assert "<osm" in data["result"]  # Basic check for OSM XML content
            # Verify our mocked data is used
            assert "123456789" in data["result"]  # Check for the mocked way ID
            break
        elif data["status"] == "failed":
            pytest.fail("Export failed")

        time.sleep(1)  # Wait before next poll
    else:
        pytest.fail("Export timed out")
