"""Focused synthetic tests for deterministic technical pilot selection."""
from __future__ import annotations

from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import socket
import tempfile
from types import MappingProxyType
import unittest
from unittest.mock import patch

import numpy as np
from astropy.io import fits

import oc3_technical_selection as cli
import oc3lib.technical_selection as stage
from oc3lib.metadata_value_semantics import PatchRowInput
from oc3lib.patch_metadata_decode import ResourceAccounting
from oc3lib.provider_physical_contracts import PRODUCTION_PHYSICAL_CONTRACTS, PhysicalRole


def patch_names() -> tuple[bytes, ...]:
    return tuple(f"{index:04d}p{index % 1000:03d}".encode("ascii") for index in range(1691))


def geometry(seed: int) -> tuple[float, float, float, float, float, float]:
    value = float(seed % 1000)
    return (value, value / 10, value - .1, value + .1, value / 10 - .1, value / 10 + .1)


def candidate(region: str, name: bytes, *, generation: str | None = None,
              grz: bool = True, corrected: bool | None = None) -> stage.Candidate:
    south = region == "south"
    return stage.Candidate(region, "DECaLS" if south else "BASS_MzLS", "DR9",
                           generation or ("9012" if south else "9011"), name, 10,
                           grz, south if corrected is None else corrected)


def make_fits(path: Path, contract, names: tuple[bytes, ...], ids: tuple[int, ...]) -> Path:
    columns = []
    for index, column in enumerate(contract.columns):
        form = column.tform; key = column.ttype.lower(); count = len(names)
        if form == "8A": values = np.asarray(names, dtype="S8")
        elif key == "brickid": values = np.asarray(ids, dtype=np.int32)
        elif key in ("release",): values = np.asarray([9012] * count, dtype=np.int16)
        elif key.startswith("nexp_"): values = np.asarray([1] * count, dtype=np.int16)
        elif form == "I": values = np.asarray([1] * count, dtype=np.int16)
        elif form == "J": values = np.asarray([100 + index] * count, dtype=np.int32)
        elif form == "6J": values = np.asarray([[0, 1, 0, 0, 0, 0]] * count, dtype=np.int32)
        elif form == "4I": values = np.asarray([[1, 2, 3, 4]] * count, dtype=np.int16)
        elif form == "4E": values = np.asarray([[1, 2, 3, 4]] * count, dtype=np.float32)
        elif form == "E": values = np.asarray([1.0] * count, dtype=np.float32)
        elif form == "D": values = np.asarray([1.0] * count, dtype=np.float64)
        elif form == "L": values = np.asarray([True] * count, dtype=bool)
        else: raise AssertionError(form)
        columns.append(fits.Column(name=column.ttype, format=form, array=values))
    plain = path if contract.compression == "identity" else path.with_suffix("")
    fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(plain)
    if contract.compression == "gzip":
        path.write_bytes(gzip.compress(plain.read_bytes(), mtime=0)); plain.unlink()
    return path


class FakeDecoder:
    root_rows = ()
    north_rows = ()
    south_rows = ()
    patch_rows = ()

    def __init__(self, accounting): self.accounting = accounting

    def decode_root(self, path, contract, observation):
        observation.cell_values_decoded += len(self.root_rows) * len(stage.ROOT_FIELDS)
        return tuple(self.root_rows)

    def decode_regional(self, path, contract, observation):
        rows = self.north_rows if contract.role is PhysicalRole.NORTH_SUMMARY else self.south_rows
        observation.cell_values_decoded += len(rows) * len(stage.REGIONAL_FIELDS)
        return tuple(rows)

    def decode_patch(self, path, contract, observation):
        observation.cell_values_decoded += len(self.patch_rows) * 3
        return tuple(self.patch_rows)


class TechnicalSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="oc3_technical_selection_")
        cls.base = Path(cls.temp.name)
        cls.paths = {}
        hashes = {}
        for role in PhysicalRole:
            path = cls.base / f"{role.value}.bin"; path.write_bytes(role.value.encode("ascii"))
            cls.paths[role] = path; hashes[role] = hashlib.sha256(path.read_bytes()).hexdigest()
        cls.names = patch_names(); cls.ids = tuple(100_000 + i for i in range(1691))
        cls.patch_rows = tuple(PatchRowInput(9012, identity, name)
                               for name, identity in zip(cls.names, cls.ids))
        cls.south_rows = tuple(stage.RegionalRow(name, identity, geometry(identity), (1, 1, 1))
                               for name, identity in zip(cls.names, cls.ids))
        cls.north_names = (b"9000m000", b"9001m001")
        cls.north_ids = (400_000, 400_001)
        cls.north_rows = tuple(stage.RegionalRow(name, identity, geometry(identity), (1, 1, 1))
                               for name, identity in zip(cls.north_names, cls.north_ids))
        all_rows = list(zip(cls.names, cls.ids)) + list(zip(cls.north_names, cls.north_ids))
        cls.root_rows = tuple(stage.RootRow(name, identity, geometry(identity))
                              for name, identity in all_rows)
        cls.inputs = stage.StageInputs(
            cls.base, cls.base, cls.paths[PhysicalRole.ROOT_SUMMARY],
            cls.paths[PhysicalRole.NORTH_SUMMARY], cls.paths[PhysicalRole.SOUTH_SUMMARY],
            cls.paths[PhysicalRole.SOUTH_PATCH_LIST], MappingProxyType(hashes),
            PRODUCTION_PHYSICAL_CONTRACTS, MappingProxyType({"synthetic": "a" * 64}), True)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def destinations(self, name: str):
        return self.base / f"{name}.csv", self.base / f"audit_{name}"

    def execute(self, name: str, *, root=None, north=None, south=None, patch_rows=None):
        class Decoder(FakeDecoder): pass
        Decoder.root_rows = self.root_rows if root is None else tuple(root)
        Decoder.north_rows = self.north_rows if north is None else tuple(north)
        Decoder.south_rows = self.south_rows if south is None else tuple(south)
        Decoder.patch_rows = self.patch_rows if patch_rows is None else tuple(patch_rows)
        csv_path, audit = self.destinations(name)
        result = stage.execute_stage(self.inputs, csv_path, audit,
                                     current_implementation="f" * 64, decoder_factory=Decoder)
        return result, csv_path, audit

    def assert_failure(self, result, code=None):
        self.assertEqual(result["terminal"]["terminal"], stage.FAILURE_TERMINAL)
        if code is not None: self.assertEqual(result["terminal"]["first_error_code"], code)

    def test_01_closed_paths_hashes_and_no_url_argument(self):
        self.assertEqual(stage.SPEC_SHA256, "781784819b6e9b8254d664d0d4d85478837c82de616a96e7ef590924f37882a8")
        self.assertEqual(stage.EXPECTED_RAW[PhysicalRole.NORTH_SUMMARY][2],
                         "2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb")
        actions = {item.dest for item in cli.parser()._actions}
        self.assertNotIn("url", actions); self.assertNotIn("execute_network", actions)

    def test_01b_production_output_paths_are_closed_before_row_access(self):
        with self.assertRaises(stage.SelectionError) as caught:
            stage.run_production(stage.ATTEMPT, stage.PATCH_EVIDENCE,
                                 self.base / "wrong.csv", stage.AUDIT_DIRECTORY)
        self.assertEqual(caught.exception.code, "TECHNICAL_SELECTION_INPUT_BINDING_FAILURE")

    def test_02_zero_network_capability(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network")), \
                patch.object(socket, "getaddrinfo", side_effect=AssertionError("dns")):
            result, _, _ = self.execute("network")
        self.assertEqual(result["aggregate"]["metrics"]["network_requests"], 0)

    def test_03_allowed_field_boundary_real_row_stride(self):
        root = self.base / "decoder_root.fits.gz"; north = self.base / "decoder_north.fits.gz"
        root_contract = replace(PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.ROOT_SUMMARY], naxis2=1)
        north_contract = replace(PRODUCTION_PHYSICAL_CONTRACTS[PhysicalRole.NORTH_SUMMARY], naxis2=1)
        make_fits(root, root_contract, (b"9002m002",), (500_000,))
        make_fits(north, north_contract, (b"9002m002",), (500_000,))
        observation = stage.SelectionObservation(); decoder = stage.TechnicalSelectiveFitsDecoder(ResourceAccounting())
        roots = decoder.decode_root(root, root_contract, observation)
        regional = decoder.decode_regional(north, north_contract, observation)
        self.assertEqual((len(roots), len(regional)), (1, 1))
        self.assertEqual(observation.decoded_fields["ROOT"], stage.ROOT_FIELDS)
        self.assertEqual(observation.decoded_fields["NORTH"], stage.REGIONAL_FIELDS)
        self.assertEqual(observation.unexpected_field_observation_count, 0)

    def test_04_south_eligibility_exact(self):
        self.assertTrue(stage.candidate_is_eligible(candidate("south", self.names[0])))
        self.assertFalse(stage.candidate_is_eligible(candidate("south", self.names[0], corrected=False)))

    def test_05_north_eligibility_exact(self):
        self.assertTrue(stage.candidate_is_eligible(candidate("north", self.north_names[0])))
        self.assertFalse(stage.candidate_is_eligible(candidate("north", self.north_names[0], grz=False)))

    def test_06_exact_patch_membership_excludes_nonmember(self):
        extra_name=b"8000p000"; extra_id=500_010
        roots=self.root_rows+(stage.RootRow(extra_name,extra_id,geometry(extra_id)),)
        south=self.south_rows+(stage.RegionalRow(extra_name,extra_id,geometry(extra_id),(1,1,1)),)
        result,_,_=self.execute("patchmember",root=roots,south=south)
        metrics=result["aggregate"]["metrics"]
        self.assertEqual((metrics["eligible_south_count"],metrics["south_patch_excluded"]),(1691,1))

    def test_07_grz_exclusion_is_technical(self):
        rows=list(self.north_rows); rows[1]=replace(rows[1],nexp=(1,0,1))
        result,_,_=self.execute("grz",north=rows)
        self.assertEqual((result["aggregate"]["metrics"]["eligible_north_count"],
                          result["aggregate"]["metrics"]["north_grz_excluded"]),(1,1))

    def test_08_generation_exclusion(self):
        self.assertFalse(stage.candidate_is_eligible(candidate("south",self.names[0],generation="9010")))
        self.assertFalse(stage.candidate_is_eligible(candidate("north",self.north_names[0],generation="9012")))

    def test_09_join_inconsistency_fails_whole_stage(self):
        rows=list(self.north_rows); rows[0]=replace(rows[0],geometry=(9.,9.,9.,9.,9.,9.))
        result,csv_path,_=self.execute("join",north=rows)
        self.assert_failure(result,"TECHNICAL_SELECTION_JOIN_FAILURE"); self.assertFalse(csv_path.exists())

    def test_10_deterministic_sha_ordering(self):
        values=(candidate("north",b"9002m002"),candidate("north",b"9003m003"))
        ordered,digest,ties=stage.order_candidates(values)
        expected=tuple(sorted(values,key=lambda item:(stage.selection_hash(item),item.brickname)))
        self.assertEqual((ordered,digest,ties),(expected,digest,0)); self.assertEqual(len(digest),64)

    def test_11_provider_row_permutation_invariance(self):
        first=stage.order_candidates(tuple(candidate("north",name) for name in self.north_names))
        second=stage.order_candidates(tuple(candidate("north",name) for name in reversed(self.north_names)))
        self.assertEqual(first,second)

    def test_12_ascii_tie_break(self):
        values=(candidate("north",b"9003m003"),candidate("north",b"9002m002"))
        ordered,_,ties=stage.order_candidates(values,hasher=lambda unused:"0"*64)
        self.assertEqual(tuple(item.brickname for item in ordered),(b"9002m002",b"9003m003")); self.assertEqual(ties,1)

    def test_13_missing_south_fails(self):
        rows=tuple(replace(row,nexp=(0,1,1)) for row in self.south_rows)
        result,csv_path,_=self.execute("nosouth",south=rows)
        self.assert_failure(result,"TECHNICAL_SELECTION_ELIGIBILITY_FAILURE"); self.assertFalse(csv_path.exists())

    def test_14_missing_north_fails(self):
        rows=tuple(replace(row,nexp=(1,1,0)) for row in self.north_rows)
        result,csv_path,_=self.execute("nonorth",north=rows)
        self.assert_failure(result,"TECHNICAL_SELECTION_ELIGIBILITY_FAILURE"); self.assertFalse(csv_path.exists())

    def test_15_distinct_brick_requirement(self):
        chosen=self.names[0]; identity=self.ids[0]
        south=tuple(replace(row,nexp=(1,1,1) if row.brickname==chosen else (0,1,1)) for row in self.south_rows)
        north=(stage.RegionalRow(chosen,identity,geometry(identity),(1,1,1)),)
        result,csv_path,_=self.execute("distinct",north=north,south=south)
        self.assert_failure(result,"TECHNICAL_SELECTION_DISTINCT_BRICKS_FAILURE"); self.assertFalse(csv_path.exists())

    def test_16_exactly_two_output_rows_and_region_order(self):
        result,csv_path,_=self.execute("rows")
        lines=csv_path.read_text().splitlines()
        self.assertEqual(len(lines),3); self.assertTrue(lines[1].startswith("south,")); self.assertTrue(lines[2].startswith("north,"))
        self.assertEqual(result["aggregate"]["metrics"]["selected_count"],2)

    def test_17_exact_csv_schema_and_canonicalization(self):
        _,csv_path,_=self.execute("csv")
        raw=csv_path.read_bytes(); lines=raw.decode("ascii").splitlines()
        self.assertEqual(lines[0],stage.CSV_HEADER.rstrip("\n")); self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"),3); self.assertNotIn(b'"',raw)
        self.assertTrue(all(line.endswith(",true,true,"+stage.STAGE_ID) for line in lines[1:]))

    def test_18_publication_conflict_fails_closed(self):
        _,csv_path,audit=self.execute("conflict")
        with self.assertRaises(stage.SelectionError) as caught:
            stage.execute_stage(self.inputs,csv_path,audit,current_implementation="f"*64,decoder_factory=FakeDecoder)
        self.assertEqual(caught.exception.code,"TECHNICAL_SELECTION_LOCAL_STATE_CONFLICT")

    def test_19_no_candidate_list_persistence(self):
        _,_,audit=self.execute("nocandidates")
        self.assertEqual({item.name for item in audit.iterdir()},set(stage.AUDIT_FILES))
        body=b"".join(item.read_bytes() for item in audit.iterdir())
        self.assertNotIn(b"candidate_list",body); self.assertNotIn(b"ranking",body)

    def test_20_no_row_level_leakage_to_audit(self):
        result,csv_path,audit=self.execute("firewall")
        names=tuple(line.split(",")[1].encode("ascii") for line in csv_path.read_text().splitlines()[1:])
        audit_body=b"".join(item.read_bytes() for item in audit.iterdir())
        self.assertTrue(all(name not in audit_body for name in names))
        self.assertEqual(result["aggregate"]["metrics"]["row_level_leakage_count"],0)

    def test_21_success_terminal(self):
        result,_,_=self.execute("success")
        self.assertEqual(result["terminal"],{"first_error_code":None,"stage_id":stage.STAGE_ID,
                         "successful":True,"terminal":stage.SUCCESS_TERMINAL})

    def test_22_failure_terminal_and_audit_only(self):
        rows=tuple(replace(row,nexp=(0,0,0)) for row in self.north_rows)
        result,csv_path,audit=self.execute("failure",north=rows)
        self.assert_failure(result); self.assertFalse(csv_path.exists())
        terminal=json.loads((audit/"TECHNICAL_SELECTION_TERMINAL.json").read_text())
        self.assertEqual(terminal["terminal"],stage.FAILURE_TERMINAL)


if __name__ == "__main__": unittest.main()
