"""Unit tests for the ``uniprot`` extraction module."""

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import call, patch

from bioregistry.alignment_model import Record
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external import uniprot
from bioregistry.external.uniprot import PREFIX_FIELD, process_uniprot_raw

EXAMPLE_RECORDS: dict[str, dict[str, Any]] = {
    # a valid record with all the trimmings
    "ValidRecord": {
        "original": {
            "abbrev": "ValidRecord",
            "name": "Test Standard Record",
            "servers": ["https://example.org/"],
            "category": "reference",
            "id": "DB-0123",
            "doiId": "DOI:10.1234/SOME_TEST_DOI.",
            "pubMedId": 987654321,
            "linkType": "explicit",
            "statistics": {"count": 1},
            "dbUrl": "https://example.org/%s",
        },
        "parsed": Record.model_validate(
            {
                "name": "Test Standard Record",
                "homepage": "https://example.org/",
                "keywords": ["reference"],
                "publications": [{"doi": "10.1234/some_test_doi", "pubmed": "987654321"}],
                URI_FORMAT_KEY: "https://example.org/$1",
            }
        ),
    },
    # full HTTPS DOI
    "FullDoiUrl": {
        "original": {
            "abbrev": "FullDoiUrl",
            "name": "Test with DOI",
            "servers": ["https://example.org/"],
            "category": "reference",
            "id": "DB-0124",
            "doiId": "https://doi.org/10.1234/567890.",
            "linkType": "explicit",
            "statistics": {"count": 1},
            "dbUrl": "https://example.org/%u",
        },
        "parsed": Record.model_validate(
            {
                "name": "Test with DOI",
                "homepage": "https://example.org/",
                "keywords": ["reference"],
                "publications": [{"doi": "10.1234/567890"}],
                URI_FORMAT_KEY: "https://example.org/$1",
            }
        ),
    },
    # PMID as an int -- should be converted to a string
    "PmidIntToStr": {
        "original": {
            "abbrev": "PmidIntToStr",
            "name": "Test with PMID int",
            "servers": ["https://example.org/"],
            "category": "reference",
            "id": "DB-0125",
            "pubMedId": 987654321,
            "linkType": "explicit",
            "statistics": {"count": 1},
            "dbUrl": "https://example.org/%s",
        },
        "parsed": Record.model_validate(
            {
                "name": "Test with PMID int",
                "homepage": "https://example.org/",
                "keywords": ["reference"],
                "publications": [{"pubmed": "987654321"}],
                URI_FORMAT_KEY: "https://example.org/$1",
            }
        ),
    },
    # Record with both %s and %u -- will not be parsed
    "BothFmtStrs": {
        "original": {
            "abbrev": "BothFmtStrs",
            "name": "Both Format DB",
            "servers": ["https://both.org/"],
            "category": "reference",
            "id": "DB-0126",
            "linkType": "explicit",
            "statistics": {"count": 2},
            "dbUrl": "https://both.org/%s/%u",
        },
        "parsed": None,
    },
    # Record without %s or %u
    # record will be saved without URI_FORMAT_KEY
    "NoFmtStrs": {
        "original": {
            "abbrev": "NoFmtStrs",
            "name": "Has Terrible URI",
            "servers": ["https://fungi.ensembl.org/"],
            "category": "reference",
            "id": "DB-0129",
            "linkType": "implicit",
            "statistics": {"count": 3},
            "dbUrl": "https://fungi.ensembl.org/%d/%m/%y",
        },
        "parsed": Record.model_validate(
            {
                "name": "Has Terrible URI",
                "homepage": "https://fungi.ensembl.org/",
                "keywords": ["reference"],
            }
        ),
    },
    # Record with prefix from ``HAS_BAD_URI``
    # record will be saved without URI_FORMAT_KEY
    "EnsemblFungi": {
        "original": {
            "abbrev": "EnsemblFungi",
            "name": "Has Bad URI",
            "servers": ["https://fungi.ensembl.org/"],
            "category": "reference",
            "id": "DB-0128",
            "linkType": "implicit",
            "statistics": {"count": 3},
            "dbUrl": "https://fungi.ensembl.org/%s",
        },
        "parsed": Record.model_validate(
            {
                "name": "Has Bad URI",
                "homepage": "https://fungi.ensembl.org/",
                "keywords": ["reference"],
            }
        ),
    },
    # test server / homepage deduplication
    "TwoServers": {
        "original": {
            "abbrev": "TwoServers",
            "name": "Two Servers",
            "servers": ["https://server.one", "https://server.two"],
            "category": "whatever",
            "id": "DB-0130",
            "linkType": "explicit",
            "statistics": {"count": 1},
            "dbUrl": "https://some.server.one/%s",
        },
        "parsed": Record.model_validate(
            {
                "name": "Two Servers",
                "homepage": "https://server.one",
                "keywords": ["whatever"],
                URI_FORMAT_KEY: "https://some.server.one/$1",
            }
        ),
    },
}

