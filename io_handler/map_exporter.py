"""
Map Exporter and Importer Module for Field Layout & Robot Simulator.
Handles reading and writing YAML map configuration files (maps.yaml).
"""

import os
import math

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def export_to_yaml(file_path: str, map_data: dict) -> bool:
    if HAS_YAML:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(map_data, f, default_flow_style=False, sort_keys=False, indent=2)
        return True
    else:
        # Fallback simple manual YAML writer
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Field Map Configuration\n")
            f.write("field:\n")
            for k, v in map_data.get('field', {}).items():
                f.write(f"  {k}: {v}\n")
            f.write("\ngrid:\n")
            for k, v in map_data.get('grid', {}).items():
                f.write(f"  {k}: {v}\n")
            f.write("\nrobot:\n")
            for k, v in map_data.get('robot', {}).items():
                if isinstance(v, dict):
                    f.write(f"  {k}:\n")
                    for sk, sv in v.items():
                        f.write(f"    {sk}: {sv}\n")
                else:
                    f.write(f"  {k}: {v}\n")
            f.write("\nobjects:\n")
            for obj in map_data.get('objects', []):
                f.write("  - ")
                first = True
                for k, v in obj.items():
                    if not first:
                        f.write("    ")
                    f.write(f"{k}: {v}\n")
                    first = False
        return True


def import_from_yaml(file_path: str) -> dict:
    """
    Import map configuration data from a YAML file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if HAS_YAML:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data else {}
    else:
        data = {'field': {}, 'grid': {}, 'robot': {}, 'objects': []}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        current_section = None
        current_sub_sec = None
        current_obj = None
        for line in content.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            if line_str.endswith(":") and not line_str.startswith("-") and not line.startswith("  "):
                sec = line_str[:-1].strip()
                if sec in ['field', 'grid', 'robot', 'objects']:
                    current_section = sec
                    current_sub_sec = None
                continue

            if current_section == 'robot':
                if line.startswith("    ") and ":" in line_str and current_sub_sec:
                    k, v = line_str.split(":", 1)
                    if current_sub_sec not in data['robot']:
                        data['robot'][current_sub_sec] = {}
                    data['robot'][current_sub_sec][k.strip()] = _parse_val(v.strip())
                elif line.startswith("  ") and ":" in line_str:
                    k, v = line_str.split(":", 1)
                    v_str = v.strip()
                    if v_str == "":
                        current_sub_sec = k
                        data['robot'][current_sub_sec] = {}
                    else:
                        current_sub_sec = None
                        data['robot'][k] = _parse_val(v_str)

            elif current_section == 'objects':
                if line_str.startswith("-"):
                    current_obj = {}
                    data['objects'].append(current_obj)
                    kv = line_str[1:].strip()
                    if ":" in kv:
                        k, v = kv.split(":", 1)
                        current_obj[k.strip()] = _parse_val(v.strip())
                elif current_obj is not None and ":" in line_str:
                    k, v = line_str.split(":", 1)
                    current_obj[k.strip()] = _parse_val(v.strip())

            elif current_section in ['field', 'grid']:
                if ":" in line_str:
                    k, v = line_str.split(":", 1)
                    data[current_section][k.strip()] = _parse_val(v.strip())

        return data


def _parse_val(val_str: str):
    if val_str.lower() == 'true':
        return True
    if val_str.lower() == 'false':
        return False
    try:
        if '.' in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str.strip('"\'')


def export_robot_to_yaml(file_path: str, robot_dict: dict) -> bool:
    """
    Export robot configuration data dictionary to a YAML file (robot.yaml).
    """
    data = {'robot': robot_dict}
    if HAS_YAML:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        return True
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Robot Specification Configuration\n")
            f.write("robot:\n")
            for k, v in robot_dict.items():
                if isinstance(v, dict):
                    f.write(f"  {k}:\n")
                    for sk, sv in v.items():
                        f.write(f"    {sk}: {sv}\n")
                else:
                    f.write(f"  {k}: {v}\n")
        return True


def import_robot_from_yaml(file_path: str) -> dict:
    """
    Import robot configuration data from a robot YAML file.
    Returns robot data dictionary.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if HAS_YAML:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                if 'robot' in data and isinstance(data['robot'], dict):
                    return data['robot']
                return data
            return {}
    else:
        full_data = import_from_yaml(file_path)
        if 'robot' in full_data and isinstance(full_data['robot'], dict) and full_data['robot']:
            return full_data['robot']
        return full_data
