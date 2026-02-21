import xml.etree.ElementTree as ET
import zipfile
import io

def parse_padfx_content(file_bytes: bytes):
    try:
        # PZIP -> extract DataSource.padf
        with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zip_ref:
            if 'DataSource.padf' not in zip_ref.namelist():
                raise ValueError("A feltöltött fájl nem tartalmaz DataSource.padf XML adatot.")
            xml_content = zip_ref.read('DataSource.padf')
    except zipfile.BadZipFile:
        raise ValueError("Érvénytelen ZIP / PADFX formátum.")

    # Parse XML
    tree = ET.parse(io.BytesIO(xml_content))
    root = tree.getroot()

    nodes = {}
    data_node = root.find('Data')
    if data_node is None:
        raise ValueError("A PADF fájl nem tartalmaz strukturált adatokat (<Data> tag).")

    for so in data_node.findall('SO'):
        node_id = so.get('Id')
        name = so.findtext('N', default='Unknown')
        pid = so.findtext('PID', default='-1')
        
        # Extract Measurements
        measurements = []
        ms_node = so.find('Ms')
        if ms_node is not None:
            for m in ms_node.findall('M'):
                m_type = m.findtext('MID', default='Unknown')
                # Results
                results = {}
                rs_node = m.find('Rs')
                if rs_node is not None:
                    for r in rs_node.findall('R'):
                        r_id = r.get('Id')
                        r_val = r.findtext('V', default='')
                        results[r_id] = r_val

                measurements.append({
                    'type': m_type,
                    'results': results,
                })
                
        nodes[node_id] = {
            'id': node_id,
            'name': name,
            'pid': pid,
            'measurements': measurements,
            'children': []
        }

    # Build Tree to group measurements by Object
    root_nodes = []
    for node_id, node in nodes.items():
        pid = node['pid']
        if pid in nodes:
            nodes[pid]['children'].append(node)
        else:
            root_nodes.append(node)

    # Flatten structured measurements for frontend
    extracted_circuits = []
    
    # Rpe, Zs, Insulation results mapping by MID / R IDs based on the previous manual analysis
    # MID=20 -> Zs / Loop (R_id 43 is Ohm)
    # MID=16 -> Line / ZLine (R_id 205 is Ohm)
    # MID=2 -> Insulation (R_id 1 is Ohm, 2 is Ohm, 3 is Ohm, wait MID=2 is Riso)
    # Actually, let's just dump all measurements with their associated Object name
    
    def walk_tree(node, path=""):
        current_path = f"{path} / {node['name']}".strip(" / ")
        
        for m in node['measurements']:
            m_type = m['type']
            results = m['results']
            
            # Simple heuristic mapping for the frontend to digest
            circuit_data = {
                "circuit_name": current_path,
                "raw_mid": m_type,
                "raw_results": results
            }
            
            # Parse Zs (Loop Impedance) MID 20 (Z-Loop) or 16 (Z-Line)
            if m_type == '20':
                circuit_data['zs_value_ohm'] = results.get('43', '').replace('Ohm', '')
            
            # Additional mappings can be added here
            extracted_circuits.append(circuit_data)

        for child in node['children']:
            walk_tree(child, current_path)

    for rn in root_nodes:
        walk_tree(rn)

    return {
        "status": "success",
        "circuits": extracted_circuits,
        "raw_nodes": root_nodes
    }
