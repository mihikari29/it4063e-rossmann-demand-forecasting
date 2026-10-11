"""Synthetic-only tests for the approved CC-02 development partition loader."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rossmann_forecasting.analysis import seasonal_decomposition as analysis
from rossmann_forecasting.data import cc02_development as provider


def _sales_frame(
    *, start: str = "2015-01-01", days: int = 84, sales_dtype: str = "float64"
) -> pd.DataFrame:
    dates = pd.date_range(start, periods=days, freq="D")
    weekly = np.array([0.0, -32.0, 21.0, 15.0, -24.0, 39.0, -19.0])
    values = 900.0 + np.arange(days, dtype=float) * 1.7 + weekly[np.arange(days) % 7]
    sales = values.astype(sales_dtype)
    return pd.DataFrame({"Store": np.ones(days, dtype="int64"), "Date": dates, "Sales": sales})


def _fixture_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    frame: pd.DataFrame | None = None,
    manifest_updates: dict[str, object] | None = None,
    parquet_bytes: bytes | None = None,
) -> tuple[Path, provider.DevelopmentInputApproval]:
    source = _sales_frame() if frame is None else frame
    root = tmp_path / "data" / "interim" / "cc02_development"
    monkeypatch.setattr(provider, "_approved_bundle_root", lambda: root)
    bundle = root / "fixture-cc02-a"
    bundle.mkdir(parents=True)
    data_path = bundle / provider.DATA_FILENAME
    if parquet_bytes is None:
        source.to_parquet(data_path, index=False, engine="pyarrow")
    else:
        data_path.write_bytes(parquet_bytes)
    data_bytes = data_path.read_bytes()
    data_sha256 = hashlib.sha256(data_bytes).hexdigest()
    dates = pd.to_datetime(source["Date"])
    dtypes = {"Store": "int64", "Date": str(source["Date"].dtype), "Sales": "float64"}
    if "Sales" in source and str(source["Sales"].dtype) in {"int64", "float64"}:
        dtypes["Sales"] = str(source["Sales"].dtype)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "artifact_id": "fixture-cc02-a",
        "purpose": provider.PURPOSE,
        "source_lineage_reference": "fixture-lineage:synthetic-only",
        "custodian_preparation_authorization_reference": "fixture-custody:synthetic-only",
        "provider_loading_approval_reference": "fixture-provider-approval:synthetic-only",
        "preflight_reference": "fixture-preflight:synthetic-only",
        "data_file": provider.DATA_FILENAME,
        "data_sha256": data_sha256,
        "data_bytes": len(data_bytes),
        "row_count": len(source),
        "store_count": int(source["Store"].nunique()) if "Store" in source else 1,
        "columns": list(provider.SOURCE_COLUMNS),
        "dtypes": dtypes,
        "sort_order": ["Store", "Date"],
        "date_min": dates.min().date().isoformat(),
        "date_max": dates.max().date().isoformat(),
    }
    if manifest_updates:
        manifest.update(manifest_updates)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    manifest_path = bundle / provider.MANIFEST_FILENAME
    manifest_path.write_bytes(manifest_bytes)
    approval = provider.DevelopmentInputApproval(
        artifact_id="fixture-cc02-a",
        purpose=provider.PURPOSE,
        bundle_location=str(bundle.absolute()),
        data_filename=provider.DATA_FILENAME,
        manifest_filename=provider.MANIFEST_FILENAME,
        expected_data_sha256=data_sha256,
        expected_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        development_ceiling=provider.DEVELOPMENT_CEILING,
        source_lineage_reference="fixture-lineage:synthetic-only",
        custodian_preparation_authorization_reference="fixture-custody:synthetic-only",
        provider_loading_approval_reference="fixture-provider-approval:synthetic-only",
        preflight_reference="fixture-preflight:synthetic-only",
    )
    return bundle, approval


def _repin_manifest(
    bundle: Path,
    approval: provider.DevelopmentInputApproval,
    updates: dict[str, object],
) -> provider.DevelopmentInputApproval:
    path = bundle / provider.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(updates)
    content = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(content)
    return replace(approval, expected_manifest_sha256=hashlib.sha256(content).hexdigest())


def test_valid_fixture_load_is_copy_safe_and_exports_distinct_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _sales_frame()
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch, frame=source)
    loaded = provider.load_approved_development_sales(approval)

    pd.testing.assert_frame_equal(loaded.frame, source)
    assert (
        loaded.data_sha256
        == hashlib.sha256((bundle / provider.DATA_FILENAME).read_bytes()).hexdigest()
    )
    assert loaded.manifest_sha256 == approval.expected_manifest_sha256
    assert loaded.provenance.source_kind == "approved_development_only"
    assert loaded.provenance.source_id == approval.artifact_id
    assert loaded.provenance.preflight_reference == approval.preflight_reference

    mutated = loaded.frame
    mutated.loc[0, "Sales"] = -999
    assert loaded.frame.loc[0, "Sales"] == source.loc[0, "Sales"]
    assert hashlib.sha256((bundle / provider.DATA_FILENAME).read_bytes()).hexdigest() == (
        loaded.data_sha256
    )

    run = provider.decompose_approved_development_sales(approval)
    manifest_path = analysis.export_decomposition_outputs(run, tmp_path / "stl-output")
    output_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance = output_manifest["source"]
    assert provenance["preflight_reference"] == approval.preflight_reference
    assert provenance["partition_snapshot"]["data_file_bytes_sha256"] == loaded.data_sha256
    assert provenance["partition_snapshot"]["manifest_file_bytes_sha256"] == loaded.manifest_sha256
    assert provenance["authorized_in_memory_projection_sha256"] == run.input_sha256
    assert run.input_sha256 != loaded.data_sha256
    assert provenance["source_lineage_reference"] == approval.source_lineage_reference
    assert (
        provenance["custodian_preparation_authorization_reference"]
        == approval.custodian_preparation_authorization_reference
    )
    assert (
        provenance["provider_loading_approval_reference"]
        == approval.provider_loading_approval_reference
    )


def test_missing_or_invalid_binding_fails_before_any_file_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)

    def unexpected_read(*args: object, **kwargs: object) -> bytes:
        pytest.fail("file bytes were read before binding validation")

    monkeypatch.setattr(provider, "_read_approved_bytes", unexpected_read)
    invalid = [
        None,
        replace(approval, purpose="phase13_training"),
        replace(approval, preflight_reference=""),
        replace(approval, source_lineage_reference=""),
        replace(approval, provider_loading_approval_reference=""),
        replace(approval, expected_data_sha256="not-a-hash"),
        replace(approval, bundle_location=str(tmp_path / "data" / "raw" / "rossmann")),
        replace(approval, bundle_location=str(tmp_path / "data" / "interim" / "train.parquet")),
        replace(
            approval,
            bundle_location=str(tmp_path / "data" / "processed" / "features_train.parquet"),
        ),
        replace(approval, bundle_location=str(bundle.parent / ".." / "raw" / "rossmann")),
        replace(approval, artifact_id="../train"),
    ]
    for item in invalid:
        with pytest.raises(provider.DevelopmentInputError):
            provider.load_approved_development_sales(item)


def test_unauthorized_binding_never_reaches_analysis_or_source_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, approval = _fixture_bundle(tmp_path, monkeypatch)

    def unexpected_read(*args: object, **kwargs: object) -> bytes:
        pytest.fail("no fallback or unauthorized file read is permitted")

    monkeypatch.setattr(provider, "_read_approved_bytes", unexpected_read)
    monkeypatch.setattr(
        analysis,
        "decompose_development_sales",
        lambda *args, **kwargs: pytest.fail("unauthorized data reached the STL analysis"),
    )
    bad_binding = replace(
        approval, bundle_location=str(tmp_path / "data" / "interim" / "train.parquet")
    )
    with pytest.raises(provider.DevelopmentInputError, match="outside the fixed"):
        provider.decompose_approved_development_sales(bad_binding)


def test_symlink_bundle_is_rejected_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)
    held = bundle.with_name("fixture-held")
    bundle.rename(held)
    try:
        bundle.symlink_to(held, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")
    monkeypatch.setattr(
        provider,
        "_read_approved_bytes",
        lambda *args, **kwargs: pytest.fail("symlinked bundle bytes must not be read"),
    )
    with pytest.raises(provider.DevelopmentInputError, match="alias"):
        provider.load_approved_development_sales(approval)


def test_reparse_point_is_rejected_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)
    original_lstat = Path.lstat

    def reparse_bundle(path: Path):
        info = original_lstat(path)
        if path == bundle:
            return type(
                "ReparseStat",
                (),
                {
                    "st_mode": info.st_mode,
                    "st_file_attributes": getattr(info, "st_file_attributes", 0) | 0x400,
                },
            )()
        return info

    monkeypatch.setattr(Path, "lstat", reparse_bundle)
    monkeypatch.setattr(
        provider,
        "_read_approved_bytes",
        lambda *args, **kwargs: pytest.fail("reparse alias bytes must not be read"),
    )
    with pytest.raises(provider.DevelopmentInputError, match="alias"):
        provider.load_approved_development_sales(approval)


def test_modified_manifest_is_rejected_before_data_file_is_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)
    with (bundle / provider.MANIFEST_FILENAME).open("ab") as manifest:
        manifest.write(b" ")
    opened: list[str] = []
    original = provider._read_approved_bytes

    def track(path: Path, *, max_bytes: int) -> bytes:
        opened.append(path.name)
        return original(path, max_bytes=max_bytes)

    monkeypatch.setattr(provider, "_read_approved_bytes", track)
    with pytest.raises(provider.DevelopmentInputError, match="manifest SHA-256"):
        provider.load_approved_development_sales(approval)
    assert opened == [provider.MANIFEST_FILENAME]


def test_modified_data_file_is_rejected_by_exact_snapshot_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)
    data_path = bundle / provider.DATA_FILENAME
    original = data_path.read_bytes()
    data_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    with pytest.raises(provider.DevelopmentInputError, match="partition SHA-256"):
        provider.load_approved_development_sales(approval)


@pytest.mark.parametrize(
    ("manifest_updates", "message"),
    [
        ({"artifact_id": "different-artifact"}, "artifact_id"),
        ({"row_count": 7}, "row count"),
        ({"date_max": "2015-06-30"}, "date bounds"),
        ({"purpose": "phase13_training"}, "purpose"),
        ({"source_lineage_reference": "unapproved"}, "source_lineage_reference"),
        (
            {"custodian_preparation_authorization_reference": "unapproved"},
            "custodian_preparation_authorization_reference",
        ),
        (
            {"provider_loading_approval_reference": "unapproved"},
            "provider_loading_approval_reference",
        ),
    ],
)
def test_inconsistent_pinned_manifest_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_updates: dict[str, object],
    message: str,
) -> None:
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch)
    approval = _repin_manifest(bundle, approval, manifest_updates)
    with pytest.raises(provider.DevelopmentInputError, match=message):
        provider.load_approved_development_sales(approval)


def test_external_hash_mismatch_rejects_before_reading_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, approval = _fixture_bundle(tmp_path, monkeypatch)
    approval = replace(approval, expected_data_sha256="0" * 64)
    read_names: list[str] = []
    original = provider._read_approved_bytes

    def track(path: Path, *, max_bytes: int) -> bytes:
        read_names.append(path.name)
        return original(path, max_bytes=max_bytes)

    monkeypatch.setattr(provider, "_read_approved_bytes", track)
    with pytest.raises(
        provider.DevelopmentInputError, match="does not match the external approval"
    ):
        provider.load_approved_development_sales(approval)
    assert read_names == [provider.MANIFEST_FILENAME]


def test_malformed_parquet_is_rejected_after_approved_byte_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad_bytes = b"this is not a parquet file"
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch, parquet_bytes=bad_bytes)
    approval = _repin_manifest(
        bundle,
        approval,
        {"data_sha256": hashlib.sha256(bad_bytes).hexdigest(), "data_bytes": len(bad_bytes)},
    )
    approval = replace(approval, expected_data_sha256=hashlib.sha256(bad_bytes).hexdigest())
    with pytest.raises(provider.DevelopmentInputError, match="not a valid supported Parquet"):
        provider.load_approved_development_sales(approval)


@pytest.mark.parametrize(
    "frame",
    [
        _sales_frame().assign(Unexpected=1),
        _sales_frame().drop(columns=["Sales"]),
        _sales_frame().assign(Store=lambda f: f["Store"].astype("float64")),
        _sales_frame().assign(Sales=lambda f: f["Sales"].astype(str)),
        _sales_frame().assign(Date=lambda f: f["Date"].astype(str)),
    ],
    ids=["extra-column", "missing-column", "store-type", "sales-type", "date-type"],
)
def test_parquet_schema_mismatches_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, frame: pd.DataFrame
) -> None:
    _, approval = _fixture_bundle(tmp_path, monkeypatch, frame=frame)
    with pytest.raises(provider.DevelopmentInputError):
        provider.load_approved_development_sales(approval)


def test_sales_null_nonfinite_zero_and_sparse_dates_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = pd.DataFrame(
        {
            "Store": np.ones(5, dtype="int64"),
            "Date": pd.to_datetime(
                ["2015-01-01", "2015-01-02", "2015-01-04", "2015-01-05", "2015-01-06"]
            ),
            "Sales": np.array([0.0, np.nan, np.inf, -np.inf, 7.0], dtype="float64"),
        }
    )
    validated = provider.validate_development_sales_frame(frame)
    _, approval = _fixture_bundle(tmp_path, monkeypatch, frame=frame)
    loaded = provider.load_approved_development_sales(approval).frame
    assert len(validated) == len(frame)
    assert loaded.loc[0, "Sales"] == 0
    assert np.isnan(loaded.loc[1, "Sales"])
    assert np.isposinf(loaded.loc[2, "Sales"])
    assert np.isneginf(loaded.loc[3, "Sales"])
    assert pd.Timestamp("2015-01-03") not in set(loaded["Date"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True), "unique"),
        (lambda frame: frame.iloc[::-1].reset_index(drop=True), "sorted"),
        (lambda frame: frame.assign(Store=0), "positive"),
        (lambda frame: frame.assign(Store=-1), "positive"),
        (
            lambda frame: frame.assign(
                Store=pd.Series([1, None] + [1] * (len(frame) - 2), dtype="Int64")
            ),
            "int64",
        ),
        (
            lambda frame: frame.assign(Date=frame["Date"].mask(frame.index == 0, pd.NaT)),
            "cannot be null",
        ),
        (
            lambda frame: frame.assign(Date=frame["Date"] + pd.Timedelta(hours=1)),
            "midnight",
        ),
        (
            lambda frame: frame.assign(Date=frame["Date"].dt.tz_localize("UTC")),
            "timezone-naive",
        ),
        (
            lambda frame: frame.assign(Date=frame["Date"] + pd.Timedelta(days=200)),
            "development ceiling",
        ),
        (lambda frame: frame.assign(Sales=frame["Sales"].astype(bool)), "int64 or float64"),
        (
            lambda frame: frame.assign(Sales=frame["Sales"].astype(complex)),
            "int64 or float64",
        ),
        (lambda frame: frame.assign(Extra=1), "exactly Store, Date, Sales"),
        (lambda frame: frame.drop(columns=["Sales"]), "exactly Store, Date, Sales"),
    ],
)
def test_direct_frame_contract_rejects_invalid_schema_and_values(mutate, message: str) -> None:
    frame = mutate(_sales_frame(days=4))
    with pytest.raises(provider.DevelopmentInputError, match=message):
        provider.validate_development_sales_frame(frame)


def test_missing_or_late_manifest_date_bounds_fail_before_stl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frame = _sales_frame(start="2015-06-20", days=15)
    bundle, approval = _fixture_bundle(tmp_path, monkeypatch, frame=frame)
    monkeypatch.setattr(
        analysis,
        "STL",
        lambda *args, **kwargs: pytest.fail("STL must not run for protected-date input"),
    )
    with pytest.raises(provider.DevelopmentInputError, match="date_max exceeds"):
        provider.decompose_approved_development_sales(approval)
    assert bundle.exists()


def test_sales_integer_schema_is_supported_without_type_coercion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _sales_frame(days=60, sales_dtype="int64")
    _, approval = _fixture_bundle(tmp_path, monkeypatch, frame=source)
    loaded = provider.load_approved_development_sales(approval)
    assert str(loaded.frame["Sales"].dtype) == "int64"
    pd.testing.assert_frame_equal(loaded.frame, source)
