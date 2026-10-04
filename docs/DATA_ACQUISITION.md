# Data Acquisition

## Source

Use the official [Kaggle Rossmann Store Sales competition](https://www.kaggle.com/c/rossmann-store-sales)
with competition slug `rossmann-store-sales`. Expected files are `train.csv`, `test.csv`,
`store.csv`, and `sample_submission.csv`.

## Automated Workflow

1. Sign in to Kaggle and accept any competition rules required for download access.
2. Create or refresh the Kaggle API credential in the user-level Kaggle configuration. Never put
   credentials in this repository.
3. Install the project and acquisition extra:

   ```powershell
   python -m pip install -e ".[acquisition]"
   ```

4. Run the acquisition command from the repository root:

   ```powershell
   python scripts/acquire_data.py
   ```

The command downloads to a temporary directory, verifies that all four expected archive members
exist and are non-empty, extracts them into a staging directory, and atomically renames that
directory to `data/raw/rossmann/`. It prints byte sizes and SHA-256 checksums. If the target already
exists, it stops instead of overwriting or mixing raw files.

An alternate destination can be selected with `--data-dir`. Relative paths are resolved from the
repository root; absolute paths are accepted.

## Manual Fallback

If the Kaggle client cannot be used, download the official competition archive in a browser after
accepting the rules. Extract exactly the four expected CSV files into `data/raw/rossmann/`, without
renaming or editing them, then run:

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
```

Do not commit the archive or CSV files. Do not copy data from unofficial mirrors.

## Current Acquisition Status

On 2026-10-05, Kaggle CLI 2.2.4 was installed in the local ignored environment and a structurally
configured user credential was detected. The official download returned HTTP 403 Forbidden. No
target raw-data directory was created. The account must accept the competition rules or refresh its
access credential before acquisition can be retried.
