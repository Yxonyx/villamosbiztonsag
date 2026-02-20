import requests
import json
import os
import zipfile

API_URL = "http://127.0.0.1:8000/api"
TEST_IMAGE_PATH = r"c:\Users\User\Downloads\Villamos_biztons_gi_ellen_rz_s (1)\Uploads\IMG_20260213_183436.jpg"

def run_test():
    print("1. Creating a new protocol...")
    protocol_data = {
        "serial_number": "E2E-TEST-002",
        "location_address": "Test Képfeltöltés Utca 1.",
        "network_type": "TN-S",
        "client_name": "E2E Teszter Kft.",
        "inspection_type": "Első ellenőrzés (VBF)",
        "inspection_date": "2026-02-20",
        "inspector_name": "Kovács Teszter",
        "status": "draft",
        "protocol_type": "vbf",
        "rpe_measurements": [],
        "insulation_measurements": [],
        "loop_impedance_measurements": [],
        "rcd_tests": [],
        "summary_results": []
    }
    
    resp = requests.post(f"{API_URL}/protocols", json=protocol_data)
    resp.raise_for_status()
    protocol = resp.json()
    protocol_id = protocol['id']
    print(f"   -> Protocol created: {protocol_id}")

    print("2. Adding a defect...")
    defect_data = {
        "custom_description": "Ez egy teszt hiba, amihez képet fogunk csatolni a teljes folyamat tesztelésére!",
        "location": "Főelosztó (E2E)"
    }
    resp = requests.post(f"{API_URL}/protocols/{protocol_id}/defects", json=defect_data)
    resp.raise_for_status()
    defect = resp.json()
    defect_id = defect['id']
    print(f"   -> Defect created: {defect_id}")

    print(f"3. Uploading test image: {TEST_IMAGE_PATH}")
    if not os.path.exists(TEST_IMAGE_PATH):
        print("   -> ERROR: Test image not found at path")
        return
        
    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": ("test_image.jpg", f, "image/jpeg")}
        resp = requests.post(f"{API_URL}/protocols/{protocol_id}/defects/{defect_id}/images", files=files)
        resp.raise_for_status()
        img_info = resp.json()
        print(f"   -> Image uploaded. Server path: {img_info.get('image_path')}")

    print("4. Downloading DOCX...")
    resp = requests.get(f"{API_URL}/protocols/{protocol_id}/download")
    resp.raise_for_status()
    
    docx_path = "test_output.docx"
    with open(docx_path, "wb") as f:
        f.write(resp.content)
    print(f"   -> DOCX saved to {docx_path}, size: {os.path.getsize(docx_path)} bytes")

    print("5. Verifying DOCX contents (checking for media files)...")
    found_images = []
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        for info in docx_zip.infolist():
            if info.filename.startswith("word/media/"):
                found_images.append(info.filename)
                
    if found_images:
        print(f"   -> SUCCESS! Found images embedded in DOCX: {found_images}")
    else:
        print("   -> FAILED! No images found inside the generated DOCX.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Error during E2E test: {e}")
