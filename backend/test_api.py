import requests

url = 'http://127.0.0.1:8000/api/protocols'
data = {
    'serial_number': 'TEST-2026-002',
    'location_address': 'Budapest, Teszt utca 1.',
    'network_type': 'TN-S',
    'inspection_type': 'Első ellenőrzés (VBF)',
    'client_name': 'Teszt Elek',
    'inspection_date': '2026-02-20',
    'inspector_name': 'Kovács Béla',
    'protocol_type': 'vbf'
}

print('Sending request to', url)
response = requests.post(url, json=data)

print(response.status_code)
print(response.json())
