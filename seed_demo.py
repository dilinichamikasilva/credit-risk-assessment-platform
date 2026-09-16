"""One-off: insert a demo application row into data/app.db for manual /docs testing."""
import sqlite3

con = sqlite3.connect("data/app.db")
cur = con.execute(
    """INSERT INTO applications
       (applicant_name, no_of_dependents, education, self_employed,
        income_annum, loan_amount, loan_term, cibil_score,
        residential_assets_value, commercial_assets_value,
        luxury_assets_value, bank_asset_value, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("Ilma Manual", 2, "Graduate", "No", 9_600_000, 29_900_000, 12, 778,
     2_400_000, 17_600_000, 22_700_000, 8_000_000, "submitted"),
)
con.commit()
print("seeded application id:", cur.lastrowid)
con.close()