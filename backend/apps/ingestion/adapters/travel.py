"""Corporate travel adapter — Concur/Navan-style JSON (trips -> segments).

Each segment becomes one row. Category drives the factor (flight / hotel / rail
/ ground). Flights that give only IATA codes get a great-circle distance estimate
from the AirportCode reference table, then bucket into short/long haul. All
business travel is Scope 3.
"""
import json
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from apps.common.exceptions import IngestionError, UnmappedCodeError
from apps.common.units import to_canonical
from apps.ingestion.services.normalizer import parse_date
from apps.reference.models import AirportCode

from .base import NormalizedRow

_SHORT_HAUL_KM = Decimal("1500")


def _haversine_km(lat1, lon1, lat2, lon2) -> Decimal:
    r = 6371.0  # mean earth radius, km
    p1, p2 = radians(float(lat1)), radians(float(lat2))
    dphi = radians(float(lat2) - float(lat1))
    dlmb = radians(float(lon2) - float(lon1))
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlmb / 2) ** 2
    return Decimal(str(round(2 * r * asin(sqrt(a)), 1)))


class TravelAdapter:
    source_type = "travel"

    def parse(self, raw_bytes, config):
        data = json.loads(raw_bytes.decode("utf-8"))
        row_number = 0
        for trip in data.get("trips", []):
            for idx, segment in enumerate(trip.get("segments", [])):
                row_number += 1
                payload = {
                    "trip_id": trip.get("trip_id"),
                    "traveler_id": trip.get("traveler_id"),
                    "segment_index": idx,
                    **segment,
                }
                yield row_number, payload

    def normalize(self, row, config) -> NormalizedRow:
        seg_type = row.get("type")
        if seg_type == "flight":
            return self._flight(row)
        if seg_type == "hotel":
            return self._hotel(row)
        if seg_type in ("rail", "ground"):
            return self._distance_segment(row, seg_type)
        raise IngestionError(f"Unknown travel segment type: {seg_type!r}")

    def _flight(self, row) -> NormalizedRow:
        given = row.get("distance_km")
        estimate = self._try_estimate(row.get("from"), row.get("to"))
        extra = {
            "route": f"{row.get('from')}-{row.get('to')}",
            "cabin": row.get("cabin"),
            "trip_id": row.get("trip_id"),
        }

        if given is None:
            if estimate is None:
                raise UnmappedCodeError(
                    f"Flight {row.get('from')}-{row.get('to')} has no distance and unknown airports."
                )
            distance = estimate
            extra["distance_estimated"] = True
        else:
            distance = Decimal(str(given))
            # If we can estimate, sanity-check the supplied distance against it.
            if estimate and estimate > 0:
                ratio = distance / estimate
                if ratio < Decimal("0.5") or ratio > Decimal("2"):
                    extra["implausible"] = (
                        f"Given distance {distance} km vs ~{estimate} km expected "
                        f"for {extra['route']}."
                    )

        haul = "short_haul" if distance < _SHORT_HAUL_KM else "long_haul"
        return NormalizedRow(
            activity_category=f"flight_{haul}",
            scope="3",
            quantity=distance,
            unit="km",
            activity_date=parse_date(row["depart"]),
            extra=extra,
        )

    def _hotel(self, row) -> NormalizedRow:
        quantity, unit = to_canonical(row["nights"], "night")
        return NormalizedRow(
            activity_category="hotel_night",
            scope="3",
            quantity=quantity,
            unit=unit,
            activity_date=parse_date(row["checkin"]),
            extra={"city": row.get("city"), "trip_id": row.get("trip_id")},
        )

    def _distance_segment(self, row, seg_type) -> NormalizedRow:
        if row.get("distance_km") is None:
            raise IngestionError(f"{seg_type} segment missing distance_km")
        quantity, unit = to_canonical(row["distance_km"], "km")
        category = "rail" if seg_type == "rail" else "ground_taxi"
        return NormalizedRow(
            activity_category=category,
            scope="3",
            quantity=quantity,
            unit=unit,
            activity_date=parse_date(row["date"]),
            extra={"mode": row.get("mode"), "trip_id": row.get("trip_id")},
        )

    def _try_estimate(self, origin, dest):
        """Great-circle estimate, or None if either airport is unknown."""
        try:
            return self._estimate_distance(origin, dest)
        except UnmappedCodeError:
            return None

    def _estimate_distance(self, origin, dest) -> Decimal:
        airports = {a.iata: a for a in AirportCode.objects.filter(iata__in=[origin, dest])}
        if origin not in airports or dest not in airports:
            missing = [c for c in (origin, dest) if c not in airports]
            raise UnmappedCodeError(f"Unknown airport code(s): {', '.join(missing)}")
        o, d = airports[origin], airports[dest]
        return _haversine_km(o.latitude, o.longitude, d.latitude, d.longitude)
