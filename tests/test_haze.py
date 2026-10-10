"""Descriptor boundaries and region handling. No live API calls."""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import haze  # noqa: E402


PSI_ITEM = {
    "timestamp": "2026-10-10T09:00:00+08:00",
    "readings": {
        "psi_twenty_four_hourly": {
            "north": 50,
            "south": 51,
            "east": 101,
            "west": 201,
            "central": 301,
        }
    },
}

PM_ITEM = {
    "timestamp": "2026-10-10T09:00:00+08:00",
    "readings": {
        "pm25_one_hourly": {
            "north": 55,
            "south": 56,
            "east": 151,
            "west": 250,
            "central": 251,
        }
    },
}


class DescriptorTests(unittest.TestCase):
    def test_psi_boundaries(self) -> None:
        cases = (
            (0, "Good"),
            (50, "Good"),
            (50.0, "Good"),
            (51, "Moderate"),
            (100, "Moderate"),
            (101, "Unhealthy"),
            (200, "Unhealthy"),
            (201, "Very unhealthy"),
            (300, "Very unhealthy"),
            (301, "Hazardous"),
            (500, "Hazardous"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(haze.psi_descriptor(value), expected)

    def test_pm25_boundaries(self) -> None:
        cases = (
            (0, "Band 1 (Normal)"),
            (55, "Band 1 (Normal)"),
            (56, "Band 2 (Elevated)"),
            (150, "Band 2 (Elevated)"),
            (151, "Band 3 (High)"),
            (250, "Band 3 (High)"),
            (250.0, "Band 3 (High)"),
            (251, "Band 4 (Very High)"),
            (400, "Band 4 (Very High)"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(haze.pm25_descriptor(value), expected)


class RegionTests(unittest.TestCase):
    def test_default_is_all_five_in_order(self) -> None:
        self.assertEqual(haze.resolve_regions([]), list(haze.REGIONS))

    def test_case_and_duplicates(self) -> None:
        self.assertEqual(
            haze.resolve_regions([" Central ", "north", "NORTH"]),
            ["central", "north"],
        )

    def test_unknown_region_is_an_error(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = haze.main(["toa payoh"])
        self.assertEqual(code, 1)
        self.assertIn("unknown region", stderr.getvalue())
        self.assertIn("central", stderr.getvalue())


class BundleTests(unittest.TestCase):
    def test_skill_copy_matches_root(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill = root / "skills" / "singapore-haze"
        self.assertEqual(
            (root / "SKILL.md").read_bytes(),
            (skill / "SKILL.md").read_bytes(),
        )
        self.assertEqual(
            (root / "scripts" / "haze.py").read_bytes(),
            (skill / "scripts" / "haze.py").read_bytes(),
        )


class ReportTests(unittest.TestCase):
    def test_descriptors_and_timestamps_are_attached(self) -> None:
        report = haze.report_from_items(PSI_ITEM, PM_ITEM, ["central", "north"])
        self.assertEqual(report["psi_timestamp"], "2026-10-10T09:00:00+08:00")
        central, north = report["regions"]
        self.assertEqual(central["region"], "central")
        self.assertEqual(central["psi_twenty_four_hourly"]["value"], 301)
        self.assertEqual(central["psi_twenty_four_hourly"]["descriptor"], "Hazardous")
        self.assertEqual(central["pm25_one_hourly"]["descriptor"], "Band 4 (Very High)")
        self.assertEqual(central["pm25_one_hourly"]["unit"], "µg/m³")
        self.assertEqual(north["psi_twenty_four_hourly"]["descriptor"], "Good")
        self.assertEqual(north["pm25_one_hourly"]["descriptor"], "Band 1 (Normal)")
        text = haze.render_text(report)
        self.assertIn("Central", text)
        self.assertIn("Hazardous", text)
        self.assertIn("09:00 SGT", text)

    def test_missing_reading_is_an_error(self) -> None:
        with self.assertRaises(haze.HazeError):
            haze.report_from_items(PSI_ITEM, PM_ITEM, ["nope"])

    def test_connection_failure_is_an_error(self) -> None:
        with self.assertRaises(haze.HazeError):
            haze.fetch_json("http://127.0.0.1:9", timeout=2)


if __name__ == "__main__":
    unittest.main()
