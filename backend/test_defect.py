import requests
import json
import glob
import os

base_url = 'http://127.0.0.1:8000/api'

# 1. Get the protocol ID
print('--- Fetching protocols ---')
try:
    protocols = requests.get(f'{base_url}/protocols').json()
    if not protocols:
        print('No protocols found')
        exit(1)
    protocol_id = protocols[0]['id']
    print(f'Protocol ID: {protocol_id}')
except Exception as e:
    print(f'Error fetching protocols: {e}')
    exit(1)

# 2. Add a defect
print('\n--- Adding a defect ---')
defect_data = {
    'custom_description': 'A fali kábel szigetelése megsérült.',
    'location': 'Folyosó'
}
try:
    defect_response = requests.post(f'{base_url}/protocols/{protocol_id}/defects', json=defect_data)
    if defect_response.status_code != 200:
        print(f'Error adding defect: {defect_response.status_code} - {defect_response.text}')
        exit(1)
    defect = defect_response.json()
    defect_id = defect['id']
    print(f'Defect ID: {defect_id}')
except Exception as e:
    print(f'Exception adding defect: {e}')
    exit(1)

# 3. Download the mock image
image_path = os.path.join(os.path.dirname(__file__), 'mock_image.jpg')
try:
    img_data = requests.get("https://picsum.photos/200/300").content
    with open(image_path, 'wb') as handler:
        handler.write(img_data)
    print(f"Mock image downloaded to {image_path}")
except Exception as e:
    print(f"Error downloading mock image: {e}")

# 4. Upload an image for the defect
print('\n--- Uploading image ---')
try:
    with open(image_path, 'rb') as f:
        files = {'file': ('mock_image.jpg', f, 'image/jpeg')}
        img_response = requests.post(f'{base_url}/protocols/{protocol_id}/defects/{defect_id}/images', files=files)
        print(f'Image upload status: {img_response.status_code}')
        if img_response.status_code != 200:
             print(f'Image upload error: {img_response.text}')
except Exception as e:
    print(f'Error uploading image: {e}')

# 5. Generate DOCX
print('\n--- Generating DOCX ---')
try:
    docx_response = requests.get(f'{base_url}/protocols/{protocol_id}/download')
    if docx_response.status_code == 200:
        with open('TEST-2026-002_with_image.docx', 'wb') as f:
            f.write(docx_response.content)
        print('DOCX successfully saved as TEST-2026-002_with_image.docx')
    else:
        print('Failed to generate DOCX:', docx_response.text)
except Exception as e:
    print(f'Error generating docx: {e}')
