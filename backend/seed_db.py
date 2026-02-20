import json
import os
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal
import models

def init_db():
    print("Táblák létrehozása...")
    models.Base.metadata.create_all(bind=engine)
    print("Táblák sikeresen létrehozva.")

def seed_data():
    db = SessionLocal()
    
    # Útvonal a json fájlhoz (két mappával kijjebb van a backendhez képest)
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'hibajegyzek_research.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("Adatok betöltése a JSON fájlból...")
        
        # Hibatípusok (DefectType) betöltése
        if 'tipikus_hibak' in data:
            for item in data['tipikus_hibak']:
                # Nézzük meg, létezik-e már
                existing = db.query(models.DefectType).filter_by(id=item['id']).first()
                if not existing:
                    defect = models.DefectType(
                        id=item['id'],
                        name=item['nev'],
                        category=item['kategoria'],
                        severity=item['sulyossag'],
                        description=item['leiras'],
                        template_text=item['sablon_szoveg'],
                        recommended_action=item.get('javasolt_intezkedés', ''),
                        standard_reference=item.get('szabvany_pont', '')
                    )
                    db.add(defect)
            print(f"{len(data['tipikus_hibak'])} hibatípus feldolgozva.")

        # Sablon szövegek (TemplateText) betöltése
        if 'sablon_szovegek' in data:
            count = 0
            # Bevezetés
            for item in data['sablon_szovegek'].get('bevezetes_eloszovak', []):
                existing = db.query(models.TemplateText).filter_by(id=item['id']).first()
                if not existing:
                    db.add(models.TemplateText(id=item['id'], category='bevezetes', title=item['nev'], content=item['szoveg']))
                    count += 1
            # Vizsgálat módszere
            for item in data['sablon_szovegek'].get('vizsgalat_modszere', []):
                existing = db.query(models.TemplateText).filter_by(id=item['id']).first()
                if not existing:
                    db.add(models.TemplateText(id=item['id'], category='modszer', title=item['nev'], content=item['szoveg']))
                    count += 1
            # Általános megállapítások
            for item in data['sablon_szovegek'].get('altalanos_megallapitasok', []):
                existing = db.query(models.TemplateText).filter_by(id=item['id']).first()
                if not existing:
                    db.add(models.TemplateText(id=item['id'], category='megallapitas', title=item['nev'], content=item['szoveg']))
                    count += 1
            # Záró megjegyzések
            for item in data['sablon_szovegek'].get('zaro_megjegyzesek', []):
                existing = db.query(models.TemplateText).filter_by(id=item['id']).first()
                if not existing:
                    db.add(models.TemplateText(id=item['id'], category='zaro', title=item['nev'], content=item['szoveg']))
                    count += 1
            # Jogi nyilatkozatok
            for item in data['sablon_szovegek'].get('jogi_nyilatkozatok', []):
                existing = db.query(models.TemplateText).filter_by(id=item['id']).first()
                if not existing:
                    db.add(models.TemplateText(id=item['id'], category='nyilatkozat', title=item['nev'], content=item['szoveg']))
                    count += 1
                    
            print(f"{count} sablonszöveg feldolgozva.")
            
        db.commit()
        print("Adatbázis inicializálva és seed-elve!")
        
    except FileNotFoundError:
        print(f"Hiba: A {json_path} fájl nem található.")
    except Exception as e:
        print(f"Hiba történt a betöltés során: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
