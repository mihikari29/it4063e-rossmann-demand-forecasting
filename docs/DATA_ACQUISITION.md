# Data Acquisition

## Source and Current Snapshot

The source is the official
[Kaggle Rossmann Store Sales competition](https://www.kaggle.com/c/rossmann-store-sales)
with competition slug `rossmann-store-sales`.

The Phase 1 snapshot was obtained through the Kaggle web interface and placed, unchanged, under
`data/raw/rossmann/`. The user confirmed the official Kaggle provenance on 2026-10-05. The earlier
Kaggle API attempt returned HTTP 403; that API failure did not affect the manually downloaded files
and is no longer an acquisition blocker.

| File | Bytes | SHA-256 |
|---|---:|---|
| `train.csv` | 38,057,952 | `f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc` |
| `test.csv` | 1,427,425 | `e75f79972de046d88c2fd55da19df627f5ca654aaf418090d4d30c60ea7dbe26` |
| `store.csv` | 45,010 | `f56bd124a2849489e6bbb5c000f5fc9640204355e316475c918ae4d089afb344` |
| `sample_submission.csv` | 317,611 | `592d892eb07072ddfa3773f13c4822ce5d01981243134c8d512ae30f016805db` |

These hashes identify the validated local snapshot. Raw files are immutable and ignored by Git.

## Manual Kaggle Download

Manual download is the currently verified acquisition path and does not require Kaggle API access:

1. Sign in to Kaggle and open the official Rossmann Store Sales competition.
2. Accept any competition rules required for download access.
3. Download the competition archive through the Kaggle web interface.
4. Extract exactly `train.csv`, `test.csv`, `store.csv`, and `sample_submission.csv` into
   `data/raw/rossmann/` without renaming or editing them.
5. Run the validation command from the repository root:

   ```powershell
   python scripts/validate_data.py --report reports/validation/rossmann.json
   ```

Compare file sizes and SHA-256 hashes with the recorded snapshot when reproducing this exact source
version. Do not copy data from unofficial mirrors, commit the archive or CSV files, or combine files
from different downloads.

## Optional Kaggle API Workflow

The API workflow remains available after competition access and credentials are configured outside
the repository:

```powershell
python -m pip install -e ".[acquisition]"
python scripts/acquire_data.py
```

The command downloads into a temporary directory, verifies the expected non-empty archive members,
extracts into a staging directory, and atomically renames it to `data/raw/rossmann/`. It refuses to
overwrite or mix an existing raw directory. An alternate destination may be passed with
`--data-dir`; relative paths resolve from the repository root.

Kaggle usernames, API keys, credential files, and browser data must remain outside the repository.
API access is optional when the official files have already been obtained manually.
