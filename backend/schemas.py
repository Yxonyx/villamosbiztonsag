from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
from uuid import UUID
from enum import Enum


class NetworkType(str, Enum):
    TN_C_S = "TN-C-S"
    TN_S = "TN-S"
    TT = "TT"
    IT = "IT"


class InspectionType(str, Enum):
    INITIAL = "Első ellenőrzés (VBF)"
    PERIODIC = "Időszakos felülvizsgálat"
    EPH_ONLY = "EPH jegyzőkönyv"


class ProtocolType(str, Enum):
    VBF = "vbf"
    EPH = "eph"


class ResultStatus(str, Enum):
    PASS = "MEGFELELT"
    FAIL = "NEM FELELT MEG"
    NOT_TESTED = "NEM VIZSGÁLT"


class EarthingMethod(str, Enum):
    THREE_WIRE = "3_wire"
    TWO_CLAMP = "2_clamp"
    SOIL_RESISTIVITY = "soil_resistivity"


class SoilType(str, Enum):
    HUMUS = "humus"
    CLAY = "clay"
    SAND = "sand"
    GRAVEL = "gravel"
    ROCK = "rock"
    FROZEN = "frozen"
    MIXED = "mixed"


class EphElementType(str, Enum):
    WATER_PIPE = "water_pipe"
    GAS_PIPE_METERED = "gas_pipe_metered"
    GAS_PIPE_UNMETERED = "gas_pipe_unmetered"
    HEATING_PIPE = "heating_pipe"
    METAL_BATHTUB = "metal_bathtub"
    SHOWER_TRAY = "shower_tray"
    LIGHTNING_CONDUCTOR = "lightning_conductor"
    CABLE_TRAY = "cable_tray"
    OTHER = "other"


# Rpe Measurement schemas
class RpeMeasurementBase(BaseModel):
    point_number: int
    location: str
    value_ohm: float
    passed: bool = True


class RpeMeasurementCreate(RpeMeasurementBase):
    pass


