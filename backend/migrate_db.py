import sqlite3

db_path = r"c:\Users\User\Downloads\Villamos_biztons_gi_ellen_rz_s (1)\vbf_jegyzokonyv\backend\vbf_database.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

columns = [
    ("breaker_type", "VARCHAR(50)"),
    ("breaker_value", "NUMERIC(10, 2)"),
    ("wire_material", "VARCHAR(50)"),
    ("wire_cross_section", "NUMERIC(10, 2)"),
    ("zs_value_ohm", "NUMERIC(10, 4)"),
    ("du_value_percent", "NUMERIC(10, 2)"),
    ("fire_rating", "VARCHAR(100)")
]

for col_name, col_type in columns:
    try:
        c.execute(f"ALTER TABLE insulation_measurements ADD COLUMN {col_name} {col_type}")
        print(f"Added {col_name}")
    except sqlite3.OperationalError as e:
        print(f"Skipped {col_name} ({e})")

conn.commit()
conn.close()
print("Migration done.")
