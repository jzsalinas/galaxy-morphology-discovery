"""Focused synthetic tests for PATCH_METADATA_DECODE_ONLY."""
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

import oc3_patch_metadata_decode as cli
import oc3lib.patch_metadata_decode as stage
from oc3lib.metadata_value_semantics import JoinRowInput, PatchRowInput
from oc3lib.provider_physical_contracts import (
    FrozenColumn, PRODUCTION_PHYSICAL_CONTRACTS, PhysicalRole,
)


def names(count: int) -> tuple[bytes, ...]:
    return tuple(f"{index:04d}p{index % 1000:03d}".encode("ascii")
                 for index in range(count))


def make_fits(path: Path, contract, row_names: tuple[bytes, ...], ids: tuple[int, ...],
              *, releases: tuple[int, ...] | None = None) -> Path:
    count = len(row_names); columns = []
    for index, column in enumerate(contract.columns):
        form = column.tform; key = column.ttype.lower()
        if form == "8A": values = np.asarray(row_names, dtype="S8")
        elif key == "release": values = np.asarray(releases or (9012,) * count, dtype=np.int16)
        elif key == "brickid": values = np.asarray(ids, dtype=np.int32)
        elif form == "I": values = np.asarray([1] * count, dtype=np.int16)
        elif form == "J": values = np.asarray([1000 + index] * count, dtype=np.int32)
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
    patch_rows = ()
    root_rows = ()
    south_rows = ()

    def __init__(self, accounting): self.accounting = accounting

    def decode_patch(self, path, contract, observation):
        observation.opaque_bytes_transited = len(self.patch_rows) * 14
        observation.cell_values_decoded = len(self.patch_rows) * 3
        return tuple(self.patch_rows)

    def decode_references(self, path, contract):
        return tuple(self.root_rows if contract.role is PhysicalRole.ROOT_SUMMARY
                     else self.south_rows)


class PatchMetadataDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="oc3_patch_decode_")
        cls.root_dir = Path(cls.temp.name)
        cls.attempt = cls.root_dir / "attempt"; cls.attempt.mkdir()
        cls.row_names = names(1691)
        cls.ids = tuple(100_000 + index for index in range(1691))
        contracts = {}
        paths = {}
        for role, relative in (
            (PhysicalRole.SOUTH_PATCH_LIST, stage.PATCH_RELATIVE),
            (PhysicalRole.ROOT_SUMMARY, stage.ROOT_RELATIVE),
            (PhysicalRole.SOUTH_SUMMARY, stage.SOUTH_RELATIVE),
        ):
            contract = replace(PRODUCTION_PHYSICAL_CONTRACTS[role], naxis2=1691)
            path = cls.attempt / relative; path.parent.mkdir(parents=True, exist_ok=True)
            make_fits(path, contract, cls.row_names, cls.ids)
            contracts[role] = contract; paths[role] = path
        hashes = {role: hashlib.sha256(path.read_bytes()).hexdigest()
                  for role, path in paths.items()}
        cls.contracts = MappingProxyType(contracts)
        cls.paths = paths
        cls.inputs = stage.StageInputs(
            attempt=cls.attempt, patch=paths[PhysicalRole.SOUTH_PATCH_LIST],
            root=paths[PhysicalRole.ROOT_SUMMARY], south=paths[PhysicalRole.SOUTH_SUMMARY],
            expected_hashes=MappingProxyType(hashes), contracts=cls.contracts,
            source_bootstrap_implementation="b" * 64,
            source_authorization_sha256="a" * 64, source_environment="e" * 64,
            source_ledger_identity="l" * 64, synthetic_only=True,
        )
        cls.patch_rows = tuple(PatchRowInput(9012, brickid, name)
                               for name, brickid in zip(cls.row_names, cls.ids))
        cls.join_rows = tuple(JoinRowInput(name, brickid)
                              for name, brickid in zip(cls.row_names, cls.ids))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def output(self, name: str) -> Path:
        return self.root_dir / f"output_{name}"

    def execute_fake(self, name: str, *, patch_rows=None, root_rows=None, south_rows=None):
        class Decoder(FakeDecoder): pass
        Decoder.patch_rows = self.patch_rows if patch_rows is None else tuple(patch_rows)
        Decoder.root_rows = self.join_rows if root_rows is None else tuple(root_rows)
        Decoder.south_rows = self.join_rows if south_rows is None else tuple(south_rows)
        return stage.execute_stage(self.inputs, self.output(name), current_implementation="f" * 64,
                                   decoder_factory=Decoder)

    def assert_failed(self, result, code: str):
        self.assertEqual(result["terminal"]["terminal"], stage.FAILURE_TERMINAL)
        self.assertEqual(result["terminal"]["first_error_code"], code)

    def test_01_closed_production_paths_hashes_and_no_url_arguments(self):
        self.assertEqual(stage.ATTEMPT, Path("/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001"))
        self.assertEqual(stage.EXPECTED_RAW[PhysicalRole.SOUTH_PATCH_LIST][1:],
                         (31680, "f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6"))
        actions={item.dest for item in cli.parser()._actions}
        self.assertNotIn("url", actions); self.assertNotIn("execute_network", actions)

    def test_02_dry_run_is_non_mutating_and_closed(self):
        with patch.object(stage, "ATTEMPT", self.attempt), patch.object(stage, "OUTPUT", self.output("dry")):
            result=stage.dry_run(self.attempt,self.output("dry"))
        self.assertEqual(result["network_requests"],0)
        self.assertFalse(self.output("dry").exists())

    def test_03_real_selective_decoder_observes_three_fields_and_opaque_transit(self):
        result=stage.execute_stage(self.inputs,self.output("real"),current_implementation="f"*64)
        observed=result["aggregate"]["decoder_observation"]
        self.assertEqual(observed["decoded_fields"],["RELEASE","BRICKID","BRICKNAME"])
        self.assertEqual(observed["cell_values_decoded"],1691*3)
        self.assertGreater(observed["opaque_bytes_transited"],0)
        self.assertEqual(observed["unexpected_field_observation_count"],0)
        self.assertEqual(result["terminal"]["terminal"],stage.SUCCESS_TERMINAL)

    def test_04_fourth_field_trips_before_observation(self):
        patch_contract=self.contracts[PhysicalRole.SOUTH_PATCH_LIST]
        changed=replace(patch_contract,columns=patch_contract.columns+(FrozenColumn("EXTRA","J"),),naxis1=18)
        contracts=dict(self.contracts); contracts[PhysicalRole.SOUTH_PATCH_LIST]=changed
        inputs=replace(self.inputs,contracts=MappingProxyType(contracts))
        result=stage.execute_stage(inputs,self.output("fourth"),current_implementation="f"*64)
        self.assert_failed(result,"PATCH_FIELD_BOUNDARY_FAILURE")
        self.assertEqual(result["aggregate"]["decoder_observation"]["unexpected_field_observation_count"],0)
        self.assertEqual(result["aggregate"]["decoder_observation"]["field_boundary_tripwire_count"],1)

    def test_05_success_counts_and_uniqueness(self):
        result=self.execute_fake("success"); metrics=result["aggregate"]["metrics"]
        self.assertEqual((metrics["row_count"],metrics["valid_row_count"],metrics["release_valid_count"]),(1691,1691,1691))
        self.assertEqual((metrics["unique_BRICKNAME_count"],metrics["unique_BRICKID_count"],metrics["unique_pair_count"]),(1691,1691,1691))

    def test_06_cardinality_1690_fails(self):
        result=self.execute_fake("1690",patch_rows=self.patch_rows[:-1])
        self.assert_failed(result,"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_07_cardinality_1692_fails(self):
        result=self.execute_fake("1692",patch_rows=self.patch_rows+(PatchRowInput(9012,999999,b"9999p999"),))
        self.assert_failed(result,"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_08_release_mismatch_fails(self):
        rows=list(self.patch_rows); rows[0]=PatchRowInput(9010,rows[0].brickid,rows[0].brickname)
        self.assert_failed(self.execute_fake("release",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_09_brickname_failure(self):
        rows=list(self.patch_rows); rows[0]=PatchRowInput(9012,rows[0].brickid,b"BAD     ")
        self.assert_failed(self.execute_fake("badname",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_10_brickid_int32_failure(self):
        rows=list(self.patch_rows); rows[0]=PatchRowInput(9012,2**31,rows[0].brickname)
        self.assert_failed(self.execute_fake("badid",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_11_brickname_uniqueness_failure(self):
        rows=list(self.patch_rows); rows[1]=PatchRowInput(9012,rows[1].brickid,rows[0].brickname)
        self.assert_failed(self.execute_fake("dupname",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_12_brickid_uniqueness_failure(self):
        rows=list(self.patch_rows); rows[1]=PatchRowInput(9012,rows[0].brickid,rows[1].brickname)
        self.assert_failed(self.execute_fake("dupid",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_13_identity_pair_duplicate_is_rejected(self):
        rows=list(self.patch_rows); rows[1]=rows[0]
        self.assert_failed(self.execute_fake("duppair",patch_rows=rows),"PATCH_VALUE_SEMANTICS_FAILURE")

    def test_14_root_missing_multiplicity_and_mismatch(self):
        self.assert_failed(self.execute_fake("rootmissing",root_rows=self.join_rows[1:]),"PATCH_RELATIONAL_FAILURE")
        self.assert_failed(self.execute_fake("rootmulti",root_rows=self.join_rows+(self.join_rows[0],)),"PATCH_RELATIONAL_FAILURE")
        rows=list(self.join_rows); rows[0]=JoinRowInput(rows[0].brickname,rows[0].brickid+1)
        self.assert_failed(self.execute_fake("rootmismatch",root_rows=rows),"PATCH_RELATIONAL_FAILURE")

    def test_15_south_missing_multiplicity_and_mismatch(self):
        self.assert_failed(self.execute_fake("southmissing",south_rows=self.join_rows[1:]),"PATCH_RELATIONAL_FAILURE")
        self.assert_failed(self.execute_fake("southmulti",south_rows=self.join_rows+(self.join_rows[0],)),"PATCH_RELATIONAL_FAILURE")
        rows=list(self.join_rows); rows[0]=JoinRowInput(rows[0].brickname,rows[0].brickid+1)
        self.assert_failed(self.execute_fake("southmismatch",south_rows=rows),"PATCH_RELATIONAL_FAILURE")

    def test_16_exact_join_counters(self):
        metrics=self.execute_fake("joins")["aggregate"]["metrics"]
        self.assertEqual((metrics["exact_ROOT_matches"],metrics["exact_SOUTH_matches"]),(1691,1691))
        for key in ("missing_from_ROOT","missing_from_SOUTH","multiplicity_failures",
                    "brickid_mismatches","brickname_mismatches","ambiguous_joins"):
            self.assertEqual(metrics[key],0)

    def test_17_outputs_have_closed_names_and_no_row_values(self):
        output=self.output("leak"); result=self.execute_fake("leak")
        self.assertEqual({item.name for item in output.iterdir()},set(stage.OUTPUT_FILES))
        body=b"".join(item.read_bytes() for item in output.iterdir())
        self.assertNotIn(self.row_names[0],body)
        self.assertNotIn(str(self.ids[0]).encode(),body)
        self.assertEqual(result["aggregate"]["metrics"]["output_row_level_leakage_count"],0)

    def test_18_failure_outputs_are_aggregate_only(self):
        output=self.output("failureout")
        result=self.execute_fake("failureout",patch_rows=self.patch_rows[:-1])
        terminal=json.loads((output/"PATCH_DECODE_TERMINAL.json").read_text())
        self.assertEqual(terminal["terminal"],stage.FAILURE_TERMINAL)
        self.assertEqual(result["terminal"]["successful"],False)

    def test_19_resource_and_output_limits(self):
        output=self.output("limits"); result=self.execute_fake("limits")
        total=sum(item.stat().st_size for item in output.iterdir())
        self.assertLessEqual(total,stage.CAPS["output_bytes"])
        self.assertLessEqual(result["aggregate"]["local_io_bytes"],stage.CAPS["local_io_bytes"])
        self.assertEqual(result["aggregate"]["metrics"]["network_requests"],0)
        self.assertEqual(result["aggregate"]["metrics"]["network_bytes"],0)

    def test_20_no_network_capability_is_exercised(self):
        with patch.object(socket,"socket",side_effect=AssertionError("network")), \
                patch.object(socket,"create_connection",side_effect=AssertionError("network")):
            result=self.execute_fake("nonetwork")
        self.assertEqual(result["terminal"]["terminal"],stage.SUCCESS_TERMINAL)

    def test_21_output_directory_is_single_use(self):
        output=self.output("single"); self.execute_fake("single")
        with self.assertRaises(stage.PatchDecodeError) as caught:
            self.execute_fake("single")
        self.assertEqual(caught.exception.code,"PATCH_LOCAL_STATE_CONFLICT")


if __name__ == "__main__": unittest.main()
