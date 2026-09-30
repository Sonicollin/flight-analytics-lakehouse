import pytest
from src.contracts import OpenSkyStateVectorContract, validate_state_vectors


def test_valid_state_vector_contract():
    """Verify that a well-formed state vector passes validation and normalizes ICAO24/callsign."""
    raw_payload = {
        "snapshot_time": 1700000000,
        "icao24": "4B1812",  # Uppercase hex to test validator normalization
        "callsign": "SWR126  ",  # Trailing spaces
        "origin_country": "Switzerland",
        "time_position": 1700000000,
        "last_contact": 1700000000,
        "longitude": 8.54,
        "latitude": 47.45,
        "baro_altitude": 10000.0,
        "on_ground": False,
        "velocity": 220.5,
        "true_track": 180.0,
        "vertical_rate": 0.0,
    }

    print("Testing valid_state_vector_contract")
    contract = OpenSkyStateVectorContract(**raw_payload)
    assert contract.icao24 == "4b1812"  # Converted to lowercase hex
    assert contract.callsign == "SWR126"  # Stripped
    assert contract.longitude == 8.54
    assert contract.latitude == 47.45


def test_invalid_icao24_hex():
    """Verify that invalid hexadecimal characters in icao24 trigger a validation error."""
    invalid_payload = {
        "snapshot_time": 1700000000,
        "icao24": "ZZZZZZ",  # Invalid hex
        "origin_country": "Japan",
        "last_contact": 1700000000,
        "on_ground": False,
    }

    print("Testing invalid icao24 hex")
    with pytest.raises(ValueError, match="Invalid hexadecimal ICAO24 string"):
        OpenSkyStateVectorContract(**invalid_payload)


def test_latitude_longitude_boundary_ranges():
    """Verify out-of-range latitude/longitude coordinates are rejected."""
    invalid_lat = {
        "snapshot_time": 1700000000,
        "icao24": "4b1812",
        "origin_country": "Japan",
        "last_contact": 1700000000,
        "latitude": 95.0,  # Max allowed is 90.0
        "longitude": 139.69,
        "on_ground": False,
    }

    print("Testing latitude and longitude boundary ranges")
    with pytest.raises(ValueError):
        OpenSkyStateVectorContract(**invalid_lat)


def test_mismatched_coordinates_validation():
    """Verify model validator fails if latitude is provided without longitude."""
    mismatched = {
        "snapshot_time": 1700000000,
        "icao24": "4b1812",
        "origin_country": "Japan",
        "last_contact": 1700000000,
        "latitude": 35.68,
        "longitude": None,  # Mismatched null
        "on_ground": False,
    }

    print("Testing if latitude and longitude are both present or null")
    with pytest.raises(ValueError, match="Latitude and Longitude must both be present or both be null"):
        OpenSkyStateVectorContract(**mismatched)


def test_validate_state_vectors_batch_isolation():
    """Verify validate_state_vectors separates valid and corrupt records correctly."""
    records = [
        {
            "snapshot_time": 1700000000,
            "icao24": "4b1812",
            "callsign": "ANA101",
            "origin_country": "Japan",
            "last_contact": 1700000000,
            "longitude": 139.69,
            "latitude": 35.68,
            "on_ground": False,
        },
        {
            "snapshot_time": 1700000000,
            "icao24": "INVALID",  # Bad length and hex
            "origin_country": "Unknown",
            "last_contact": 1700000000,
            "on_ground": False,
        },
    ]

    print("Testing if validate_state_vectors isolates valid and rejected records correctly")
    valid, rejected = validate_state_vectors(records)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert valid[0]["icao24"] == "4b1812"
    assert "error" in rejected[0]