-- Migration script a hibajegyzék funkció hozzáadásához
-- Futtatás: psql -U vbf_user -d vbf_database -f migration.sql

-- Hibatípusok (előre definiált hibák)
CREATE TABLE IF NOT EXISTS defect_types (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    template_text TEXT,
    recommended_action TEXT,
    standard_reference VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jegyzőkönyvhöz rendelt hibák
CREATE TABLE IF NOT EXISTS protocol_defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    defect_type_id VARCHAR(20) REFERENCES defect_types(id) ON DELETE SET NULL,
    custom_description TEXT,
    location VARCHAR(255),
    severity_override VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Hibákhoz csatolt képek
CREATE TABLE IF NOT EXISTS defect_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_defect_id UUID REFERENCES protocol_defects(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sablon szövegek
CREATE TABLE IF NOT EXISTS template_texts (
    id VARCHAR(20) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexek
CREATE INDEX IF NOT EXISTS idx_protocol_defects_protocol ON protocol_defects(protocol_id);
CREATE INDEX IF NOT EXISTS idx_protocol_defects_type ON protocol_defects(defect_type_id);
CREATE INDEX IF NOT EXISTS idx_defect_images_defect ON defect_images(protocol_defect_id);
CREATE INDEX IF NOT EXISTS idx_template_texts_category ON template_texts(category);

-- Hibatípusok feltöltése
INSERT INTO defect_types (id, name, category, severity, description, template_text, recommended_action, standard_reference)
VALUES 
('HIBA-001', 'Hiányzó vagy hibás FI-relé (RCD)', 'aramutes_veszelye', 'kritikus', 
 'Az áramvédő kapcsoló (FI-relé) hiányzik, nem működik megfelelően, vagy a tesztgomb megnyomáskor nem old ki. A 30mA érzékenységű RCD hiánya az érintésvédelem alapvető hiányosságát jelenti.',
 'A vizsgálat során megállapítást nyert, hogy a(z) {helyszin} területén üzemelő villamos berendezés érintésvédelmi áramvédő kapcsolóval (RCD) nem rendelkezik / az áramvédő kapcsoló működésképtelen állapotban van. Az MSZ HD 60364-4-41 szabvány szerinti védelem nem biztosított.',
 '30mA érzékenységű, megfelelő névleges áramú áramvédő kapcsoló (RCD) azonnali beszerelése / cseréje kötelező.',
 'MSZ HD 60364-4-41:2017, 411.3.3'),

('HIBA-002', 'Hiányzó vagy megszakadt védővezeték (PE)', 'aramutes_veszelye', 'kritikus',
 'A védővezeték (PE) nem csatlakozik a fogyasztóhoz, megszakadt, vagy a csatlakozási pont meglazult. Ez az alapvető érintésvédelmi hiányosság közvetlen életveszélyt jelent.',
 'A(z) {helyszin} / {azonosito} jelű fogyasztási helyen a védővezeték (PE) folytonossága nem biztosított / a védővezeték hiányzik. A védővezető-ellenállás mért értéke: {ertek} Ω (megengedett: max. 1 Ω). Közvetlen életveszély áll fenn.',
 'A védővezeték azonnali helyreállítása, a csatlakozási pontok ellenőrzése és megfelelő rögzítése. A hiba elhárításáig a fogyasztó használata TILOS.',
 'MSZ HD 60364-5-54:2014, 543.1'),

('HIBA-003', 'Szigetelési ellenállás nem megfelelő', 'aramutes_veszelye', 'sulyos',
 'A vezetékek szigetelési ellenállása a mért értékek alapján nem éri el a szabványban előírt minimális értéket (általában 1 MΩ). Ez elektromos zárlat és áramütés veszélyét jelenti.',
 'A(z) {aramkor} áramkör szigetelési ellenállásának mért értéke: {ertek} MΩ. A megengedett minimális érték: 1 MΩ (MSZ HD 60364-6:2017, 6.4.3.3 táblázat szerint). A szigetelés nem megfelelő állapotú.',
 'A szigetelési hiba helyének megkeresése és a hibás vezetékszakasz cseréje. Nedvesség okozta hiba esetén a nedvesség forrásának megszüntetése.',
 'MSZ HD 60364-6:2017, 6.4.3.3'),

('HIBA-004', 'Nem megfelelő túláramvédelem', 'tuz_veszelye', 'sulyos',
 'A kismegszakító vagy biztosító névleges értéke nem felel meg a vezeték megengedett terhelhetőségének. Túlméretezett védelem esetén a vezeték túlmelegedhet még mielőtt a védelem kioldana.',
 'A(z) {aramkor} áramkör túláramvédelme ({vedelem_tipus}, {vedelem_ertek}A) nem megfelelő a {vezetek_keresztmetszet} mm² keresztmetszetű vezetékhez. Megengedett maximális: {max_ertek}A. Az MSZ HD 60364-4-43 szabvány követelményei nem teljesülnek.',
 'A túláramvédelem cseréje a vezeték keresztmetszetének megfelelő névleges értékűre, vagy a vezeték cseréje megfelelő keresztmetszetűre.',
 'MSZ HD 60364-4-43:2013, 433.1'),

('HIBA-005', 'Hiányzó vagy hibás érvéghüvely', 'tuz_veszelye', 'kozepes',
 'A többerű (sodrott) vezetékek végén nem található érvéghüvely, vagy az érvéghüvely nincs megfelelően préselve. Ez rossz érintkezéshez, ívképződéshez és tűzveszélyhez vezethet.',
 'A(z) {helyszin} területén található villamos berendezésben a többerű (sodrott) vezetékek végződéseinél érvéghüvely alkalmazása nem történt meg / az érvéghüvely nem megfelelően rögzített. Tűzveszélyes állapot.',
 'Megfelelő méretű érvéghüvelyek felszerelése és szakszerű préselése minden sodrott vezetékvégen.',
 'MSZ HD 60364-5-52:2014, 526.1'),

('HIBA-006', 'Szabványtalan vezetékszín-jelölés', 'szabvanytalan_allapot', 'kozepes',
 'A vezetékek színjelölése nem felel meg az MSZ HD 60364 szabványnak. A védővezeték (zöld-sárga), a nullavezeték (kék) és a fázisvezetékek (barna, fekete, szürke) színe nem azonosítható egyértelműen.',
 'A(z) {helyszin} villamos hálózatán a vezetékek színjelölése nem felel meg az MSZ HD 60364-5-51:2017 szabvány 514.3 pontjában előírtaknak. Félreértésre és balesetveszélyre ad lehetőséget.',
 'A nem szabványos színjelölésű vezetékek jelölése megfelelő színű zsugórcsővel vagy jelölőgyűrűvel, vagy a vezetékek cseréje.',
 'MSZ HD 60364-5-51:2017, 514.3'),

('HIBA-007', 'Alumínium és réz vezeték közvetlen érintkezése', 'tuz_veszelye', 'sulyos',
 'A réz és alumínium vezetékek közvetlenül érintkeznek, megfelelő összekötő elem (pl. bimetál saruval) használata nélkül. Az elektrokémiai oxidáció fokozott átmeneti ellenállást és tűzveszélyt okoz.',
 'A(z) {helyszin} villamos berendezésében alumínium és réz vezeték közvetlen kontaktusban van speciális összekötő elem alkalmazása nélkül. Az elektrokémiai korrózió miatt fokozott tűzveszély áll fenn.',
 'Bimetál saruval vagy speciális összekötő elemmel történő újrabekötés, vagy az alumínium vezetékszakasz cseréje réz vezetékre.',
 'MSZ HD 60364-5-52:2014, 526.2'),

('HIBA-008', 'Hiányzó vagy sérült burkolat/fedél', 'aramutes_veszelye', 'sulyos',
 'A villamos berendezés burkolata hiányzik, megsérült vagy nem zárható megfelelően, így az aktív (feszültség alatt lévő) részek hozzáférhetővé válnak.',
 'A(z) {berendezes} villamos berendezés burkolata sérült / hiányzik / nem zárható megfelelően. Az aktív részek védelme nem biztosított, az MSZ HD 60364-4-41 szabvány 416. pontja szerinti védelem nem teljesül.',
 'A sérült burkolat azonnali javítása vagy cseréje. A hiányzó fedél pótlása. A hiba elhárításáig a berendezés használata TILOS.',
 'MSZ HD 60364-4-41:2017, 416'),

('HIBA-009', 'Túlterhelt csatlakozási pont', 'tuz_veszelye', 'sulyos',
 'Egy csatlakozási ponton több vezeték van bekötve, mint amennyi megengedett, vagy a csatlakozási pont túlterheltsége miatt felmelegedés tapasztalható.',
 'A(z) {helyszin} elosztóban a(z) {csatlakozo} csatlakozási pont túlterhelt: {vezetek_db} db vezeték bekötve a megengedett {max_db} helyett. Túlmelegedés / égésnyomok észlelhetők. Fokozott tűzveszély.',
 'A túlterhelt csatlakozási pont tehermentesítése, szükség esetén további sorkapcsok beépítése. Az érintett vezetékek és csatlakozások ellenőrzése, szükség esetén cseréje.',
 'MSZ HD 60364-5-52:2014, 526.3'),

('HIBA-010', 'Nem megfelelő IP védettség', 'szabvanytalan_allapot', 'kozepes',
 'A villamos berendezés IP (Ingress Protection) védettségi fokozata nem megfelelő a telepítési helyszínnek. Például vizes helyiségben IP20-as berendezés található.',
 'A(z) {helyszin} területén telepített {berendezes} villamos berendezés IP védettségi fokozata ({aktualis_ip}) nem felel meg a helyszín követelményeinek (elvárt: {elvart_ip}). Az MSZ HD 60364-5-51:2017 szabvány 512.2 pontjának követelményei nem teljesülnek.',
 'A nem megfelelő IP védettségű berendezés cseréje a helyszínnek megfelelő védettségű berendezésre.',
 'MSZ HD 60364-5-51:2017, 512.2'),

('HIBA-011', 'Hiányzó vagy elavult dokumentáció', 'szabvanytalan_allapot', 'enyhe',
 'A villamos berendezés áramköri rajza, kapcsolási vázlata vagy egyéb dokumentációja hiányzik, elavult vagy nem felel meg a tényleges állapotnak.',
 'A(z) {helyszin} villamos berendezéséhez tartozó műszaki dokumentáció (áramköri rajz, kapcsolási vázlat) nem áll rendelkezésre / elavult / nem felel meg a tényleges állapotnak. Az MSZ HD 60364-6:2017 szabvány 6.4.2.1 pontja szerinti ellenőrzés csak korlátozottan végezhető el.',
 'A villamos hálózat felmérése és új, naprakész dokumentáció készítése. Az elosztóban lévő áramkörök egyértelmű jelölése.',
 'MSZ HD 60364-6:2017, 6.4.2.1'),

('HIBA-012', 'Csavart/forrasztott vezetékkötés', 'tuz_veszelye', 'sulyos',
 'A vezetékek csavart vagy forrasztott kötéssel vannak összekötve, kötődoboz és megfelelő sorkapocs használata nélkül. Ez megbízhatatlan kötést és tűzveszélyt jelent.',
 'A(z) {helyszin} villamos hálózatán szabványtalan vezetékkötés található: csavart/forrasztott kötés kötődoboz nélkül. Az MSZ HD 60364-5-52:2014 szabvány 526.4 pontja szerinti követelmények nem teljesülnek. Fokozott tűzveszély.',
 'Az összes csavart/forrasztott kötés megszüntetése. Kötődobozok beépítése és megfelelő sorkapcsok vagy WAGO-típusú összekötők alkalmazása.',
 'MSZ HD 60364-5-52:2014, 526.4'),

('HIBA-013', 'Hurokimpedancia nem megfelelő', 'aramutes_veszelye', 'sulyos',
 'A mért hurokimpedancia értéke meghaladja a megengedett maximumot, így zárlat esetén a védelem nem tudja biztosítani az előírt kikapcsolási időt.',
 'A(z) {aramkor} áramkör hurokimpedanciájának mért értéke: {ertek} Ω. A megengedett maximális érték a {vedelem} védelemmel és {feszultseg}V feszültséggel: {max_ertek} Ω. Az automatikus lekapcsolással történő védelem az MSZ HD 60364-4-41:2017 szabvány 411.4 pontja szerint nem biztosított.',
 'A hurokimpedancia csökkentése: rövidebb vezetékhossz, nagyobb keresztmetszetű vezeték, vagy a földelés javítása.',
 'MSZ HD 60364-4-41:2017, 411.4'),

('HIBA-014', 'Meglazult csatlakozások', 'tuz_veszelye', 'kozepes',
 'A csatlakozási pontok meglazultak, a csavarok nem megfelelő nyomatékkal vannak meghúzva. Ez megnövekedett átmeneti ellenálláshoz és túlmelegedéshez vezet.',
 'A(z) {helyszin} elosztóban / csatlakozási pontokon meglazult kötések találhatók. A csatlakozások hőmérséklete emelkedett / égésnyomok láthatók. Fokozott tűzveszély áll fenn.',
 'Minden csatlakozási pont ellenőrzése és megfelelő nyomatékkal történő meghúzása. Sérült sorkapcsok, csatlakozók cseréje.',
 'MSZ HD 60364-5-52:2014, 526.1'),

('HIBA-015', 'Főelosztó EPH kötés hiánya', 'aramutes_veszelye', 'kritikus',
 'A főelosztónál az egyenpotenciálra hozás (EPH) nem megfelelő: a fém csőrendszerek (víz, gáz, fűtés) nincsenek bekötve a főföldvezetékbe.',
 'A(z) {helyszin} főelosztójánál a fő egyenpotenciálra hozás (EPH) nem megfelelő / hiányos. A következő vezetőképes rendszerek nincsenek bekötve: {rendszerek}. Az MSZ HD 60364-4-41:2017 szabvány 411.3.1.2 pontja szerinti védelem nem biztosított.',
 'Az összes vezetőképes rendszer (fém vízvezeték, gázvezeték, fűtéscsövek, szerkezeti fémek) bekötése a főföldvezetékbe megfelelő keresztmetszetű EPH vezetékkel.',
 'MSZ HD 60364-4-41:2017, 411.3.1.2'),

('HIBA-016', 'Elavult alumínium vezetékezés', 'tuz_veszelye', 'kozepes',
 'A régi, általában panelépületekben található alumínium vezetékezés oxidálódott, törékennyé vált. A csatlakozási pontoknál fokozott az átmeneti ellenállás és a tűzveszély.',
 'A(z) {helyszin} villamos hálózata elavult alumínium vezetékezéssel rendelkezik. A vezetékek törékenyek, oxidálódtak, a csatlakozási pontoknál megnövekedett átmeneti ellenállás mérhető. A hálózat felújítása szükséges.',
 'Hosszú távon a teljes hálózat cseréje réz vezetékekre. Rövid távon a csatlakozási pontok felülvizsgálata, speciális alumínium-kompatibilis sorkapcsok alkalmazása.',
 'MSZ HD 60364-5-52:2014, 523.9')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    severity = EXCLUDED.severity,
    description = EXCLUDED.description,
    template_text = EXCLUDED.template_text,
    recommended_action = EXCLUDED.recommended_action,
    standard_reference = EXCLUDED.standard_reference;

-- Sablon szövegek feltöltése
INSERT INTO template_texts (id, category, title, content)
VALUES
-- Bevezető szövegek
('BEV-001', 'bevezetes', 'Általános bevezetés - időszakos felülvizsgálat',
 'Jelen jegyzőkönyv a(z) {megrendelo_neve} megrendelésére, a(z) {cim} címen található villamos berendezés időszakos biztonsági felülvizsgálatának eredményeit tartalmazza. A felülvizsgálat az MSZ HD 60364-6:2017, valamint a 40/2017. (XII. 4.) NGM rendelet előírásai alapján történt.'),

('BEV-002', 'bevezetes', 'Bevezetés - első felülvizsgálat (üzembe helyezés előtt)',
 'Jelen jegyzőkönyv a(z) {cim} címen újonnan létesült / bővített / átalakított villamos berendezés üzembe helyezés előtti első felülvizsgálatának eredményeit tartalmazza. A felülvizsgálat célja annak megállapítása, hogy a villamos berendezés megfelel-e az MSZ HD 60364 szabványsorozat és a vonatkozó jogszabályok követelményeinek.'),

('BEV-003', 'bevezetes', 'Bevezetés - ingatlan adásvétel/bérbeadás',
 'Jelen jegyzőkönyv a(z) {cim} címen található ingatlan villamos berendezésének adásvétel / bérbeadás előtti kötelező biztonsági felülvizsgálatának eredményeit tartalmazza, a 40/2017. (XII. 4.) NGM rendelet 12. § (2) bekezdésének megfelelően.'),

-- Vizsgálati módszerek
('MOD-001', 'modszer', 'Vizsgálati módszerek - teljes',
 'A felülvizsgálat az alábbi vizsgálati módszerekkel történt:

1. Szemrevételezéses vizsgálat: A villamos berendezés látható részeinek, szerelési állapotának, jelöléseinek vizsgálata feszültségmentes és feszültség alatti állapotban.

2. Műszeres mérések:
- Védővezető folytonosság mérése
- Szigetelési ellenállás mérése
- Hurokimpedancia mérése
- RCD (áramvédő kapcsoló) működésének ellenőrzése
- Fázissorrend vizsgálata

Alkalmazott mérőműszerek: {muszer_tipus}, gyári szám: {gyari_szam}, kalibrálás érvényessége: {kalibralas_ervenyes}'),

('MOD-002', 'modszer', 'Vizsgálati módszerek - egyszerűsített',
 'A felülvizsgálat szemrevételezéses vizsgálatból és műszeres mérésekből állt, az MSZ HD 60364-6:2017 szabvány előírásai szerint. A mérésekhez használt műszer: {muszer_tipus}, kalibrálva: {kalibralas_datum}.'),

-- Megállapítások
('MEG-001', 'megallapitas', 'Megfelelt minősítés',
 'A vizsgált villamos berendezés érintésvédelmi szempontból MEGFELELT minősítésű. Az MSZ HD 60364 szabványsorozat és a 40/2017. (XII. 4.) NGM rendelet követelményeinek megfelel. A berendezés üzemeltetése az érvényességi időn belül folytatható.'),

('MEG-002', 'megallapitas', 'Nem felelt meg minősítés',
 'A vizsgált villamos berendezés érintésvédelmi szempontból NEM FELELT MEG minősítésű. A jegyzőkönyv hibajegyzék mellékletében felsorolt hiányosságok miatt a berendezés nem felel meg az MSZ HD 60364 szabványsorozat és a vonatkozó jogszabályok követelményeinek. A hibák kijavításáig a berendezés üzemeltetése NEM AJÁNLOTT / TILOS.'),

('MEG-003', 'megallapitas', 'Feltételesen megfelelt',
 'A vizsgált villamos berendezés érintésvédelmi szempontból FELTÉTELESEN MEGFELELT minősítésű. A hibajegyzékben felsorolt kisebb hiányosságok ellenére közvetlen életveszély nem áll fenn. A hibák javítása a következő időszakos felülvizsgálatig / a megjelölt határidőig elvégzendő.'),

-- Záró szövegek
('ZAR-001', 'zaro', 'Általános záradék',
 'A jegyzőkönyv a kiállítás napjától számított {ev} évig érvényes. A következő időszakos felülvizsgálat legkésőbbi időpontja: {kovetkezo_datum}. A jegyzőkönyv érvényét veszti, ha a villamos berendezésen bármilyen bővítés, átalakítás, javítás történik.'),

('ZAR-002', 'zaro', 'Záradék hibával',
 'A hibajegyzékben feltüntetett hiányosságok kijavítását követően utóellenőrzés szükséges. A hibajavítás dokumentálása a jegyzőkönyv M1 mellékletében történik. A végleges MEGFELELT minősítés csak a hibák kijavítása és ellenőrzése után adható ki.'),

-- Jogi nyilatkozatok
('JOG-001', 'nyilatkozat', 'Felülvizsgáló nyilatkozata',
 'Alulírott nyilatkozom, hogy a felülvizsgálatot a vonatkozó jogszabályok és szabványok előírásai szerint végeztem. A méréseket hitelesített mérőműszerrel hajtottam végre. A jegyzőkönyvben rögzített megállapítások a vizsgálat időpontjában fennálló állapotot tükrözik.'),

('JOG-002', 'nyilatkozat', 'Üzemeltető felelőssége',
 'A villamos berendezés üzemeltetője felelős a berendezés rendeltetésszerű használatáért, a feltárt hibák kijavításáért és a következő időszakos felülvizsgálat határidőben történő elvégeztetéséért. Az üzemeltetőnek biztosítania kell, hogy a villamos berendezésen csak szakképzett villanyszerelő végezzen bármilyen munkát.'),

('JOG-003', 'nyilatkozat', 'Kritikus hiba figyelmeztetés',
 'FIGYELMEZTETÉS: A jegyzőkönyvben ''kritikus'' súlyosságúként megjelölt hibák közvetlen életveszélyt és/vagy fokozott tűzveszélyt jelentenek. Ezen hibák azonnali kijavítása kötelező. A hibák kijavításáig az érintett áramkörök, berendezések üzemeltetése TILOS. Az üzemeltető tudomásul veszi, hogy a figyelmeztetés ellenére történő üzemeltetés esetén a felelősség őt terheli.')
ON CONFLICT (id) DO UPDATE SET
    category = EXCLUDED.category,
    title = EXCLUDED.title,
    content = EXCLUDED.content;

-- EPH és földelés táblák ha még nem léteznek
CREATE TABLE IF NOT EXISTS earthing_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    measurement_method VARCHAR(50),
    ra_value DECIMAL(10, 4),
    rb_value DECIMAL(10, 4),
    rc_value DECIMAL(10, 4),
    soil_resistivity DECIMAL(10, 2),
    soil_type VARCHAR(50),
    limit_value DECIMAL(10, 4) DEFAULT 10.0,
    passed BOOLEAN,
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    weather_conditions VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eph_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    element_name VARCHAR(255),
    element_type VARCHAR(50),
    connection_point VARCHAR(255),
    continuity_resistance DECIMAL(10, 4),
    passed BOOLEAN,
    point_number INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- EPH mezők hozzáadása a protocols táblához ha még nincsenek
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'protocol_type') THEN
        ALTER TABLE protocols ADD COLUMN protocol_type VARCHAR(20) DEFAULT 'vbf';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'gas_provider_required') THEN
        ALTER TABLE protocols ADD COLUMN gas_provider_required BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'gas_meter_number') THEN
        ALTER TABLE protocols ADD COLUMN gas_meter_number VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'gas_appliance_type') THEN
        ALTER TABLE protocols ADD COLUMN gas_appliance_type VARCHAR(100);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'pe_conductor_size') THEN
        ALTER TABLE protocols ADD COLUMN pe_conductor_size DECIMAL(5, 2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'eph_conductor_size') THEN
        ALTER TABLE protocols ADD COLUMN eph_conductor_size DECIMAL(5, 2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'protocols' AND column_name = 'pen_separation_point') THEN
        ALTER TABLE protocols ADD COLUMN pen_separation_point VARCHAR(255);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_earthing_protocol ON earthing_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_eph_protocol ON eph_measurements(protocol_id);
