"""
Core Logic and Exporter Test Suite for Field Layout Editor & Robot Simulator.
"""

import os
import sys

from io_handler.map_exporter import export_to_yaml, import_from_yaml


def test_map_export_import():
    sample_data = {
        'field': {
            'width_m': 2.0,
            'height_m': 4.0,
            'width_cm': 200.0,
            'height_cm': 400.0,
            'width_mm': 2000.0,
            'height_mm': 4000.0,
            'scale_px_per_mm': 0.25,
            'scale_px_per_cm': 2.5,
            'width_px': 500,
            'height_px': 1000
        },
        'grid': {
            'size_cm': 10.0,
            'snap_enabled': True
        },
        'robot': {
            'type': 'robot',
            'name': 'Robot',
            'sides': 6,
            'diameter_cm': 30.0,
            'x_cm': 100.0,
            'y_cm': 50.0,
            'rotation_deg': 0.0,
            'color': '#e74c3c'
        },
        'objects': [
            {
                'type': 'home_box',
                'name': 'Home Area',
                'x_cm': 25.0,
                'y_cm': 25.0,
                'width_cm': 50.0,
                'height_cm': 50.0,
                'rotation_deg': 0.0,
                'color': '#2ecc71'
            },
            {
                'type': 'stand_cube',
                'name': 'Stand Cube 1',
                'x_cm': 80.0,
                'y_cm': 150.0,
                'width_cm': 30.0,
                'height_cm': 30.0,
                'rotation_deg': 0.0,
                'color': '#e67e22'
            },
            {
                'type': 'wall',
                'name': 'Tembok 1',
                'x_cm': 0.0,
                'y_cm': 200.0,
                'width_cm': 200.0,
                'height_cm': 10.0,
                'rotation_deg': 0.0,
                'color': '#34495e'
            }
        ]
    }

    test_file = "maps.yaml"
    # Export to maps.yaml
    success = export_to_yaml(test_file, sample_data)
    assert success, "Export to maps.yaml failed"
    assert os.path.exists(test_file), "maps.yaml file was not created"

    # Import back from maps.yaml
    loaded = import_from_yaml(test_file)
    assert loaded['field']['width_m'] == 2.0
    assert loaded['field']['height_m'] == 4.0
    assert loaded['field']['width_px'] == 500
    assert loaded['field']['height_px'] == 1000
    assert loaded['robot']['sides'] == 6
    assert loaded['robot']['diameter_cm'] == 30.0
    assert len(loaded['objects']) == 3

    print("[OK] All YAML Export/Import Tests Passed!")
    print(f"Sample exported maps.yaml content:\n{open(test_file).read()}")


if __name__ == "__main__":
    test_map_export_import()