# Record in UNIPROT_SKIP_PREFIXES -- will not be parsed
SKIPPED_PREFIX: dict[str, Any] = {
    "original": {
        "abbrev": "UniPathway",
        "name": "Deprecated database",
        "servers": ["https://unipathway.org/"],
        "category": "reference",
        "id": "DB-0127",
        "linkType": "explicit",
        "statistics": {"count": 2},
        "dbUrl": "https://unipathway.org/%u",
    },
    "parsed": None,
}


SKIP_PREFIXES = "UNIPROT_SKIP_PREFIXES"
_process_record = "_process_record"


class TestProcessUniprotRaw(unittest.TestCase):
    """Test the ``process_uniprot_raw`` function."""

    def setUp(self) -> None:
        """Create a temporary folder that lives for the whole test case."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self) -> None:
        """Remove the temporary folder."""
        self.tmp_dir.cleanup()

    def _write_json(self, obj: dict[str, Any]) -> Path:
        """Write a small JSON file for the tests."""
        p = self.tmp_path / "raw.json"
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
        return p

    def test_returns_dict_of_processed_records(self) -> None:
        """Ensure that each record is processed by ``_process_record``."""
        payload = {
            "results": [
                {PREFIX_FIELD: "A", "foo": 1},
                {PREFIX_FIELD: "B", "foo": 2},
                {PREFIX_FIELD: "C", "foo": 3},
            ]
        }
        path = self._write_json(payload)

        # No prefixes are skipped
        with (
            patch.object(uniprot, SKIP_PREFIXES, set()),
            patch.object(uniprot, _process_record) as mock_process,
        ):
            mock_process.side_effect = lambda prefix, rec: {"processed": f"{prefix}:{rec['foo']}"}

            result: dict[str, Any] = uniprot.process_uniprot_raw(path)

        self.assertEqual(set(result), {"A", "B", "C"})
        self.assertEqual(result["A"]["processed"], "A:1")
        self.assertEqual(result["B"]["processed"], "B:2")
        self.assertEqual(result["C"]["processed"], "C:3")

        expected_calls = [
            call("A", {"foo": 1}),
            call("B", {"foo": 2}),
            call("C", {"foo": 3}),
        ]
        self.assertEqual(mock_process.call_args_list, expected_calls)

    def test_skips_prefixes(self) -> None:
        """Ensure that records with prefixes in the SKIP_PREFIXES list are skipped."""
        payload = {
            "results": [
                {PREFIX_FIELD: "SKIPME", "x": 1},
                {PREFIX_FIELD: "KEEP", "x": 2},
            ]
        }
        path = self._write_json(payload)

        with (
            patch.object(uniprot, SKIP_PREFIXES, {"SKIPME"}),
            patch.object(uniprot, _process_record) as mock_process,
        ):
            mock_process.return_value = {"ok": True}
            out = uniprot.process_uniprot_raw(path)

        # Only the non-skipped prefix appears
        self.assertEqual(out, {"KEEP": {"ok": True}})
        mock_process.assert_called_once_with("KEEP", {"x": 2})

    def test_ignores_none_from_process_record(self) -> None:
        """Ensure that if ``_process_record`` returns None, the entry is not saved."""
        payload = {
            "results": [
                {PREFIX_FIELD: "ONE", "a": 1},
                {PREFIX_FIELD: "TWO", "b": 2},
            ]
        }
        path = self._write_json(payload)

        with (
            patch.object(uniprot, SKIP_PREFIXES, set()),
            patch.object(uniprot, _process_record) as mock_process,
        ):

            def side_effect(prefix: str, rec: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
                """Return the record is the prefix is ONE; otherwise return None."""
                return {"value": rec} if prefix == "ONE" else None

            mock_process.side_effect = side_effect
            out = uniprot.process_uniprot_raw(path)

        self.assertEqual(out, {"ONE": {"value": {"a": 1}}})
        self.assertEqual(mock_process.call_count, 2)

    def test_empty_results_returns_empty_dict(self) -> None:
        """Ensure that an empty ``results`` list returns an empty dictionary."""
        path = self._write_json({"results": []})

        with (
            patch.object(uniprot, SKIP_PREFIXES, set()),
            patch.object(uniprot, _process_record) as mock_process,
        ):
            out = uniprot.process_uniprot_raw(path)

        self.assertEqual(out, {})
        mock_process.assert_not_called()

    def test_missing_results_key_raises_key_error(self) -> None:
        """Ensure that if the ``results`` key is missing, an error is raised."""
        path = self._write_json({"no_results_here": []})
        with self.assertRaises(KeyError):
            uniprot.process_uniprot_raw(path)

    def test_missing_key_raises_key_error(self) -> None:
        """Ensure that an error is raised if the PREFIX_FIELD key is missing."""
        payload = {"results": [{"foo": "bar"}]}
        path = self._write_json(payload)

        with patch.object(uniprot, SKIP_PREFIXES, set()):
            with self.assertRaises(KeyError):
                uniprot.process_uniprot_raw(path)

    def test_process_record_receives_mutated_record(self) -> None:
        """Ensure that the PREFIX_FIELD key is removed from the record."""
        payload = {
            "results": [
                {PREFIX_FIELD: "X", "val": 1},
                {PREFIX_FIELD: "Y", "val": 2},
            ]
        }
        path = self._write_json(payload)

        captured: dict[str, dict[str, Any]] = {}

        def mock_process(prefix: str, rec: dict[str, Any]) -> dict[str, str]:
            """Create a copy of the input to check for mutation by the processing function."""
            # Store a shallow copy for inspection; mutate the original
            captured[prefix] = rec.copy()
            rec["mutated"] = True
            return {"p": prefix}

        with (
            patch.object(uniprot, SKIP_PREFIXES, set()),
            patch.object(uniprot, _process_record, side_effect=mock_process),
        ):
            out = uniprot.process_uniprot_raw(path)

        self.assertEqual(set(out), {"X", "Y"})

        # PREFIX_FIELD must be removed before the call to _process_record
        self.assertNotIn(PREFIX_FIELD, captured["X"])
        self.assertNotIn(PREFIX_FIELD, captured["Y"])

        # The mutation injected for the first record must not appear in the second
        self.assertNotIn("mutated", captured["Y"])

    def test_process_uniprot_raw_valid_data(self) -> None:
        """Test the ``process_uniprot_raw`` function with a valid dataset."""
        # include the skipped entry in the list of entries to process
        payload = [
            *[rec["original"] for rec in EXAMPLE_RECORDS.values()],
            SKIPPED_PREFIX["original"],
        ]
        path = self._write_json({"results": payload})

        expected_output = {k: v["parsed"] for k, v in EXAMPLE_RECORDS.items() if v["parsed"]}

        output = process_uniprot_raw(path)
        self.assertEqual(output, expected_output)


class TestProcessRecord(unittest.TestCase):
    """Tests for the internal ``_process_record`` function that parses the UniProt database list."""

    def test_process_record_outputs(self) -> None:
        """Test the outout of _process_record against the predicted output."""
        for record_value in EXAMPLE_RECORDS.values():
            with self.subTest(record_value=record_value):
                orig_record = deepcopy(record_value["original"])
                result = uniprot._process_record(orig_record.pop(PREFIX_FIELD), orig_record)
                self.assertEqual(result, record_value["parsed"])

    def test_debug_logged_for_leftover_fields(self) -> None:
        """Ensure that the debugger is called if there are extra fields in the entry."""
        with patch.object(uniprot.logger, "debug") as mock_debug:
            record = deepcopy(EXAMPLE_RECORDS["ValidRecord"]["original"])
            record["extra_field"] = "some value"
            result = uniprot._process_record(record.pop(PREFIX_FIELD), record)
            self.assertEqual(result, EXAMPLE_RECORDS["ValidRecord"]["parsed"])

            # The logger should have been called with a message containing "forgot something"
            mock_debug.assert_any_call("forgot something: %s", {"extra_field": "some value"})

    def test_debug_logged_for_both_format_strings(self) -> None:
        """Ensure that the debugger is called if both %s and %u are present in dbUrl."""
        with patch.object(uniprot.logger, "debug") as mock_debug:
            record = deepcopy(EXAMPLE_RECORDS["BothFmtStrs"]["original"])
            result = uniprot._process_record(record.pop(PREFIX_FIELD), record)
            self.assertEqual(result, EXAMPLE_RECORDS["BothFmtStrs"]["parsed"])
            mock_debug.assert_any_call("has both formats: %s", "https://both.org/%s/%u")

    def test_debug_logged_for_no_format_strings(self) -> None:
        """Ensure that the debugger is if there is no %s or %u in dbUrl."""
        with patch.object(uniprot.logger, "debug") as mock_debug:
            record = deepcopy(EXAMPLE_RECORDS["NoFmtStrs"]["original"])
            result = uniprot._process_record(record.pop(PREFIX_FIELD), record)
            self.assertEqual(result, EXAMPLE_RECORDS["NoFmtStrs"]["parsed"])
            mock_debug.assert_any_call("no annotation in %s", "NoFmtStrs")

    def test_debug_logged_for_has_bad_uri(self) -> None:
        """Ensure that the debugger is called for a ``has_bad_uri`` entry."""
        with patch.object(uniprot.logger, "debug") as mock_debug:
            record = deepcopy(EXAMPLE_RECORDS["EnsemblFungi"]["original"])
            result = uniprot._process_record(record.pop(PREFIX_FIELD), record)
            self.assertEqual(result, EXAMPLE_RECORDS["EnsemblFungi"]["parsed"])
            # The logger should have been called with a message containing "forgot something"
            mock_debug.assert_any_call("no annotation in %s", "EnsemblFungi")


if __name__ == "__main__":
    unittest.main()
