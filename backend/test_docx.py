import requests
import json
import os

API_URL = "http://127.0.0.1:8000/api"

payload = {
    "protocol_type": "vbf",
    "serial_number": "VBF-TEST-2026-999",
    "location_address": "Test Street 1.",
    "network_type": "TN-S",
    "inspection_type": "Első ellenőrzés",
    "client_name": "Test Client Kft.",
    "inspection_date": "2026-02-20",
    "inspector_name": "Test Elek",
    "status": "completed",
    "rpe_measurements": [],
    "insulation_measurements": [
        {
            "circuit_name": "Világítás Nappali",
            "breaker_type": "B",
            "breaker_value": 10.0,
            "wire_material": "Cu",
            "wire_cross_section": 1.5,
            "zs_value_ohm": 0.45,
            "du_value_percent": 1.5,
            "fire_rating": "A",
            "ln_value_mohm": 100.0,
            "lpe_value_mohm": 150.0,
            "npe_value_mohm": 120.0,
            "passed": True
        }
    ],
    "loop_impedance_measurements": [],
    "rcd_tests": [],
    "summary_results": []
}

def test_api():
    # Create protocol
    print("Creating protocol...")
    res = requests.post(f"{API_URL}/protocols", json=payload)
    if not res.ok:
        print(f"Error creating protocol: {res.text}")
        return
    
    data = res.json()
    protocol_id = data.get("id")
    print(f"Protocol created with ID: {protocol_id}")
    
    # Download DOCX
    print("Generating DOCX...")
    docx_res = requests.get(f"{API_URL}/protocols/{protocol_id}/download")
    if docx_res.ok:
        with open("test_output.docx", "wb") as f:
            f.write(docx_res.content)
        print(f"Successfully downloaded DOCX to test_output.docx! File size: {len(docx_res.content)} bytes")
    else: # Error
        print(f"Error downloading docx: {docx_res.text}")

if __name__ == "__main__":
    test_api()
