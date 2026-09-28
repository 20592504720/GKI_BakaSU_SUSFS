"""Focused checks for GKI release tag synchronization."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import gki_fetch  # noqa: E402
import update_data  # noqa: E402


def makefile(sublevel: int) -> str:
    return f"VERSION = 5\nPATCHLEVEL = 10\nSUBLEVEL = {sublevel}\n"


class ReleaseTagTests(unittest.TestCase):
    def test_latest_revision_is_numeric_and_scoped_to_series(self) -> None:
        output = "\n".join(
            (
                "abc\trefs/tags/android13-5.10-2025-07_r2",
                "abc\trefs/tags/android13-5.10-2025-07_r10",
                "abc\trefs/tags/android13-5.10-2025-10_r4",
                "abc\trefs/tags/android12-5.10-2025-07_r99",
            )
        )
        with patch.object(
            gki_fetch.subprocess, "run",
            return_value=subprocess.CompletedProcess([], 0, output, ""),
        ):
            tags = gki_fetch.fetch_latest_release_tags("android13", "5.10")
        self.assertEqual(
            tags,
            {
                "2025-07": "android13-5.10-2025-07_r10",
                "2025-10": "android13-5.10-2025-10_r4",
            },
        )

    def test_missing_release_tags_fail_instead_of_assuming_r1(self) -> None:
        with patch.object(
            gki_fetch.subprocess, "run",
            return_value=subprocess.CompletedProcess([], 0, "", ""),
        ):
            with self.assertRaises(gki_fetch.FetchError):
                gki_fetch.fetch_latest_release_tags("android13", "5.10")

    def test_remote_ref_listing_retries_transient_failure(self) -> None:
        output = "abc\trefs/tags/android13-5.10-2025-07_r4\n"
        with (
            patch.object(
                gki_fetch.subprocess,
                "run",
                side_effect=[
                    subprocess.CalledProcessError(128, ["git", "ls-remote"]),
                    subprocess.CompletedProcess([], 0, output, ""),
                ],
            ) as run,
            patch.object(gki_fetch.time, "sleep") as sleep,
        ):
            tags = gki_fetch.fetch_latest_release_tags("android13", "5.10")
        self.assertEqual(tags["2025-07"], "android13-5.10-2025-07_r4")
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(2)

    def test_monthly_branches_include_deprecated(self) -> None:
        output = "\n".join(
            (
                "abc\trefs/heads/android12-5.10-2026-08",
                "abc\trefs/heads/deprecated/android12-5.10-2023-06",
                "abc\trefs/heads/android13-5.10-2026-08",
            )
        )
        with patch.object(
            gki_fetch.subprocess, "run",
            return_value=subprocess.CompletedProcess([], 0, output, ""),
        ):
            branches = gki_fetch.fetch_monthly_branches("android12", "5.10")
        self.assertEqual(branches, {"2026-08", "2023-06"})

    def test_existing_revision_and_new_month_are_updated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "5.10.json"
            path.write_text(
                json.dumps(
                    {
                        "android_version": "android13",
                        "kernel_version": "5.10",
                        "entries": [
                            {"date": "2025-07", "kernel": "5.10.238", "revision": "r1"},
                            {"date": "2025-08", "kernel": "5.10.238", "revision": "r1"},
                            {"date": "lts", "kernel": "5.10.245", "revision": "r1"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            tags = {
                "2025-07": "android13-5.10-2025-07_r4",
                "2025-10": "android13-5.10-2025-10_r2",
            }
            versions = {
                tags["2025-07"]: makefile(238),
                tags["2025-10"]: makefile(243),
            }
            with (
                patch.object(update_data, "json_path", return_value=str(path)),
                patch.object(update_data, "fetch_latest_release_tags", return_value=tags),
                patch.object(update_data, "fetch_monthly_branches", return_value={"2025-08", "2025-09"}),
                patch.object(update_data, "fetch_makefile", return_value=makefile(239)),
                patch.object(update_data, "fetch_tag_makefile", side_effect=versions.get),
                patch.object(update_data, "fetch_lts", return_value=makefile(260)),
                patch.object(update_data.time, "sleep"),
            ):
                changed = update_data.update_target(
                    "android13", "5.10", "2025-07", "2025-10", ""
                )
            self.assertTrue(changed)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["entries"],
                [
                    {"date": "2025-07", "kernel": "5.10.238", "revision": "r4"},
                    {"date": "2025-08", "kernel": "5.10.239"},
                    {"date": "2025-09", "kernel": "5.10.239"},
                    {"date": "2025-10", "kernel": "5.10.243", "revision": "r2"},
                    {"date": "lts", "kernel": "5.10.260"},
                ],
            )

    def test_same_revision_still_repairs_stale_kernel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "5.10.json"
            path.write_text(
                json.dumps(
                    {
                        "android_version": "android13",
                        "kernel_version": "5.10",
                        "entries": [
                            {"date": "2025-07", "kernel": "5.10.111", "revision": "r4"},
                            {"date": "lts", "kernel": "5.10.260"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(update_data, "json_path", return_value=str(path)),
                patch.object(update_data, "fetch_latest_release_tags", return_value={
                    "2025-07": "android13-5.10-2025-07_r4"
                }),
                patch.object(update_data, "fetch_monthly_branches", return_value=set()),
                patch.object(update_data, "fetch_tag_makefile", return_value=makefile(238)),
                patch.object(update_data, "fetch_lts", return_value=makefile(260)),
                patch.object(update_data.time, "sleep"),
            ):
                changed = update_data.update_target(
                    "android13", "5.10", "2025-07", "2025-07", ""
                )
            self.assertTrue(changed)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["entries"][0]["kernel"], "5.10.238")


if __name__ == "__main__":
    unittest.main()
