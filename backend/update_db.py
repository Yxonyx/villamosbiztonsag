import sqlite3
import os

DB_PATH = "vbf_database.db"

def update_database():
    if not os.path.exists(DB_PATH):
        print(f"Hiba: Nincs adatbázis fájl ({DB_PATH}) ebben a mappában.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Új FI-relé oszlopok, amiket hozzá kell adni az rcd_tests táblához
    new_columns = {
        "circuit_name": "TEXT",
        "breaker_type": "TEXT",
        "breaker_value": "TEXT",
        "wire_material": "TEXT",
        "wire_cross_section": "TEXT",
        "rated_current_ma": "TEXT"
    }
    
    try:
        cursor.execute("PRAGMA table_info(rcd_tests)")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        added_count = 0
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                print(f"Hozzáadás: {col_name} ({col_type}) az rcd_tests táblához...")
                cursor.execute(f"ALTER TABLE rcd_tests ADD COLUMN {col_name} {col_type}")
                added_count += 1
                
        conn.commit()
        if added_count > 0:
            print(f"Sikeresen frissítve! {added_count} új oszlop hozzáadva a táblához.")
        else:
            print("Az adatbázis már naprakész, nem kellett módosítani.")
            
    except sqlite3.OperationalError as e:
        print(f"Hiba történt az adatbázis módosításakor: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Ellenőrzöm és frissítem az SQLite adatbázis sémáját...")
    update_database()
