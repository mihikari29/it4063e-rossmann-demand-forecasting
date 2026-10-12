"""Synthetic-only tests for the separately gated CC-02 custodian execution bridge."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import stat
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from rossmann_forecasting.analysis import seasonal_decomposition as analysis
from rossmann_forecasting.data import cc02_custodian_execution as execution
from rossmann_forecasting.data import cc02_development as provider
from rossmann_forecasting.data import cc02_preparation as preparation


def _synthetic_source() -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(preparation.EXPECTED_HEADER)
    start = datetime(2015, 1, 1)
    for index in range(84):
        day = start + timedelta(days=index)
        sales = 900 + index * 2 + (index % 7) * 13
        writer.writerow([1, day.isoweekday(), day.date().isoformat(), sales, 10, 1, 0, 0, 0])
    # Synthetic protected-date canary: classification uses Date before numeric projection.
    writer.writerow(["invalid-store", 1, "2015-07-04", "protected-canary", 0, 1, 0, 0, 0])
    return output.getvalue().encode("utf-8")


def _authorization(
    source: bytes, *, execution_id: str | None = None
) -> execution.CustodianExecutionAuthorization:
    execution_id = execution_id or str(uuid.uuid4())
    evidences = {
        "source_access_approval": b"synthetic-source-access-approval",
        "custody_record": b"synthetic-custody-record",
        "preparation_approval": b"synthetic-preparation-approval",
    }
    return execution.CustodianExecutionAuthorization(
        execution_id=execution_id,
        custodian_name="Synthetic Fixture Custodian",
        windows_user="fixture-user",
        host_name="fixture-host",
        valid_until_utc="2099-01-01T00:00:00Z",
        execution_commit="a" * 40,
        lock_sha256="b" * 64,
        source_path=preparation.EXPECTED_SOURCE_PATH.as_posix(),
        expected_source_bytes=len(source),
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        artifact_id="fixture-cc02-execution",
        source_lineage_reference="synthetic-source-access-record",
        custodian_preparation_authorization_reference="synthetic-preparation-record",
        provider_loading_approval_reference="synthetic-provider-record:PENDING",
        preflight_reference="synthetic-preflight-record:PENDING",
        evidence={
            "source_access_approval": execution.EvidenceIdentity(
                "synthetic-source-access-record",
                hashlib.sha256(evidences["source_access_approval"]).hexdigest(),
            ),
            "custody_record": execution.EvidenceIdentity(
                "synthetic-custody-record", hashlib.sha256(evidences["custody_record"]).hexdigest()
            ),
            "preparation_approval": execution.EvidenceIdentity(
                "synthetic-preparation-record",
                hashlib.sha256(evidences["preparation_approval"]).hexdigest(),
            ),
        },
    )


def _runtime() -> dict[str, object]:
    return {
        "code_revision": "a" * 40,
        "code_worktree_dirty": False,
        "uv_lock_sha256": "b" * 64,
    }


def _write_evidence(root: Path, authorization: execution.CustodianExecutionAuthorization) -> None:
    folder = root / authorization.execution_id
    folder.mkdir(parents=True, exist_ok=True)
    contents = {
        "source_access_approval": b"synthetic-source-access-approval",
        "custody_record": b"synthetic-custody-record",
        "preparation_approval": b"synthetic-preparation-approval",
    }
    for key, filename in execution._EVIDENCE_NAMES.items():
        (folder / filename).write_bytes(contents[key])


def _run_synthetic(
    tmp_path: Path,
    source: bytes,
    authorization: execution.CustodianExecutionAuthorization,
    *,
    reader,
    bundle_root: Path | None = None,
    preparation_receipt_root: Path | None = None,
) -> preparation.PreparationResult:
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)
    return execution._execute_authorized_snapshot(
        authorization,
        authorization_bytes=b"synthetic-only-authorization-packet",
        evidence_root=evidence_root,
        receipt_root=tmp_path / "execution-receipts",
        bundle_root=bundle_root or tmp_path / "data" / "interim" / "cc02_development",
        preparation_receipt_root=preparation_receipt_root
        or tmp_path / "reports" / "generated" / "cc02_custodian",
        source_reader=reader,
        runtime=_runtime(),
        windows_user="fixture-user",
        host_name="fixture-host",
        now=datetime(2026, 10, 12, tzinfo=UTC),
    )


def test_structured_packet_requires_exact_documented_source_identity() -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    packet = {
        "schema_version": 1,
        "execution_id": authorization.execution_id,
        "custodian": {
            "name": authorization.custodian_name,
            "windows_user": authorization.windows_user,
            "host_name": authorization.host_name,
        },
        "valid_until_utc": authorization.valid_until_utc,
        "procedure": {
            "commit": authorization.execution_commit,
            "lock_sha256": authorization.lock_sha256,
        },
        "source_snapshot": {
            "path": authorization.source_path,
            "bytes": authorization.expected_source_bytes,
            "sha256": authorization.expected_source_sha256,
        },
        "artifact_id": authorization.artifact_id,
        "source_lineage_reference": authorization.source_lineage_reference,
        "custodian_preparation_authorization_reference": (
            authorization.custodian_preparation_authorization_reference
        ),
        "provider_loading_approval_reference": authorization.provider_loading_approval_reference,
        "preflight_reference": authorization.preflight_reference,
        "evidence": {
            key: {"record_id": identity.record_id, "sha256": identity.sha256}
            for key, identity in authorization.evidence.items()
        },
    }
    content = json.dumps(packet).encode("utf-8")
    parsed = execution._parse_authorization(content, require_documented_source=False)
    assert parsed.expected_source_sha256 == hashlib.sha256(source).hexdigest()
    with pytest.raises(execution.CustodianExecutionError, match="documented Rossmann snapshot"):
        execution._parse_authorization(content, require_documented_source=True)


def test_authorized_synthetic_snapshot_prepares_once_and_stops_before_provider_or_stl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    calls: list[str] = []
    monkeypatch.setattr(
        provider,
        "load_approved_development_sales",
        lambda *args, **kwargs: pytest.fail("custodian preparation must not load the provider"),
    )
    monkeypatch.setattr(
        analysis,
        "decompose_development_sales",
        lambda *args, **kwargs: pytest.fail("custodian preparation must not run STL"),
    )

    result = _run_synthetic(
        tmp_path,
        source,
        authorization,
        reader=lambda: calls.append("synthetic snapshot read") or source,
    )

    assert calls == ["synthetic snapshot read"]
    assert result.row_count == 84
    assert result.data_bytes > 0
    manifest = json.loads((result.bundle_path / preparation.MANIFEST_FILENAME).read_text())
    assert set(manifest) == preparation._MANIFEST_KEYS
    assert manifest["columns"] == ["Store", "Date", "Sales"]
    assert manifest["date_max"] == "2015-03-25"
    assert manifest["provider_loading_approval_reference"] == "synthetic-provider-record:PENDING"
    assert manifest["preflight_reference"] == "synthetic-preflight-record:PENDING"
    preparation_record = json.loads(result.receipt_path.read_bytes())
    assert preparation_record["designation"] == provider.PREPARATION_RECORD_DESIGNATION
    marker = tmp_path / "execution-receipts" / f"{authorization.execution_id}.json"
    assert json.loads(marker.read_text())["designation"].startswith("one-use")

    with pytest.raises(execution.CustodianExecutionError, match="already consumed"):
        _run_synthetic(
            tmp_path,
            source,
            authorization,
            reader=lambda: pytest.fail("consumed authorization must fail before source access"),
        )


@pytest.mark.parametrize("missing", ["preparation_approval", "custody_record"])
def test_missing_preparation_or_custody_evidence_fails_before_source_reader(
    tmp_path: Path, missing: str
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)
    (evidence_root / authorization.execution_id / execution._EVIDENCE_NAMES[missing]).unlink()

    with pytest.raises(
        execution.CustodianExecutionError, match=f"{missing} evidence could not be read"
    ):
        execution._execute_authorized_snapshot(
            authorization,
            authorization_bytes=b"synthetic-only-authorization-packet",
            evidence_root=evidence_root,
            receipt_root=tmp_path / "execution-receipts",
            bundle_root=tmp_path / "bundle",
            preparation_receipt_root=tmp_path / "prep-receipts",
            source_reader=lambda: pytest.fail("missing evidence must fail before source access"),
            runtime=_runtime(),
            windows_user="fixture-user",
            host_name="fixture-host",
            now=datetime(2026, 10, 12, tzinfo=UTC),
        )
    assert not (tmp_path / "execution-receipts").exists()


def test_runtime_and_identity_failures_do_not_read_synthetic_source(tmp_path: Path) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)

    with pytest.raises(execution.CustodianExecutionError, match="current Windows account"):
        execution._execute_authorized_snapshot(
            authorization,
            authorization_bytes=b"synthetic-only-authorization-packet",
            evidence_root=evidence_root,
            receipt_root=tmp_path / "execution-receipts",
            bundle_root=tmp_path / "bundle",
            preparation_receipt_root=tmp_path / "prep-receipts",
            source_reader=lambda: pytest.fail("wrong custodian must fail before source access"),
            runtime=_runtime(),
            windows_user="different-user",
            host_name="fixture-host",
            now=datetime(2026, 10, 12, tzinfo=UTC),
        )

    with pytest.raises(preparation.PreparationError, match="SHA-256"):
        _run_synthetic(
            tmp_path / "wrong-source",
            source,
            authorization,
            reader=lambda: bytes([source[0] ^ 1]) + source[1:],
        )


@pytest.mark.parametrize(
    "case",
    [
        "existing-bundle",
        "existing-preparation-receipt",
        "bundle-root-file",
        "preparation-receipt-root-file",
        "file-ancestor",
        "inaccessible-root",
        "traversal-root",
    ],
)
def test_invalid_output_destinations_fail_before_source_or_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)
    bundle_root = tmp_path / "bundle-root"
    preparation_receipt_root = tmp_path / "receipt-root"
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("preserve-me", encoding="utf-8")
    expected_path: Path

    if case == "existing-bundle":
        expected_path = bundle_root / authorization.artifact_id
        expected_path.mkdir(parents=True)
        (expected_path / "sentinel.txt").write_text("preserve-bundle", encoding="utf-8")
    elif case == "existing-preparation-receipt":
        expected_path = preparation_receipt_root / authorization.artifact_id
        expected_path.mkdir(parents=True)
        (expected_path / "sentinel.txt").write_text("preserve-receipt", encoding="utf-8")
    elif case == "bundle-root-file":
        expected_path = bundle_root
        bundle_root.write_text("preserve-root", encoding="utf-8")
    elif case == "preparation-receipt-root-file":
        expected_path = preparation_receipt_root
        preparation_receipt_root.write_text("preserve-root", encoding="utf-8")
    elif case == "file-ancestor":
        expected_path = tmp_path / "not-a-directory"
        expected_path.write_text("preserve-ancestor", encoding="utf-8")
        bundle_root = expected_path / "child" / "bundle-root"
    elif case == "inaccessible-root":
        expected_path = bundle_root
        original_lstat = Path.lstat

        def inaccessible(path: Path):
            if path == expected_path:
                raise PermissionError("synthetic private path detail")
            return original_lstat(path)

        monkeypatch.setattr(Path, "lstat", inaccessible)
    else:
        expected_path = tmp_path
        bundle_root = tmp_path / ".." / "traversal-root"

    reads: list[bytes] = []
    with pytest.raises(execution.CustodianExecutionError) as failure:
        execution._execute_authorized_snapshot(
            authorization,
            authorization_bytes=b"synthetic-only-authorization-packet",
            evidence_root=evidence_root,
            receipt_root=tmp_path / "execution-receipts",
            bundle_root=bundle_root,
            preparation_receipt_root=preparation_receipt_root,
            source_reader=lambda: reads.append(source) or source,
            runtime=_runtime(),
            windows_user="fixture-user",
            host_name="fixture-host",
            now=datetime(2026, 10, 12, tzinfo=UTC),
        )

    assert reads == []
    assert not (tmp_path / "execution-receipts" / f"{authorization.execution_id}.json").exists()
    assert unrelated.read_text(encoding="utf-8") == "preserve-me"
    assert str(tmp_path) not in str(failure.value)
    if case == "existing-bundle":
        assert (expected_path / "sentinel.txt").read_text(encoding="utf-8") == "preserve-bundle"
    elif case == "existing-preparation-receipt":
        assert (expected_path / "sentinel.txt").read_text(encoding="utf-8") == "preserve-receipt"
    elif case in {"bundle-root-file", "preparation-receipt-root-file", "file-ancestor"}:
        assert expected_path.read_text(encoding="utf-8").startswith("preserve-")


@pytest.mark.parametrize("dangling", [False, True])
@pytest.mark.parametrize("target_root", ["bundle", "receipt"])
def test_output_symlink_alias_fails_before_source_or_marker(
    tmp_path: Path, dangling: bool, target_root: str
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)
    bundle_root = tmp_path / "bundle-root"
    preparation_receipt_root = tmp_path / "receipt-root"
    root = bundle_root if target_root == "bundle" else preparation_receipt_root
    destination = root / authorization.artifact_id
    destination.parent.mkdir(parents=True)
    target = tmp_path / "symlink-target"
    if not dangling:
        target.mkdir()
    try:
        destination.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")

    reads: list[bytes] = []
    with pytest.raises(execution.CustodianExecutionError, match="cannot be inspected safely"):
        execution._execute_authorized_snapshot(
            authorization,
            authorization_bytes=b"synthetic-only-authorization-packet",
            evidence_root=evidence_root,
            receipt_root=tmp_path / "execution-receipts",
            bundle_root=bundle_root,
            preparation_receipt_root=preparation_receipt_root,
            source_reader=lambda: reads.append(source) or source,
            runtime=_runtime(),
            windows_user="fixture-user",
            host_name="fixture-host",
            now=datetime(2026, 10, 12, tzinfo=UTC),
        )
    assert reads == []
    assert destination.is_symlink()
    assert not (tmp_path / "execution-receipts" / f"{authorization.execution_id}.json").exists()


@pytest.mark.parametrize("target_root", ["bundle", "receipt"])
def test_output_reparse_alias_report_fails_before_source_or_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target_root: str
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    evidence_root = tmp_path / "evidence"
    _write_evidence(evidence_root, authorization)
    bundle_root = tmp_path / "bundle-root"
    preparation_receipt_root = tmp_path / "receipt-root"
    root = bundle_root if target_root == "bundle" else preparation_receipt_root
    destination = root / authorization.artifact_id
    original_lstat = Path.lstat

    def report_reparse(path: Path):
        if path == destination:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            )
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", report_reparse)
    reads: list[bytes] = []
    with pytest.raises(execution.CustodianExecutionError, match="cannot be inspected safely"):
        execution._execute_authorized_snapshot(
            authorization,
            authorization_bytes=b"synthetic-only-authorization-packet",
            evidence_root=evidence_root,
            receipt_root=tmp_path / "execution-receipts",
            bundle_root=bundle_root,
            preparation_receipt_root=preparation_receipt_root,
            source_reader=lambda: reads.append(source) or source,
            runtime=_runtime(),
            windows_user="fixture-user",
            host_name="fixture-host",
            now=datetime(2026, 10, 12, tzinfo=UTC),
        )
    assert reads == []
    assert not (tmp_path / "execution-receipts" / f"{authorization.execution_id}.json").exists()


def test_destination_appearing_after_preflight_is_rejected_by_publication_guard(
    tmp_path: Path,
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    bundle_root = tmp_path / "bundle-root"
    destination = bundle_root / authorization.artifact_id
    reads: list[bytes] = []

    def create_racing_destination() -> bytes:
        reads.append(source)
        destination.mkdir(parents=True)
        (destination / "sentinel.txt").write_text("preserve-race", encoding="utf-8")
        return source

    with pytest.raises(FileExistsError, match="immutable preparation destination already exists"):
        _run_synthetic(
            tmp_path,
            source,
            authorization,
            reader=create_racing_destination,
            bundle_root=bundle_root,
        )
    assert reads == [source]
    assert (destination / "sentinel.txt").read_text(encoding="utf-8") == "preserve-race"
    assert (tmp_path / "execution-receipts" / f"{authorization.execution_id}.json").is_file()


def test_fixed_source_reader_uses_only_the_allowlisted_path_and_checks_synthetic_identity(
    tmp_path: Path,
) -> None:
    source = _synthetic_source()
    authorization = _authorization(source)
    synthetic_source_path = tmp_path / preparation.EXPECTED_SOURCE_PATH
    synthetic_source_path.parent.mkdir(parents=True)
    synthetic_source_path.write_bytes(source)

    assert execution._read_fixed_source_snapshot(authorization, repository=tmp_path) == source
    synthetic_source_path.write_bytes(bytes([source[0] ^ 1]) + source[1:])
    with pytest.raises(execution.CustodianExecutionError, match="SHA-256"):
        execution._read_fixed_source_snapshot(authorization, repository=tmp_path)
    arbitrary_path = replace(authorization, source_path="data/raw/rossmann/other.csv")
    with pytest.raises(execution.CustodianExecutionError, match="fixed documented source path"):
        execution._read_fixed_source_snapshot(arbitrary_path, repository=tmp_path)


def test_provider_and_stl_remain_closed_without_separate_provider_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        provider,
        "_read_approved_bytes",
        lambda *args, **kwargs: pytest.fail("missing provider binding must stop before file read"),
    )
    monkeypatch.setattr(
        analysis,
        "decompose_development_sales",
        lambda *args, **kwargs: pytest.fail("missing provider binding must stop before STL"),
    )
    with pytest.raises(provider.DevelopmentInputError, match="external DevelopmentInputApproval"):
        provider.decompose_approved_development_sales(None)  # type: ignore[arg-type]


def test_cli_default_and_missing_fixed_packet_fail_without_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(execution, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(
        execution,
        "_read_fixed_source_snapshot",
        lambda *args, **kwargs: pytest.fail("CLI gate must stop before source access"),
    )
    with pytest.raises(SystemExit):
        preparation.cli_main([])
    with pytest.raises(SystemExit):
        preparation.cli_main(["--execute-once"])
    with pytest.raises(SystemExit):
        preparation.cli_main(["--execute-once", "--approval-reference", "arbitrary-string"])
    assert "no source was opened" in capsys.readouterr().err


def test_describe_command_reports_fixed_gate_without_opening_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        execution,
        "_read_fixed_source_snapshot",
        lambda *args, **kwargs: pytest.fail("contract description must not access source bytes"),
    )
    assert preparation.cli_main(["--describe-input-contract"]) == 0
    contract = json.loads(capsys.readouterr().out)
    assert contract["production_source"] == "data/raw/rossmann/train.csv"
    assert "fails closed" in contract["default_execution"]
    assert "no data-file I/O" in contract["contract_description"]
    assert "--execute-once" in contract["one_time_execution"]
    assert "not approving authority" in contract["authorization"]
    assert "separate approval" in contract["downstream_gates"]
    assert contract["execution_authorization"]["source_snapshot"]["bytes"] == (
        preparation.REFERENCE_SOURCE_BYTES
    )