class RpeMeasurement(RpeMeasurementBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# Insulation Measurement schemas
class InsulationMeasurementBase(BaseModel):
    circuit_name: str
    ln_value_mohm: float
    lpe_value_mohm: float
    npe_value_mohm: float
    passed: bool = True


class InsulationMeasurementCreate(InsulationMeasurementBase):
    pass


class InsulationMeasurement(InsulationMeasurementBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# Loop Impedance Measurement schemas
class LoopImpedanceMeasurementBase(BaseModel):
    point_number: int
    location: str
    value_ohm: float
    passed: bool = True


class LoopImpedanceMeasurementCreate(LoopImpedanceMeasurementBase):
    pass


class LoopImpedanceMeasurement(LoopImpedanceMeasurementBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# RCD Test schemas
class RcdTestBase(BaseModel):
    test_type: str
    current_description: str
    trip_time_ms: Optional[float] = None
    passed: bool = True


class RcdTestCreate(RcdTestBase):
    pass


class RcdTest(RcdTestBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# Summary Result schemas
class SummaryResultBase(BaseModel):
    test_name: str
    result: str
    comment: Optional[str] = None


class SummaryResultCreate(SummaryResultBase):
    pass


class SummaryResult(SummaryResultBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# Earthing Measurement schemas (Földelés mérés)
class EarthingMeasurementBase(BaseModel):
    measurement_method: Optional[str] = "3_wire"  # '3_wire', '2_clamp', 'soil_resistivity'
    ra_value: Optional[float] = None  # Földelési ellenállás (Ω)
    rb_value: Optional[float] = None  # Segédföldelő ellenállás (Ω)
    rc_value: Optional[float] = None  # Áramelektróda ellenállás (Ω)
    soil_resistivity: Optional[float] = None  # ρE (Ωm)
    soil_type: Optional[str] = None  # 'humus', 'clay', 'sand', etc.
    limit_value: float = 10.0  # Határérték (Ω), alapértelmezett: 10 Ω
    passed: Optional[bool] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    weather_conditions: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('passed', mode='before')
    @classmethod
    def auto_check_passed(cls, v, info):
        # Auto-check if Ra ≤ limit
        if v is None and info.data.get('ra_value') is not None:
            limit = info.data.get('limit_value', 10.0)
            return info.data['ra_value'] <= limit
        return v


class EarthingMeasurementCreate(EarthingMeasurementBase):
    pass


class EarthingMeasurement(EarthingMeasurementBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# EPH Measurement schemas (EPH bekötések)
class EphMeasurementBase(BaseModel):
    point_number: Optional[int] = None
    element_name: str  # pl. "Vízcső", "Gázcső"
    element_type: Optional[str] = "other"  # 'water_pipe', 'gas_pipe_metered', etc.
    connection_point: str = "EPH sín"  # EPH sín, PE sín, stb.
    continuity_resistance: Optional[float] = None  # Folytonosság (Ω)
    passed: bool = True
    notes: Optional[str] = None


class EphMeasurementCreate(EphMeasurementBase):
    pass


class EphMeasurement(EphMeasurementBase):
    id: UUID
    protocol_id: UUID

    class Config:
        from_attributes = True


# Protocol schemas
class ProtocolBase(BaseModel):
    serial_number: str
    certificate_number: Optional[str] = None
    location_address: str
    network_type: str
    client_name: str
    inspection_type: str
    inspection_date: date
    instrument_model: Optional[str] = None
    calibration_valid_until: Optional[date] = None
    inspector_name: str
    professional_summary: Optional[str] = None
    defect_list: Optional[str] = None
    status: str = "draft"
    # EPH specific fields
    protocol_type: str = "vbf"  # 'vbf' or 'eph'
    gas_provider_required: bool = False
    gas_meter_number: Optional[str] = None
    gas_appliance_type: Optional[str] = None
    pe_conductor_size: Optional[float] = None  # mm²
    eph_conductor_size: Optional[float] = None  # mm²
    pen_separation_point: Optional[str] = None


class ProtocolCreate(ProtocolBase):
    rpe_measurements: List[RpeMeasurementCreate] = []
    insulation_measurements: List[InsulationMeasurementCreate] = []
    loop_impedance_measurements: List[LoopImpedanceMeasurementCreate] = []
    rcd_tests: List[RcdTestCreate] = []
    summary_results: List[SummaryResultCreate] = []
    earthing_measurements: List[EarthingMeasurementCreate] = []
    eph_measurements: List[EphMeasurementCreate] = []


class ProtocolUpdate(BaseModel):
    serial_number: Optional[str] = None
    certificate_number: Optional[str] = None
    location_address: Optional[str] = None
    network_type: Optional[str] = None
    client_name: Optional[str] = None
    inspection_type: Optional[str] = None
    inspection_date: Optional[date] = None
    instrument_model: Optional[str] = None
    calibration_valid_until: Optional[date] = None
    inspector_name: Optional[str] = None
    professional_summary: Optional[str] = None
    defect_list: Optional[str] = None
    status: Optional[str] = None
    # EPH specific fields
    protocol_type: Optional[str] = None
    gas_provider_required: Optional[bool] = None
    gas_meter_number: Optional[str] = None
    gas_appliance_type: Optional[str] = None
    pe_conductor_size: Optional[float] = None
    eph_conductor_size: Optional[float] = None
    pen_separation_point: Optional[str] = None
    # Measurements
    rpe_measurements: Optional[List[RpeMeasurementCreate]] = None
    insulation_measurements: Optional[List[InsulationMeasurementCreate]] = None
    loop_impedance_measurements: Optional[List[LoopImpedanceMeasurementCreate]] = None
    rcd_tests: Optional[List[RcdTestCreate]] = None
    summary_results: Optional[List[SummaryResultCreate]] = None
    earthing_measurements: Optional[List[EarthingMeasurementCreate]] = None
    eph_measurements: Optional[List[EphMeasurementCreate]] = None


class Protocol(ProtocolBase):
    id: UUID
    rpe_measurements: List[RpeMeasurement] = []
    insulation_measurements: List[InsulationMeasurement] = []
    loop_impedance_measurements: List[LoopImpedanceMeasurement] = []
    rcd_tests: List[RcdTest] = []
    summary_results: List[SummaryResult] = []
    earthing_measurements: List[EarthingMeasurement] = []
    eph_measurements: List[EphMeasurement] = []
    protocol_defects: List["ProtocolDefect"] = []

    class Config:
        from_attributes = True


class ProtocolList(BaseModel):
    id: UUID
    serial_number: str
    location_address: str
    client_name: str
    inspection_date: date
    status: str
    protocol_type: str = "vbf"

    class Config:
        from_attributes = True


# DefectType schemas (Hibatípusok)
class DefectTypeBase(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    description: Optional[str] = None
    template_text: Optional[str] = None
    recommended_action: Optional[str] = None
    standard_reference: Optional[str] = None


class DefectType(DefectTypeBase):
    class Config:
        from_attributes = True


# DefectImage schemas (Hiba képek)
class DefectImageBase(BaseModel):
    image_path: str
    original_filename: Optional[str] = None
    description: Optional[str] = None


class DefectImageCreate(BaseModel):
    description: Optional[str] = None


class DefectImage(DefectImageBase):
    id: UUID
    protocol_defect_id: UUID

    class Config:
        from_attributes = True


# ProtocolDefect schemas (Jegyzőkönyv hibák)
class ProtocolDefectBase(BaseModel):
    defect_type_id: Optional[str] = None
    custom_description: Optional[str] = None
    location: Optional[str] = None
    severity_override: Optional[str] = None


class ProtocolDefectCreate(ProtocolDefectBase):
    pass


class ProtocolDefect(ProtocolDefectBase):
    id: UUID
    protocol_id: UUID
    defect_type: Optional[DefectType] = None
    images: List[DefectImage] = []

    class Config:
        from_attributes = True


# TemplateText schemas (Sablon szövegek)
class TemplateTextBase(BaseModel):
    id: str
    category: str
    title: str
    content: str


class TemplateText(TemplateTextBase):
    class Config:
        from_attributes = True
