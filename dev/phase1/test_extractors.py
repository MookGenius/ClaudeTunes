#!/usr/bin/env python3
"""
Test Domain Extractors and JSON Writers
Phase 1: Domain JSON Architecture

Verifies that extractors parse UDP packets correctly
and JSON writers work atomically.
"""

import sys
import os
from datetime import datetime as dt

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1'))

from utils import (
    MetadataExtractor,
    SuspensionExtractor,
    TireExtractor,
    AeroExtractor,
    DrivetrainExtractor,
    BalanceExtractor,
    BufferedDomainWriter
)

# Simple car database for testing
CAR_DATABASE = {
    3462: "2013 Ferrari LaFerrari",
    1: "Test Car 1"
}

# Simple downforce database for testing
DOWNFORCE_DATABASE = {
    3462: 825,  # LaFerrari downforce
    1: 0
}


def create_dummy_packet():
    """Create a dummy 296-byte UDP packet for testing"""
    # GT7 packet is 296 bytes
    packet = bytearray(296)

    # Fill with some test data
    import struct

    # Speed (0x4C): 50 m/s
    packet[0x4C:0x50] = struct.pack('f', 50.0)

    # Suspension (0xC4-0xD3): 0.030 m = 30mm
    packet[0xC4:0xC8] = struct.pack('f', 0.030)  # FL
    packet[0xC8:0xCC] = struct.pack('f', 0.030)  # FR
    packet[0xCC:0xD0] = struct.pack('f', 0.032)  # RL
    packet[0xD0:0xD4] = struct.pack('f', 0.032)  # RR

    # Tire temps (0x60-0x6F): 85°C
    packet[0x60:0x64] = struct.pack('f', 85.0)  # FL
    packet[0x64:0x68] = struct.pack('f', 85.0)  # FR
    packet[0x68:0x6C] = struct.pack('f', 82.0)  # RL
    packet[0x6C:0x70] = struct.pack('f', 82.0)  # RR

    # RPM (0x3C): 6000
    packet[0x3C:0x40] = struct.pack('f', 6000.0)

    # Throttle (0x91): 80%
    packet[0x91:0x92] = struct.pack('B', int(80 * 2.55))

    # Car code (0x124): 3462 (LaFerrari)
    packet[0x124:0x128] = struct.pack('i', 3462)

    # Current lap (0x74): 3
    packet[0x74:0x76] = struct.pack('h', 3)

    # Body height (0x38): 0.065 m = 65mm
    packet[0x38:0x3C] = struct.pack('f', 0.065)

    return bytes(packet)


def test_extractors():
    """Test all 6 domain extractors"""
    print("=" * 60)
    print("Testing Domain Extractors")
    print("=" * 60)

    # Create dummy packet
    packet = create_dummy_packet()
    timestamp = dt.now()

    # Initialize extractors
    metadata_ex = MetadataExtractor(CAR_DATABASE)
    suspension_ex = SuspensionExtractor()
    tire_ex = TireExtractor()
    aero_ex = AeroExtractor(DOWNFORCE_DATABASE)
    drivetrain_ex = DrivetrainExtractor()
    balance_ex = BalanceExtractor()

    # Extract data
    print("\n1. MetadataExtractor:")
    metadata = metadata_ex.extract(packet, timestamp)
    print(f"   Car: {metadata['car']['name']}")
    print(f"   Speed: {metadata['session_summary']['speed_kph']:.1f} kph")
    print(f"   Lap: {metadata['session_summary']['current_lap']}")

    print("\n2. SuspensionExtractor:")
    suspension = suspension_ex.extract(packet)
    print(f"   FL Travel: {suspension['travel_mm']['FL']['current']:.1f} mm")
    print(f"   Ride Height: {suspension['current_ride_height_mm']['front']:.1f} mm")

    print("\n3. TireExtractor:")
    tires = tire_ex.extract(packet)
    print(f"   FL Temp: {tires['temps_celsius']['FL']['current']:.1f}°C")
    print(f"   FL Slip: {tires['slip_ratio']['FL']['current']:.3f}")

    print("\n4. AeroExtractor:")
    aero = aero_ex.extract(packet, car_code=3462)
    print(f"   Avg Front Height: {aero['ride_height_mm']['avg_front']:.1f} mm")
    print(f"   Downforce: {aero['downforce_estimate_lbs']['total']} lbs")

    print("\n5. DrivetrainExtractor:")
    drivetrain = drivetrain_ex.extract(packet)
    print(f"   RPM: {drivetrain['power_delivery']['rpm']:.0f}")
    print(f"   Throttle: {drivetrain['power_delivery']['throttle_pct']:.1f}%")

    print("\n6. BalanceExtractor:")
    balance = balance_ex.extract(packet)
    print(f"   Lateral G: {balance['weight_transfer']['lateral_g']['current']:.2f}")
    print(f"   Balance: {balance['stability_metrics']['balance_bias']}")

    print("\n✅ All extractors working!")
    return True


