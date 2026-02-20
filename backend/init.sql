-- Fő protokoll tábla
CREATE TABLE IF NOT EXISTS protocols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    serial_number VARCHAR(50) NOT NULL UNIQUE,
    certificate_number VARCHAR(100),
    location_address TEXT NOT NULL,
    network_type VARCHAR(20) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    inspection_type VARCHAR(50) NOT NULL,
    inspection_date DATE NOT NULL,
    instrument_model VARCHAR(100),
    calibration_valid_until DATE,
    inspector_name VARCHAR(255) NOT NULL,
    professional_summary TEXT,
    defect_list TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    -- EPH specific fields
    protocol_type VARCHAR(20) DEFAULT 'vbf',
    gas_provider_required BOOLEAN DEFAULT FALSE,
    gas_meter_number VARCHAR(50),
    gas_appliance_type VARCHAR(100),
    pe_conductor_size DECIMAL(5, 2),
    eph_conductor_size DECIMAL(5, 2),
    pen_separation_point VARCHAR(255)
);

-- Védővezető folytonosság (Rpe) mérések
CREATE TABLE IF NOT EXISTS rpe_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    point_number INTEGER,
    location VARCHAR(255),
    value_ohm DECIMAL(10,4),
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Szigetelési ellenállás mérések
CREATE TABLE IF NOT EXISTS insulation_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    circuit_name VARCHAR(255),
    ln_value_mohm DECIMAL(10,2),
    lpe_value_mohm DECIMAL(10,2),
    npe_value_mohm DECIMAL(10,2),
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Hurokellenállás (Zs) mérések
CREATE TABLE IF NOT EXISTS loop_impedance_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    point_number INTEGER,
    location VARCHAR(255),
    value_ohm DECIMAL(10,4),
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FI-relé tesztek
CREATE TABLE IF NOT EXISTS rcd_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    test_type VARCHAR(50),
    current_description VARCHAR(100),
    trip_time_ms DECIMAL(10,2),
    passed BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vizsgálati összesítés
CREATE TABLE IF NOT EXISTS summary_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id UUID REFERENCES protocols(id) ON DELETE CASCADE,
    test_name VARCHAR(100),
    result VARCHAR(50),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Földelési mérések (EPH)
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

-- EPH bekötések
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

-- Indexek a gyorsabb lekérdezésekhez
CREATE INDEX IF NOT EXISTS idx_protocols_serial ON protocols(serial_number);
CREATE INDEX IF NOT EXISTS idx_protocols_date ON protocols(inspection_date);
CREATE INDEX IF NOT EXISTS idx_rpe_protocol ON rpe_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_insulation_protocol ON insulation_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_loop_protocol ON loop_impedance_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_rcd_protocol ON rcd_tests(protocol_id);
CREATE INDEX IF NOT EXISTS idx_summary_protocol ON summary_results(protocol_id);
CREATE INDEX IF NOT EXISTS idx_earthing_protocol ON earthing_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_eph_protocol ON eph_measurements(protocol_id);
CREATE INDEX IF NOT EXISTS idx_protocol_defects_protocol ON protocol_defects(protocol_id);
CREATE INDEX IF NOT EXISTS idx_protocol_defects_type ON protocol_defects(defect_type_id);
CREATE INDEX IF NOT EXISTS idx_defect_images_defect ON defect_images(protocol_defect_id);
CREATE INDEX IF NOT EXISTS idx_template_texts_category ON template_texts(category);

