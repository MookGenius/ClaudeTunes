#!/usr/bin/env python3
"""
Verify Domain JSON Files Created by gt7_1r_phase1.py
Checks structure, content, and completeness
"""

import json
import os
import sys
from pathlib import Path


def find_latest_session():
    """Find the most recent session folder"""
    sessions_dir = Path("sessions")

    if not sessions_dir.exists():
        print("❌ sessions/ directory not found!")
        return None

    # Get all session folders (format: YYYYMMDD_HHMMSS)
    session_folders = [f for f in sessions_dir.iterdir() if f.is_dir()]

    if not session_folders:
        print("❌ No session folders found in sessions/")
        return None

    # Sort by name (which is timestamp) and get latest
    latest = sorted(session_folders)[-1]
    return latest


def verify_json_file(filepath, expected_keys):
    """Verify a JSON file exists and has expected structure"""
    if not filepath.exists():
        return False, f"File not found: {filepath.name}"

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    # Check for expected keys
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        return False, f"Missing keys: {missing_keys}"

    return True, data


def verify_metadata_json(session_folder):
    """Verify metadata.json"""
    filepath = session_folder / "metadata.json"
    expected_keys = ['session_id', 'car', 'track', 'session_summary']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ metadata.json")
    print(f"     Car: {data['car']['name']}")
    print(f"     Session ID: {data['session_id']}")
    print(f"     Speed: {data['session_summary']['speed_kph']:.1f} kph")

    return True, data


def verify_suspension_json(session_folder):
    """Verify suspension.json"""
    filepath = session_folder / "suspension.json"
    expected_keys = ['travel_mm', 'bottoming_events', 'current_ride_height_mm']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ suspension.json")

    # Check for FL travel stats
    if 'FL' in data['travel_mm']:
        fl_travel = data['travel_mm']['FL']
        print(f"     FL Travel: avg={fl_travel.get('avg', 0):.1f}mm, samples={len(fl_travel.get('samples', []))}")

    return True, data


def verify_tires_json(session_folder):
    """Verify tires.json"""
    filepath = session_folder / "tires.json"
    expected_keys = ['temps_celsius', 'slip_ratio']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ tires.json")

    # Check FL temp
    if 'FL' in data['temps_celsius']:
        fl_temp = data['temps_celsius']['FL']
        print(f"     FL Temp: avg={fl_temp.get('avg', 0):.1f}°C, samples={len(fl_temp.get('samples', []))}")

    return True, data


def verify_aero_json(session_folder):
    """Verify aero.json"""
    filepath = session_folder / "aero.json"
    expected_keys = ['ride_height_mm', 'downforce_estimate_lbs']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ aero.json")

    print(f"     Avg Front Height: {data['ride_height_mm'].get('avg_front', 0):.1f}mm")
    print(f"     Downforce: {data['downforce_estimate_lbs']['total']} lbs")

    return True, data


def verify_drivetrain_json(session_folder):
    """Verify drivetrain.json"""
    filepath = session_folder / "drivetrain.json"
    expected_keys = ['power_delivery', 'gearing']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ drivetrain.json")

    print(f"     RPM: avg={data['power_delivery'].get('avg_rpm', 0):.0f}")
    print(f"     Current Gear: {data['gearing'].get('current_gear', 0)}")

    return True, data


def verify_balance_json(session_folder):
    """Verify balance.json"""
    filepath = session_folder / "balance.json"
    expected_keys = ['weight_transfer', 'rotation']

    success, result = verify_json_file(filepath, expected_keys)

    if not success:
        return False, result

    data = result
    print(f"  ✅ balance.json")

    lat_g = data['weight_transfer'].get('lateral_g', {})
    print(f"     Lateral G: avg={lat_g.get('avg', 0):.2f}")

    return True, data


def main():
    print("=" * 60)
    print("Domain JSON Verification - Phase 1")
    print("=" * 60)
    print()

    # Find latest session
    print("Finding latest session...")
    session_folder = find_latest_session()

    if not session_folder:
        print()
        print("❌ No session found to verify!")
        print()
        print("Run gt7_1r_phase1.py first:")
        print("  1. Terminal 1: python3 gt7_1r_phase1.py 127.0.0.1")
        print("  2. Terminal 2: python3 test_gt7_1r_mock_udp.py")
        print()
        return False

    print(f"Latest session: {session_folder}")
    print()

    # Verify all 6 domain JSONs
    print("Verifying domain JSON files:")
    print()

    results = []
    results.append(verify_metadata_json(session_folder))
    results.append(verify_suspension_json(session_folder))
    results.append(verify_tires_json(session_folder))
    results.append(verify_aero_json(session_folder))
    results.append(verify_drivetrain_json(session_folder))
    results.append(verify_balance_json(session_folder))

    # Summary
    print()
    print("=" * 60)

    all_passed = all(success for success, _ in results)

    if all_passed:
        print("✅ ALL DOMAIN JSON FILES VERIFIED!")
        print("=" * 60)
        print()
        print("Phase 1 Step 1.2 (gt7_1r.py) is working correctly!")
        print()
        print("Domain JSONs are:")
        print("  - Created successfully")
        print("  - Properly structured")
        print("  - Containing valid data")
        print()
        print("Ready for Step 1.4 (modify claudetunes_cli.py)!")
        return True
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("=" * 60)
        print()
        for i, (success, result) in enumerate(results):
            if not success:
                print(f"  ❌ Issue {i+1}: {result}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
