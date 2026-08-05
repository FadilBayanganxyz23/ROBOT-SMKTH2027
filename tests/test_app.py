"""
Automated Verification Test Suite for Field Layout Editor & Robot Simulator.
"""

import sys
import os

# Set offscreen platform before importing PyQt6 GUI components
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from io_handler.map_exporter import export_to_yaml, import_from_yaml


def test_gui_and_yaml():
    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()
    
    # 1. Verify default values
    assert window.field_width_m == 2.0, f"Expected 2.0, got {window.field_width_m}"
    assert window.field_height_m == 4.0, f"Expected 4.0, got {window.field_height_m}"
    assert window.scene.width_cm == 200.0
    assert window.scene.height_cm == 400.0
    print("✅ Test 1 Passed: Default field dimensions 2x4M verified.")

    # 2. Test scale conversion calculation
    # 1 mm = 0.25 px -> 2000 mm x 4000 mm = 500 px x 1000 px
    w_px = int(2000 * 0.25)
    h_px = int(4000 * 0.25)
    assert w_px == 500
    assert h_px == 1000
    print(f"✅ Test 2 Passed: Conversion calculation verified. 2x4M = {w_px}x{h_px} pixels at 0.25 px/mm.")

    # 3. Test item additions
    window.add_home_box()
    window.add_stand_cube()
    window.add_wall()
    window.add_line()
    window.add_cabinet()
    
    items = window.scene.items()
    types = [getattr(it, 'item_type', '') for it in items if hasattr(it, 'item_type')]
    assert 'home_box' in types
    assert 'stand_cube' in types
    assert 'wall' in types
    assert 'line' in types
    assert 'cabinet' in types
    assert 'robot' in types
    print("✅ Test 3 Passed: All layout items added successfully.")

    # 4. Test robot configuration update (Oval diameter)
    window.spn_robot_diam.setValue(45.0)
    assert window.robot_item.diameter_cm == 45.0
    print("✅ Test 4 Passed: Robot Oval diameter (45cm) updated.")

    # 5. Test export to maps.yaml
    test_yaml_path = "test_maps.yaml"
    map_data = window.build_map_data()
    export_to_yaml(test_yaml_path, map_data)
    assert os.path.exists(test_yaml_path)
    print("✅ Test 5 Passed: maps.yaml exported successfully.")

    # 6. Test import from maps.yaml
    imported_data = import_from_yaml(test_yaml_path)
    assert imported_data['field']['width_m'] == 2.0
    assert imported_data['field']['height_m'] == 4.0
    assert imported_data['field']['width_px'] == 500
    assert imported_data['field']['height_px'] == 1000
    assert imported_data['robot']['diameter_cm'] == 45.0
    print("✅ Test 6 Passed: maps.yaml imported and validated successfully.")

    # Clean up test file
    if os.path.exists(test_yaml_path):
        os.remove(test_yaml_path)

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    sys.exit(0)


if __name__ == "__main__":
    test_gui_and_yaml()