-- Hibatípusok alapadatok feltöltése
INSERT INTO defect_types (id, name, category, severity, description, template_text, recommended_action, standard_reference) VALUES 
('HIBA-001', 'Hiányzó vagy hibás FI-relé (RCD)', 'aramutes_veszelye', 'kritikus', 'Az áramvédő kapcsoló hiányzik vagy nem működik megfelelően.', 'A vizsgálat során megállapítást nyert, hogy az érintésvédelmi áramvédő kapcsolóval (RCD) nem rendelkezik / működésképtelen.', '30mA érzékenységű RCD azonnali beszerelése kötelező.', 'MSZ HD 60364-4-41:2017, 411.3.3'),
('HIBA-002', 'Hiányzó vagy megszakadt védővezeték (PE)', 'aramutes_veszelye', 'kritikus', 'A védővezeték nem csatlakozik vagy megszakadt.', 'A védővezeték (PE) folytonossága nem biztosított. Közvetlen életveszély áll fenn.', 'A védővezeték azonnali helyreállítása kötelező.', 'MSZ HD 60364-5-54:2014, 543.1'),
('HIBA-003', 'Szigetelési ellenállás nem megfelelő', 'aramutes_veszelye', 'sulyos', 'A szigetelési ellenállás nem éri el az 1 MΩ minimumot.', 'A szigetelési ellenállás mért értéke nem megfelelő. Zárlat és áramütés veszélye.', 'A hibás vezetékszakasz cseréje szükséges.', 'MSZ HD 60364-6:2017, 6.4.3.3'),
('HIBA-004', 'Nem megfelelő túláramvédelem', 'tuz_veszelye', 'sulyos', 'A túláramvédelem nem felel meg a vezeték keresztmetszetének.', 'A túláramvédelem nem megfelelő a vezeték keresztmetszetéhez.', 'A túláramvédelem cseréje szükséges.', 'MSZ HD 60364-4-43:2013, 433.1'),
('HIBA-005', 'Hiányzó vagy hibás érvéghüvely', 'tuz_veszelye', 'kozepes', 'Sodrott vezetéken nincs érvéghüvely.', 'A többerű vezetékek végződéseinél érvéghüvely nem található.', 'Érvéghüvelyek felszerelése szükséges.', 'MSZ HD 60364-5-52:2014, 526.1'),
('HIBA-006', 'Szabványtalan vezetékszín-jelölés', 'szabvanytalan_allapot', 'kozepes', 'A vezetékek színjelölése nem megfelelő.', 'A vezetékek színjelölése nem felel meg a szabványnak.', 'Megfelelő jelölés szükséges.', 'MSZ HD 60364-5-51:2017, 514.3'),
('HIBA-007', 'Alumínium és réz közvetlen érintkezése', 'tuz_veszelye', 'sulyos', 'Réz és alumínium vezeték közvetlenül érintkezik.', 'Alumínium és réz vezeték közvetlen kontaktusban van.', 'Bimetál saru alkalmazása szükséges.', 'MSZ HD 60364-5-52:2014, 526.2'),
('HIBA-008', 'Hiányzó vagy sérült burkolat', 'aramutes_veszelye', 'sulyos', 'A burkolat sérült vagy hiányzik.', 'A villamos berendezés burkolata sérült/hiányzik.', 'A burkolat javítása/cseréje szükséges.', 'MSZ HD 60364-4-41:2017, 416'),
('HIBA-009', 'Túlterhelt csatlakozási pont', 'tuz_veszelye', 'sulyos', 'A csatlakozási pont túlterhelt.', 'A csatlakozási pont túlterhelt, fokozott tűzveszély.', 'A csatlakozási pont tehermentesítése szükséges.', 'MSZ HD 60364-5-52:2014, 526.3'),
('HIBA-010', 'Nem megfelelő IP védettség', 'szabvanytalan_allapot', 'kozepes', 'Az IP védettségi fokozat nem megfelelő.', 'Az IP védettségi fokozat nem felel meg a helyszínnek.', 'Megfelelő IP védettségű berendezés szükséges.', 'MSZ HD 60364-5-51:2017, 512.2'),
('HIBA-011', 'Hiányzó dokumentáció', 'szabvanytalan_allapot', 'enyhe', 'A műszaki dokumentáció hiányzik.', 'A műszaki dokumentáció nem áll rendelkezésre.', 'Dokumentáció készítése szükséges.', 'MSZ HD 60364-6:2017, 6.4.2.1'),
('HIBA-012', 'Csavart/forrasztott kötés', 'tuz_veszelye', 'sulyos', 'Szabványtalan vezetékkötés található.', 'Csavart/forrasztott kötés kötődoboz nélkül.', 'Kötődobozok és sorkapcsok alkalmazása.', 'MSZ HD 60364-5-52:2014, 526.4'),
('HIBA-013', 'Hurokimpedancia nem megfelelő', 'aramutes_veszelye', 'sulyos', 'A hurokimpedancia meghaladja a megengedettet.', 'A hurokimpedancia mért értéke túl magas.', 'A hurokimpedancia csökkentése szükséges.', 'MSZ HD 60364-4-41:2017, 411.4'),
('HIBA-014', 'Meglazult csatlakozások', 'tuz_veszelye', 'kozepes', 'A csatlakozási pontok meglazultak.', 'Meglazult kötések találhatók, tűzveszély.', 'A csatlakozások meghúzása szükséges.', 'MSZ HD 60364-5-52:2014, 526.1'),
('HIBA-015', 'Főelosztó EPH kötés hiánya', 'aramutes_veszelye', 'kritikus', 'Az EPH bekötés hiányos.', 'A fő egyenpotenciálra hozás nem megfelelő.', 'EPH bekötések pótlása szükséges.', 'MSZ HD 60364-4-41:2017, 411.3.1.2'),
('HIBA-016', 'Elavult alumínium vezetékezés', 'tuz_veszelye', 'kozepes', 'Az alumínium vezetékezés elavult.', 'Elavult alumínium vezetékezés, oxidált csatlakozók.', 'Felújítás szükséges.', 'MSZ HD 60364-5-52:2014, 523.9')
ON CONFLICT (id) DO NOTHING;

