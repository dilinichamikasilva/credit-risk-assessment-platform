"""Member 1 - Data & Pipeline Lead: build the shared train/val/test splits. v3

Reads the raw CSVs, produces stratified 70/15/15 splits for Model A (default
probability) and Models B/C (loan approval / recommended amount), and saves them
as parquet files under data/processed/ (gitignored - regenerate locally with:
python -m ml.training.prepare_data).

Split parameters mirror the training notebooks exactly:
test_size=0.30 then 0.50, stratified, random_state=RANDOM_STATE (42).
"""

from __future__ import annotations

import json

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.config import DATA_PROCESSED, DATA_RAW, RANDOM_STATE, ensure_dirs
from ml.pipeline.features import strip_loan_frame

FIRST_SPLIT = dict(test_size=0.30, random_state=RANDOM_STATE)
SECOND_SPLIT = dict(test_size=0.50, random_state=RANDOM_STATE)


def _save(prefix, name, frame):
    path = DATA_PROCESSED / f'{prefix}_{name}.parquet'
    frame.to_parquet(path)
    print(f'  saved {path.name:22s} rows={len(frame):>7,} cols={frame.shape[1]}')


def _two_stage_split(X, y, stratify_first, second_stratifier=None):
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, stratify=stratify_first, **FIRST_SPLIT
    )
    stratify_second = y_temp if second_stratifier is None else second_stratifier(y_temp)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, stratify=stratify_second, **SECOND_SPLIT
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def _default_csv():
    for name in ('credit_risk_dataset.csv', 'credit_risk_dataset_1.csv'):
        path = DATA_RAW / name
        if path.exists():
            return path
    raise FileNotFoundError('credit risk dataset not found in data/raw/')


def build_default_splits() -> dict:
    path = _default_csv()
    print(f'Model A source: {path.name}')
    df = pd.read_csv(path)
    y = df['SeriousDlqin2yrs'].astype(int)
    X = df.drop(columns=[c for c in ('SeriousDlqin2yrs', 'Id') if c in df.columns])

    X_train, X_val, X_test, y_train, y_val, y_test = _two_stage_split(X, y, y)

    _save('a', 'train', X_train)
    _save('a', 'val', X_val)
    _save('a', 'test', X_test)
    _save('ya', 'train', y_train.to_frame())
    _save('ya', 'val', y_val.to_frame())
    _save('ya', 'test', y_test.to_frame())

    scale_pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    print(f'  scale_pos_weight = {scale_pos_weight:.2f}')
    return {
        'source': path.name,
        'rows': {'train': len(X_train), 'val': len(X_val), 'test': len(X_test)},
        'scale_pos_weight': round(scale_pos_weight, 4),
    }


def build_loan_splits() -> dict:
    path = DATA_RAW / 'loan_approval_dataset.csv'
    loan_df = strip_loan_frame(pd.read_csv(path))
    print(f'Models B/C source: {path.name} (strip_loan_frame applied)')

    # ---- Model B: approve / reject on ALL rows (same encoding as notebook 03) ----
    y_b = (loan_df['loan_status'] == 'Approved').astype(int)
    X_b = loan_df.drop(columns=[c for c in ('loan_status', 'loan_id') if c in loan_df.columns])

    Xb_train, Xb_val, Xb_test, yb_train, yb_val, yb_test = _two_stage_split(X_b, y_b, y_b)
    _save('b', 'train', Xb_train)
    _save('b', 'val', Xb_val)
    _save('b', 'test', Xb_test)
    _save('yb', 'train', yb_train.to_frame())
    _save('yb', 'val', yb_val.to_frame())
    _save('yb', 'test', yb_test.to_frame())

    # ---- Model C: Approved applications only (same as notebook 04) ----
    work = loan_df[loan_df['loan_status'] == 'Approved'].reset_index(drop=True)
    y_c = work['loan_amount'].astype(float)
    X_c = work.drop(columns=[c for c in ('loan_status', 'loan_id', 'loan_amount') if c in work.columns])

    strata_first = pd.qcut(y_c, q=5, duplicates='drop')
    Xc_train, Xc_val, Xc_test, yc_train, yc_val, yc_test = _two_stage_split(
        X_c,
        y_c,
        stratify_first=strata_first,
        second_stratifier=lambda t: pd.qcut(t, q=min(5, t.nunique()), duplicates='drop'),
    )
    _save('c', 'train', Xc_train)
    _save('c', 'val', Xc_val)
    _save('c', 'test', Xc_test)
    _save('yc', 'train', yc_train.to_frame())
    _save('yc', 'val', yc_val.to_frame())
    _save('yc', 'test', yc_test.to_frame())

    return {
        'rows_b': {'train': len(Xb_train), 'val': len(Xb_val), 'test': len(Xb_test)},
        'rows_c_approved_only': {
            'train': len(Xc_train), 'val': len(Xc_val), 'test': len(Xc_test),
        },
    }


def main() -> None:
    ensure_dirs()
    print('prepare_data v3 running...')
    default_summary = build_default_splits()
    loan = build_loan_splits()
    summary = {
        'random_state': RANDOM_STATE,
        'split': '70/15/15 (0.30 then 0.50), stratified',
        'default_a': default_summary,
        'loan_b': {'rows': loan['rows_b']},
        'loan_c': {
            'rows': loan['rows_c_approved_only'],
            'note': 'Approved only; target=loan_amount; X has no loan_amount',
        },
    }
    info_path = DATA_PROCESSED / 'split_info.json'
    info_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'Split summary written to {info_path}')


if __name__ == '__main__':
    main()
