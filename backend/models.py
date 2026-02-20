from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer, Numeric, Boolean, DateTime, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class Protocol(Base):
    __tablename__ = "protocols"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial_number = Column(String(50), nullable=False, unique=True)
    certificate_number = Column(String(100))
    location_address = Column(Text, nullable=False)
    network_type = Column(String(20), nullable=False)
    client_name = Column(String(255), nullable=False)
    inspection_type = Column(String(50), nullable=False)
    inspection_date = Column(Date, nullable=False)
    instrument_model = Column(String(100))
    calibration_valid_until = Column(Date)
    inspector_name = Column(String(255), nullable=False)
    professional_summary = Column(Text)
    defect_list = Column(Text)
    status = Column(String(20), default='draft')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # EPH specific fields
    protocol_type = Column(String(20), default='vbf')  # 'vbf' or 'eph'
    gas_provider_required = Column(Boolean, default=False)
    gas_meter_number = Column(String(50))
    gas_appliance_type = Column(String(100))
    pe_conductor_size = Column(Numeric(5, 2))  # PE vezeték keresztmetszet (mm²)
    eph_conductor_size = Column(Numeric(5, 2))  # EPH fővezeték keresztmetszet (mm²)
    pen_separation_point = Column(String(255))  # PE-N szétválasztás helye
    
    # Relationships
    rpe_measurements = relationship("RpeMeasurement", back_populates="protocol", cascade="all, delete-orphan")
    insulation_measurements = relationship("InsulationMeasurement", back_populates="protocol", cascade="all, delete-orphan")
    loop_impedance_measurements = relationship("LoopImpedanceMeasurement", back_populates="protocol", cascade="all, delete-orphan")
    rcd_tests = relationship("RcdTest", back_populates="protocol", cascade="all, delete-orphan")
    summary_results = relationship("SummaryResult", back_populates="protocol", cascade="all, delete-orphan")
    earthing_measurements = relationship("EarthingMeasurement", back_populates="protocol", cascade="all, delete-orphan")
    eph_measurements = relationship("EphMeasurement", back_populates="protocol", cascade="all, delete-orphan")
    protocol_defects = relationship("ProtocolDefect", back_populates="protocol", cascade="all, delete-orphan")


class RpeMeasurement(Base):
    __tablename__ = "rpe_measurements"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    point_number = Column(Integer)
    location = Column(String(255))
    value_ohm = Column(Numeric(10, 4))
    passed = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="rpe_measurements")


class InsulationMeasurement(Base):
    __tablename__ = "insulation_measurements"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    circuit_name = Column(String(255))
    ln_value_mohm = Column(Numeric(10, 2))
    lpe_value_mohm = Column(Numeric(10, 2))
    npe_value_mohm = Column(Numeric(10, 2))
    passed = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="insulation_measurements")


class LoopImpedanceMeasurement(Base):
    __tablename__ = "loop_impedance_measurements"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    point_number = Column(Integer)
    location = Column(String(255))
    value_ohm = Column(Numeric(10, 4))
    passed = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="loop_impedance_measurements")


class RcdTest(Base):
    __tablename__ = "rcd_tests"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    test_type = Column(String(50))
    current_description = Column(String(100))
    trip_time_ms = Column(Numeric(10, 2))
    passed = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="rcd_tests")


class SummaryResult(Base):
    __tablename__ = "summary_results"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    test_name = Column(String(100))
    result = Column(String(50))
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="summary_results")


class EarthingMeasurement(Base):
    """Földelési ellenállás mérések táblája"""
    __tablename__ = "earthing_measurements"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    
    # Mérési módszer: '3_wire', '2_clamp', 'soil_resistivity'
    measurement_method = Column(String(50))
    
    # Földelési ellenállás értékek (Ω)
    ra_value = Column(Numeric(10, 4))  # Földelési ellenállás
    rb_value = Column(Numeric(10, 4))  # Segédföldelő ellenállás
    rc_value = Column(Numeric(10, 4))  # Áramelektróda ellenállás
    
    # Fajlagos talajellenállás
    soil_resistivity = Column(Numeric(10, 2))  # ρE (Ωm)
    soil_type = Column(String(50))  # 'humus', 'clay', 'sand', 'gravel', 'rock', 'frozen', 'mixed'
    
    # Határérték és megfelelőség
    limit_value = Column(Numeric(10, 4), default=10.0)  # Alapértelmezett: 10 Ω
    passed = Column(Boolean)
    
    # Környezeti adatok
    temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    weather_conditions = Column(String(100))
    
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="earthing_measurements")


class EphMeasurement(Base):
    """EPH bekötések folytonosság mérések táblája"""
    __tablename__ = "eph_measurements"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    
    # Bekötött elem adatok
    element_name = Column(String(255))  # pl. "Vízcső", "Gázcső"
    element_type = Column(String(50))  # 'water_pipe', 'gas_pipe_metered', 'gas_pipe_unmetered', 'heating_pipe', 'metal_bathtub', 'shower_tray', 'lightning_conductor', 'other'
    connection_point = Column(String(255))  # EPH sín, PE sín, stb.
    
    # Mérési értékek
    continuity_resistance = Column(Numeric(10, 4))  # Folytonosság (Ω)
    passed = Column(Boolean)
    
    # Sorszám a dokumentumban
    point_number = Column(Integer)
    
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    protocol = relationship("Protocol", back_populates="eph_measurements")


class DefectType(Base):
    """Előre definiált hibatípusok táblája"""
    __tablename__ = "defect_types"
    
    id = Column(String(20), primary_key=True)  # pl. "HIBA-001"
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # aramutes_veszelye, tuz_veszelye, szabvanytalan_allapot
    severity = Column(String(20), nullable=False)  # kritikus, sulyos, kozepes, enyhe
    description = Column(Text)
    template_text = Column(Text)
    recommended_action = Column(Text)
    standard_reference = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    protocol_defects = relationship("ProtocolDefect", back_populates="defect_type")


class ProtocolDefect(Base):
    """Jegyzőkönyvhöz rendelt hibák táblája"""
    __tablename__ = "protocol_defects"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_id = Column(Uuid(as_uuid=True), ForeignKey("protocols.id", ondelete="CASCADE"))
    defect_type_id = Column(String(20), ForeignKey("defect_types.id", ondelete="SET NULL"))
    custom_description = Column(Text)  # Egyedi leírás a sablon helyett/mellett
    location = Column(String(255))  # Hiba pontos helye
    severity_override = Column(String(20))  # Ha felül akarjuk írni az alapértelmezett súlyosságot
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    protocol = relationship("Protocol", back_populates="protocol_defects")
    defect_type = relationship("DefectType", back_populates="protocol_defects")
    images = relationship("DefectImage", back_populates="protocol_defect", cascade="all, delete-orphan")


class DefectImage(Base):
    """Hibákhoz csatolt képek táblája"""
    __tablename__ = "defect_images"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_defect_id = Column(Uuid(as_uuid=True), ForeignKey("protocol_defects.id", ondelete="CASCADE"))
    image_path = Column(String(500), nullable=False)  # Relatív útvonal az uploads mappához képest
    original_filename = Column(String(255))  # Eredeti fájlnév
    description = Column(Text)  # Kép leírása
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    protocol_defect = relationship("ProtocolDefect", back_populates="images")


class TemplateText(Base):
    """Sablon szövegek táblája"""
    __tablename__ = "template_texts"
    
    id = Column(String(20), primary_key=True)  # pl. "BEV-001"
    category = Column(String(50), nullable=False)  # bevezetes, modszer, megallapitas, zaro, nyilatkozat
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
