from fastapi import FastAPI, Depends, HTTPException, Response, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import shutil
import uuid as uuid_module
from pathlib import Path

from database import get_db, engine, Base
import models
import schemas
from docx_generator import generate_protocol_docx, generate_eph_docx
from padfx_parser import parse_padfx_content
from update_db import update_database

# Uploads directory
UPLOADS_DIR = Path("uploads/defect_images")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Create tables and run schema updates
Base.metadata.create_all(bind=engine)
update_database()

app = FastAPI(
    title="VBF Jegyzőkönyv API",
    description="Villamos Biztonsági Felülvizsgálati Jegyzőkönyv Kezelő",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = "static"
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = "static/index.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>VBF Jegyzőkönyv Alkalmazás</h1><p>Frontend nem található.</p>")


# PADFX Import Endpoint
@app.post("/api/import-padfx")
async def import_padfx(file: UploadFile = File(...)):
    """Metrel PADFX mérési adatfájl feldolgozása és JSON-né alakítása"""
    if not file.filename.endswith('.padfx'):
        raise HTTPException(status_code=400, detail="Csak .padfx fájlok tölthetők fel.")
    try:
        content = await file.read()
        parsed_data = parse_padfx_content(content)
        return parsed_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Protocol CRUD endpoints
@app.get("/api/protocols", response_model=List[schemas.ProtocolList])
def list_protocols(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista összes jegyzőkönyv"""
    protocols = db.query(models.Protocol).order_by(models.Protocol.created_at.desc()).offset(skip).limit(limit).all()
    return protocols


@app.post("/api/protocols", response_model=schemas.Protocol)
def create_protocol(protocol: schemas.ProtocolCreate, db: Session = Depends(get_db)):
    """Új jegyzőkönyv létrehozása"""
    # Check if serial number exists
    existing = db.query(models.Protocol).filter(models.Protocol.serial_number == protocol.serial_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ez a sorszám már létezik")
    
    # Create protocol with EPH fields
    db_protocol = models.Protocol(
        serial_number=protocol.serial_number,
        certificate_number=protocol.certificate_number,
        location_address=protocol.location_address,
        network_type=protocol.network_type,
        client_name=protocol.client_name,
        inspection_type=protocol.inspection_type,
        inspection_date=protocol.inspection_date,
        instrument_model=protocol.instrument_model,
        calibration_valid_until=protocol.calibration_valid_until,
        inspector_name=protocol.inspector_name,
        professional_summary=protocol.professional_summary,
        defect_list=protocol.defect_list,
        status=protocol.status,
        # EPH specific fields
        protocol_type=protocol.protocol_type,
        gas_provider_required=protocol.gas_provider_required,
        gas_meter_number=protocol.gas_meter_number,
        gas_appliance_type=protocol.gas_appliance_type,
        pe_conductor_size=protocol.pe_conductor_size,
        eph_conductor_size=protocol.eph_conductor_size,
        pen_separation_point=protocol.pen_separation_point
    )
    db.add(db_protocol)
    db.flush()
    
    # Add VBF measurements
    for rpe in protocol.rpe_measurements:
        db.add(models.RpeMeasurement(protocol_id=db_protocol.id, **rpe.model_dump()))
    
    for ins in protocol.insulation_measurements:
        db.add(models.InsulationMeasurement(protocol_id=db_protocol.id, **ins.model_dump()))
    
    for loop in protocol.loop_impedance_measurements:
        db.add(models.LoopImpedanceMeasurement(protocol_id=db_protocol.id, **loop.model_dump()))
    
    for rcd in protocol.rcd_tests:
        db.add(models.RcdTest(protocol_id=db_protocol.id, **rcd.model_dump()))
    
    for summary in protocol.summary_results:
        db.add(models.SummaryResult(protocol_id=db_protocol.id, **summary.model_dump()))
    
    # Add EPH/Earthing measurements
    for earthing in protocol.earthing_measurements:
        data = earthing.model_dump()
        # Auto-check passed if Ra <= limit
        if data.get('ra_value') is not None and data.get('passed') is None:
            data['passed'] = data['ra_value'] <= data.get('limit_value', 10.0)
        db.add(models.EarthingMeasurement(protocol_id=db_protocol.id, **data))
    
    for eph in protocol.eph_measurements:
        db.add(models.EphMeasurement(protocol_id=db_protocol.id, **eph.model_dump()))
    
    db.commit()
    db.refresh(db_protocol)
    return db_protocol


@app.get("/api/protocols/{protocol_id}", response_model=schemas.Protocol)
def get_protocol(protocol_id: UUID, db: Session = Depends(get_db)):
    """Jegyzőkönyv lekérdezése"""
    protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    return protocol


@app.put("/api/protocols/{protocol_id}", response_model=schemas.Protocol)
def update_protocol(protocol_id: UUID, protocol_update: schemas.ProtocolUpdate, db: Session = Depends(get_db)):
    """Jegyzőkönyv frissítése"""
    db_protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not db_protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    
    # Update basic fields (excluding measurement lists)
    exclude_fields = {'rpe_measurements', 'insulation_measurements', 'loop_impedance_measurements', 
                      'rcd_tests', 'summary_results', 'earthing_measurements', 'eph_measurements'}
    update_data = protocol_update.model_dump(exclude_unset=True, exclude=exclude_fields)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_protocol, key, value)
    
    # Update VBF measurements if provided
    if protocol_update.rpe_measurements is not None:
        db.query(models.RpeMeasurement).filter(models.RpeMeasurement.protocol_id == protocol_id).delete()
        for rpe in protocol_update.rpe_measurements:
            db.add(models.RpeMeasurement(protocol_id=protocol_id, **rpe.model_dump()))
    
    if protocol_update.insulation_measurements is not None:
        db.query(models.InsulationMeasurement).filter(models.InsulationMeasurement.protocol_id == protocol_id).delete()
        for ins in protocol_update.insulation_measurements:
            db.add(models.InsulationMeasurement(protocol_id=protocol_id, **ins.model_dump()))
    
    if protocol_update.loop_impedance_measurements is not None:
        db.query(models.LoopImpedanceMeasurement).filter(models.LoopImpedanceMeasurement.protocol_id == protocol_id).delete()
        for loop in protocol_update.loop_impedance_measurements:
            db.add(models.LoopImpedanceMeasurement(protocol_id=protocol_id, **loop.model_dump()))
    
    if protocol_update.rcd_tests is not None:
        db.query(models.RcdTest).filter(models.RcdTest.protocol_id == protocol_id).delete()
        for rcd in protocol_update.rcd_tests:
            db.add(models.RcdTest(protocol_id=protocol_id, **rcd.model_dump()))
    
    if protocol_update.summary_results is not None:
        db.query(models.SummaryResult).filter(models.SummaryResult.protocol_id == protocol_id).delete()
        for summary in protocol_update.summary_results:
            db.add(models.SummaryResult(protocol_id=protocol_id, **summary.model_dump()))
    
    # Update EPH/Earthing measurements if provided
    if protocol_update.earthing_measurements is not None:
        db.query(models.EarthingMeasurement).filter(models.EarthingMeasurement.protocol_id == protocol_id).delete()
        for earthing in protocol_update.earthing_measurements:
            data = earthing.model_dump()
            if data.get('ra_value') is not None and data.get('passed') is None:
                data['passed'] = data['ra_value'] <= data.get('limit_value', 10.0)
            db.add(models.EarthingMeasurement(protocol_id=protocol_id, **data))
    
    if protocol_update.eph_measurements is not None:
        db.query(models.EphMeasurement).filter(models.EphMeasurement.protocol_id == protocol_id).delete()
        for eph in protocol_update.eph_measurements:
            db.add(models.EphMeasurement(protocol_id=protocol_id, **eph.model_dump()))
    
    db.commit()
    db.refresh(db_protocol)
    return db_protocol


@app.delete("/api/protocols/{protocol_id}")
def delete_protocol(protocol_id: UUID, db: Session = Depends(get_db)):
    """Jegyzőkönyv törlése"""
    db_protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not db_protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    
    db.delete(db_protocol)
    db.commit()
    return {"message": "Jegyzőkönyv törölve"}


@app.get("/api/protocols/{protocol_id}/download")
def download_protocol(protocol_id: UUID, db: Session = Depends(get_db)):
    """Word dokumentum letöltése"""
    protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    
    # Generate DOCX based on protocol type
    if protocol.protocol_type == "eph":
        docx_bytes = generate_eph_docx(protocol)
        filename = f"EPH_jegyzokonyv_{protocol.serial_number.replace('/', '_')}.docx"
    else:
        docx_bytes = generate_protocol_docx(protocol)
        filename = f"VBF_jegyzokonyv_{protocol.serial_number.replace('/', '_')}.docx"
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/next-serial")
def get_next_serial(db: Session = Depends(get_db)):
    """Következő sorszám generálása"""
    from datetime import datetime
    year = datetime.now().year
    
    # Find last serial number for this year
    last_protocol = db.query(models.Protocol).filter(
        models.Protocol.serial_number.like(f"{year}/%")
    ).order_by(models.Protocol.serial_number.desc()).first()
    
    if last_protocol:
        try:
            last_num = int(last_protocol.serial_number.split('/')[1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    return {"serial_number": f"{year}/{next_num:03d}"}


# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# ==================== DEFECT TYPES API ====================

@app.get("/api/defect-types", response_model=List[schemas.DefectType])
def list_defect_types(db: Session = Depends(get_db)):
    """Lista összes előre definiált hibatípus"""
    defect_types = db.query(models.DefectType).order_by(models.DefectType.id).all()
    return defect_types


@app.get("/api/defect-types/{defect_type_id}", response_model=schemas.DefectType)
def get_defect_type(defect_type_id: str, db: Session = Depends(get_db)):
    """Hibatípus lekérdezése"""
    defect_type = db.query(models.DefectType).filter(models.DefectType.id == defect_type_id).first()
    if not defect_type:
        raise HTTPException(status_code=404, detail="Hibatípus nem található")
    return defect_type


# ==================== TEMPLATE TEXTS API ====================

@app.get("/api/template-texts", response_model=List[schemas.TemplateText])
def list_template_texts(category: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista sablon szövegek, opcionálisan kategória szerint szűrve"""
    query = db.query(models.TemplateText)
    if category:
        query = query.filter(models.TemplateText.category == category)
    return query.order_by(models.TemplateText.id).all()


@app.get("/api/template-texts/{template_id}", response_model=schemas.TemplateText)
def get_template_text(template_id: str, db: Session = Depends(get_db)):
    """Sablon szöveg lekérdezése"""
    template = db.query(models.TemplateText).filter(models.TemplateText.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Sablon szöveg nem található")
    return template


# ==================== PROTOCOL DEFECTS API ====================

@app.get("/api/protocols/{protocol_id}/defects", response_model=List[schemas.ProtocolDefect])
def list_protocol_defects(protocol_id: UUID, db: Session = Depends(get_db)):
    """Lista jegyzőkönyvhöz rendelt hibák"""
    protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    return protocol.protocol_defects


@app.post("/api/protocols/{protocol_id}/defects", response_model=schemas.ProtocolDefect)
def add_protocol_defect(protocol_id: UUID, defect: schemas.ProtocolDefectCreate, db: Session = Depends(get_db)):
    """Hiba hozzáadása jegyzőkönyvhöz"""
    protocol = db.query(models.Protocol).filter(models.Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Jegyzőkönyv nem található")
    
    # Check if defect type exists (if provided)
    if defect.defect_type_id:
        defect_type = db.query(models.DefectType).filter(models.DefectType.id == defect.defect_type_id).first()
        if not defect_type:
            raise HTTPException(status_code=400, detail="Hibatípus nem található")
    
    db_defect = models.ProtocolDefect(
        protocol_id=protocol_id,
        defect_type_id=defect.defect_type_id,
        custom_description=defect.custom_description,
        location=defect.location,
        severity_override=defect.severity_override
    )
    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)
    return db_defect


@app.put("/api/protocols/{protocol_id}/defects/{defect_id}", response_model=schemas.ProtocolDefect)
def update_protocol_defect(protocol_id: UUID, defect_id: UUID, defect: schemas.ProtocolDefectCreate, db: Session = Depends(get_db)):
    """Hiba frissítése"""
    db_defect = db.query(models.ProtocolDefect).filter(
        models.ProtocolDefect.id == defect_id,
        models.ProtocolDefect.protocol_id == protocol_id
    ).first()
    if not db_defect:
        raise HTTPException(status_code=404, detail="Hiba nem található")
    
    for key, value in defect.model_dump(exclude_unset=True).items():
        setattr(db_defect, key, value)
    
    db.commit()
    db.refresh(db_defect)
    return db_defect


@app.delete("/api/protocols/{protocol_id}/defects/{defect_id}")
def delete_protocol_defect(protocol_id: UUID, defect_id: UUID, db: Session = Depends(get_db)):
    """Hiba törlése (és a hozzá tartozó képek is)"""
    db_defect = db.query(models.ProtocolDefect).filter(
        models.ProtocolDefect.id == defect_id,
        models.ProtocolDefect.protocol_id == protocol_id
    ).first()
    if not db_defect:
        raise HTTPException(status_code=404, detail="Hiba nem található")
    
    # Delete associated images from filesystem
    for image in db_defect.images:
        try:
            image_path = UPLOADS_DIR / image.image_path.replace("defect_images/", "")
            if image_path.exists():
                image_path.unlink()
        except Exception:
            pass  # Ignore file deletion errors
    
    db.delete(db_defect)
    db.commit()
    return {"message": "Hiba törölve"}


# ==================== DEFECT IMAGES API ====================

@app.post("/api/protocols/{protocol_id}/defects/{defect_id}/images", response_model=schemas.DefectImage)
async def upload_defect_image(
    protocol_id: UUID,
    defect_id: UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Kép feltöltése hibához"""
    # Verify defect exists and belongs to protocol
    db_defect = db.query(models.ProtocolDefect).filter(
        models.ProtocolDefect.id == defect_id,
        models.ProtocolDefect.protocol_id == protocol_id
    ).first()
    if not db_defect:
        raise HTTPException(status_code=404, detail="Hiba nem található")
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Csak képfájlok tölthetők fel (JPEG, PNG, GIF, WebP)")
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = '.jpg'
    unique_filename = f"{uuid_module.uuid4()}{file_ext}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fájl mentése sikertelen: {str(e)}")
    
    # Create database record
    db_image = models.DefectImage(
        protocol_defect_id=defect_id,
        image_path=f"defect_images/{unique_filename}",
        original_filename=file.filename,
        description=description
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image


@app.get("/api/uploads/{path:path}")
async def get_uploaded_file(path: str):
    """Feltöltött fájl lekérdezése"""
    file_path = Path("uploads") / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fájl nem található")
    return FileResponse(file_path)


@app.delete("/api/defect-images/{image_id}")
def delete_defect_image(image_id: UUID, db: Session = Depends(get_db)):
    """Kép törlése"""
    db_image = db.query(models.DefectImage).filter(models.DefectImage.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Kép nem található")
    
    # Delete file from filesystem
    try:
        image_path = UPLOADS_DIR / db_image.image_path.replace("defect_images/", "")
        if image_path.exists():
            image_path.unlink()
    except Exception:
        pass  # Ignore file deletion errors
    
    db.delete(db_image)
    db.commit()
    return {"message": "Kép törölve"}