-- Sablon szövegek alapadatok feltöltése
INSERT INTO template_texts (id, category, title, content) VALUES
('BEV-001', 'bevezetes', 'Általános bevezetés', 'Jelen jegyzőkönyv időszakos biztonsági felülvizsgálat eredményeit tartalmazza az MSZ HD 60364-6:2017 és 40/2017. NGM rendelet alapján.'),
('BEV-002', 'bevezetes', 'Első felülvizsgálat', 'Jelen jegyzőkönyv üzembe helyezés előtti első felülvizsgálat eredményeit tartalmazza.'),
('BEV-003', 'bevezetes', 'Adásvétel előtti', 'Jelen jegyzőkönyv adásvétel/bérbeadás előtti kötelező felülvizsgálat eredményeit tartalmazza.'),
('MOD-001', 'modszer', 'Teljes vizsgálat', 'A felülvizsgálat szemrevételezéses vizsgálatból és műszeres mérésekből állt: Rpe, szigetelés, hurokimpedancia, RCD teszt.'),
('MOD-002', 'modszer', 'Egyszerűsített', 'A felülvizsgálat az MSZ HD 60364-6:2017 szabvány előírásai szerint történt.'),
('MEG-001', 'megallapitas', 'Megfelelt', 'A vizsgált villamos berendezés MEGFELELT minősítésű. Üzemeltetése folytatható.'),
('MEG-002', 'megallapitas', 'Nem felelt meg', 'A vizsgált villamos berendezés NEM FELELT MEG. A hibák kijavításáig üzemeltetése TILOS.'),
('MEG-003', 'megallapitas', 'Feltételesen megfelelt', 'A vizsgált villamos berendezés FELTÉTELESEN MEGFELELT. A hibák javítása ajánlott.'),
('ZAR-001', 'zaro', 'Érvényesség', 'A jegyzőkönyv a kiállítástól számított meghatározott ideig érvényes.'),
('JOG-001', 'nyilatkozat', 'Felülvizsgáló nyilatkozat', 'A felülvizsgálatot a vonatkozó szabványok szerint, hitelesített műszerrel végeztem.')
ON CONFLICT (id) DO NOTHING;
