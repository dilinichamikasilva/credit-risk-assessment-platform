# Phase 0 — Sri Lanka localization research findings

**Date:** 2026-09-18  
**Purpose:** Blocking research before dataset generation and model retrain for the Credit Risk Platform.

---

## 1. Labeled Sri Lankan credit datasets

| Source | Finding | Usable for this project? |
|---|---|---|
| Kaggle | No public labeled Sri Lankan consumer-default / loan-approval / loan-amount CSV found under CRIB / CBSL / local-bank keywords. | No |
| UCI ML Repository | No Sri Lanka–specific credit dataset. | No |
| data.gov.lk / DCS | Household Income & Expenditure Survey microdata catalogs exist; no licensed open loan-default/approval labels for training. | No (aggregate stats only) |
| CBSL | Credit Information page describes CRIB infrastructure; statistical releases are aggregates, not applicant-level labeled files. | No |
| CRIB (crib.lk) | Member-only credit reports/scores; no public training corpus. | No |
| Academic (Kelaniya KLN repository; IEEE ICODSA 2022) | Case studies cite **private** bank/finance-company data (e.g. ~10.6k bank loans with CRIB status; ~100k vehicle-leasing records). Papers describe methods/metrics; **raw CSVs are not released**. | No |

**Conclusion:** No licensable, public, labeled Sri Lankan applicant dataset matching Models A/B/C was found. **Phase 1 must use a synthetic generator** calibrated to published statistics and CRIB methodology notes — never labeled as real applicant records.

---

## 2. CRIB credit score — range and methodology (verified)

| Fact | Value | Source |
|---|---|---|
| Official name | **CRIB Score** (Individual / Corporate) | [CRIB FAQs](https://www.crib.lk/en/help-desk/faqs) |
| Numeric range | **250 – 900** (three-digit) | [CRIB Score Reference Guide PDF](https://www.crib.lk/images/pdfs/crib-score-reference-guide.pdf); CRIB FAQs; CRIB digital-access announcement |
| Direction | Higher score → lower credit risk to lenders | Same |
| Inputs (high level) | Payment behaviour, over-indebtedness, demographics, credit utilization, lender inquiries, guaranteed contracts, dishonoured cheques | Reference Guide + FAQs |
| Interpretation aid | Risk grade mapped from score; **XX** = insufficient information | Reference Guide |
| PD framing | Annual report describes score as related to probability of default over ~12 months (high-level product description) | [CRIB Annual Report 2024](https://www.crib.lk/images/pdfs/crib-annual-report-2024.pdf) |

**Not the same as CIBIL:** CIBIL commonly uses **300–900**. CRIB’s published floor is **250**, not 300.

**Unverified (do not invent):** Exact numeric cutoffs for CRIB letter grades (A1–E3 etc.) were not extracted as a complete official table for this plan. Risk-tier bins used in our app (Poor/Fair/Good/Excellent) will be **project-defined bands over 250–900**, documented as such in `meta.json` — not claimed as official CRIB grade boundaries.

---

## 3. Realistic LKR magnitudes (calibration anchors)

| Quantity | Figure | Source / note |
|---|---|---|
| Mean monthly household income | **LKR 76,414** (2019) | DCS Household Income and Expenditure Survey 2019 Final Results |
| Median monthly household income | **LKR 53,333** (2019) | Same |
| Implied mean annual HH income (nominal 2019) | ~**LKR 917,000** | 76,414 × 12 |
| Implied median annual HH income (2019) | ~**LKR 640,000** | 53,333 × 12 |
| HIES “loans” windfall/loan variable (subset) | mean ~**LKR 315k**, range ~4k–6.5M | DCS HIES 2019 NADA catalog variable `loans` (limited sample — use as order-of-magnitude only) |
| Inflation / 2024–2026 | Severe 2022–23 inflation raised nominal incomes vs 2019 | CBSL socio-economic publications; generator will target **nominal mid-2020s** retail bands, not raw 2019 rupees alone |
| Retail personal / consumer loan (synthetic target band) | ~**LKR 100,000 – 5,000,000** typical; some higher for secured | Calibrated order-of-magnitude from HIES loan tails + retail lending practice (not a CBSL published “average personal loan size”) |
| Housing / vehicle / secured (synthetic) | ~**LKR 1,000,000 – 25,000,000** | Plausible retail secured range for synthetic assets/loan amounts |
| Asset values (synthetic) | Residential/commercial/bank assets in **hundreds of thousands to tens of millions LKR** | Scaled to income so ratios stay sensible |

**Not found:** A CBSL-published single “average personal loan ticket size” suitable as a hard target. Synthetic loan amounts will be income-linked with noise, not a rescaled Indian crore distribution.

---

## 4. Implications for Phases 1–4

1. **Dataset:** Build `ml/training/generate_sri_lanka_dataset.py` → CSVs under `data/raw/` with explicit synthetic provenance in filenames/headers/`meta`.
2. **Score field:** Full rename **`cibil_score` → `crib_score`** everywhere (pipeline, schemas, routers, DB, frontend). CRIB range **250–900**.
3. **Currency:** Frontend `formatCurrency` → **LKR** (verify `en-LK` / `si-LK` / `en` rendering).
4. **Labels:** Replace every user-facing “CIBIL” with **CRIB**; disclose synthetic / indicative training data in UI.
5. **Model B labels:** Do **not** make `loan_status` a near-deterministic function of score alone (avoid repeating the Indian-dataset shortcut).

---

## 5. Sources (primary)

- https://www.crib.lk/images/pdfs/crib-score-reference-guide.pdf  
- https://www.crib.lk/en/help-desk/faqs  
- https://www.crib.lk/images/pdfs/crib-annual-report-2024.pdf  
- http://www.statistics.gov.lk/Resource/en/IncomeAndExpenditure/HouseholdIncomeandExpenditureSurvey2019FinalResults.pdf  
- https://www.cbsl.gov.lk/en/financial-system/financial-infrastructure/credit-information  
- Kelaniya / IEEE papers (private data; not redistributable)
