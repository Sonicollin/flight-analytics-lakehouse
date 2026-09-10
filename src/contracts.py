from typing import Self
from pydantic import BaseModel, Field, field_validator, model_validator


class OpenSkyStateVectorContract(BaseModel):
    """
    Data contract enforcing structural, numerical, and quality rules
    for raw OpenSky Network state vector records.
    """

    snapshot_time: int = Field(
        ..., 
        description="Unix timestamp (seconds) of the state vector snapshot."
    )
    icao24: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        description="Unique 24-bit ICAO transponder address in hexadecimal."
    )
    callsign: str | None = Field(
        default=None, 
        description="8-character flight callsign (or tail number) stripped of padding."
    )
    origin_country: str = Field(
        ..., 
        description="Country name inferred from transponder ICAO address."
    )
    time_position: int | None = Field(
        default=None, 
        description="Unix timestamp for last position fix."
    )
    last_contact: int = Field(
        ..., 
        description="Unix timestamp for last signal received by OpenSky sensor network."
    )
    longitude: float | None = Field(
        default=None, 
        ge=-180.0, 
        le=180.0, 
        description="WGS-84 longitude in decimal degrees."
    )
    latitude: float | None = Field(
        default=None, 
        ge=-90.0, 
        le=90.0, 
        description="WGS-84 latitude in decimal degrees."
    )
    baro_altitude: float | None = Field(
        default=None, 
        description="Barometric altitude in meters."
    )
    on_ground: bool = Field(
        ..., 
        description="Flag indicating whether aircraft is on the ground."
    )
    velocity: float | None = Field(
        default=None, 
        ge=0.0, 
        description="Ground speed in meters per second."
    )
    true_track: float | None = Field(
        default=None, 
        ge=0.0, 
        lt=360.0, 
        description="True track angle in degrees clockwise from true North."
    )
    vertical_rate: float | None = Field(
        default=None, 
        description="Climb/sink rate in meters per second."
    )

    @field_validator("icao24")
    @classmethod
    def validate_hex_icao24(cls, value: str) -> str:
        """Ensure ICAO address is a valid lowercase hexadecimal string."""
        clean_val = value.strip().lower()
        if not all(c in "0123456789abcdef" for c in clean_val):
            raise ValueError(f"Invalid hexadecimal ICAO24 string: '{value}'")
        return clean_val

    @field_validator("callsign")
    @classmethod
    def clean_callsign(cls, value: str | None) -> str | None:
        """Strip whitespace and return None if callsign is empty."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    @model_validator(mode="after")
    def validate_position_consistency(self) -> Self:
        """Ensures latitude and longitude are either both present or both null."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and Longitude must both be present or both be null.")
        return self


def validate_state_vectors(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Validates a list of raw state vector dictionaries against OpenSkyStateVectorContract.

    Args:
        records: Raw parsed state vector dicts.

    Returns:
        A tuple of (valid_records, invalid_records_with_errors).
    """
    valid_records: list[dict] = []
    rejected_records: list[dict] = []

    for raw_record in records:
        try:
            validated = OpenSkyStateVectorContract(**raw_record)
            valid_records.append(validated.model_dump())
        except Exception as err:
            rejected_records.append({"raw_record": raw_record, "error": str(err)})

    return valid_records, rejected_records