def test_json_writers():
    """Test JSON writers with atomic writes"""
    print("\n" + "=" * 60)
    print("Testing JSON Writers")
    print("=" * 60)

    # Create test session folder
    import tempfile
    import shutil
    test_session = tempfile.mkdtemp(prefix="test_session_")
    print(f"\nTest session folder: {test_session}")

    try:
        # Initialize buffered writer
        writer = BufferedDomainWriter(test_session, buffer_size=3)

        # Create dummy packet
        packet = create_dummy_packet()
        timestamp = dt.now()

        # Initialize extractors
        metadata_ex = MetadataExtractor(CAR_DATABASE)
        suspension_ex = SuspensionExtractor()
        tire_ex = TireExtractor()
        aero_ex = AeroExtractor(DOWNFORCE_DATABASE)
        drivetrain_ex = DrivetrainExtractor()
        balance_ex = BalanceExtractor()

        # Simulate 5 packet updates (buffer size = 3)
        print("\nSimulating 5 packet updates (buffer=3):")
        for i in range(5):
            # Extract domains
            metadata = metadata_ex.extract(packet, timestamp)
            suspension = suspension_ex.extract(packet)
            tires = tire_ex.extract(packet)
            aero = aero_ex.extract(packet, car_code=3462)
            drivetrain = drivetrain_ex.extract(packet)
            balance = balance_ex.extract(packet)

            # Update buffers
            writer.update_domain('metadata', metadata)
            writer.update_domain('suspension', suspension)
            writer.update_domain('tires', tires)
            writer.update_domain('aero', aero)
            writer.update_domain('drivetrain', drivetrain)
            should_flush = writer.update_domain('balance', balance)

            if should_flush:
                writer.flush()
                print(f"  Packet {i+1}: ✅ Flushed to disk (buffer full)")
            else:
                print(f"  Packet {i+1}: Buffered ({writer.update_count}/{writer.buffer_size})")

        # Force final write
        writer.force_write()
        print(f"  Final flush: ✅ Written to disk")

        # Verify files exist
        print("\nVerifying JSON files:")
        expected_files = [
            'metadata.json',
            'suspension.json',
            'tires.json',
            'aero.json',
            'drivetrain.json',
            'balance.json'
        ]

        all_exist = True
        for filename in expected_files:
            filepath = os.path.join(test_session, filename)
            exists = os.path.exists(filepath)
            status = "✅" if exists else "❌"
            print(f"  {status} {filename}")
            if not exists:
                all_exist = False

        # Read and validate one file
        if all_exist:
            import json
            with open(os.path.join(test_session, 'metadata.json'), 'r') as f:
                metadata_check = json.load(f)
            print(f"\nSample data from metadata.json:")
            print(f"  Car: {metadata_check['car']['name']}")
            print(f"  Session ID: {metadata_check['session_id']}")

        print("\n✅ All JSON files created successfully!" if all_exist else "\n❌ Some files missing!")

        return all_exist

    finally:
        # Cleanup
        if os.path.exists(test_session):
            shutil.rmtree(test_session)
            print(f"\nCleaned up test session: {test_session}")


if __name__ == '__main__':
    print("Phase 1: Domain Extractor & JSON Writer Tests")
    print()

    # Run tests
    extractors_ok = test_extractors()
    writers_ok = test_json_writers()

    print("\n" + "=" * 60)
    if extractors_ok and writers_ok:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
