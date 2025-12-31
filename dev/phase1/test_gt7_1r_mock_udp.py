#!/usr/bin/env python3
"""
Mock UDP Packet Sender for Testing gt7_1r_phase1.py
Simulates GT7 PlayStation sending telemetry data
"""

import socket
import struct
import time
from Crypto.Cipher import Salsa20


def create_mock_gt7_packet(packet_id=1, lap=1, car_code=3462):
    """Create a mock 296-byte GT7 packet with realistic data"""
    packet = bytearray(296)

    # Magic number (0x00-0x03) - GT7 packet identifier "G7S0"
    packet[0x00:0x04] = struct.pack('I', 0x47375330)

    # Position (0x04-0x0F) - arbitrary position
    packet[0x04:0x08] = struct.pack('f', 100.0)  # pos_x
    packet[0x08:0x0C] = struct.pack('f', 5.0)    # pos_y
    packet[0x0C:0x10] = struct.pack('f', 200.0)  # pos_z

    # Velocity (0x10-0x1B) - ~50 m/s forward
    packet[0x10:0x14] = struct.pack('f', 0.0)    # vel_x
    packet[0x14:0x18] = struct.pack('f', 0.0)    # vel_y
    packet[0x18:0x1C] = struct.pack('f', 50.0)   # vel_z (forward)

    # Rotation (0x1C-0x27) - slight roll
    packet[0x1C:0x20] = struct.pack('f', 0.05)   # pitch
    packet[0x20:0x24] = struct.pack('f', 0.0)    # yaw
    packet[0x24:0x28] = struct.pack('f', 0.02)   # roll

    # Angular velocity (0x2C-0x37)
    packet[0x2C:0x30] = struct.pack('f', 0.1)    # ang_vel_x
    packet[0x30:0x34] = struct.pack('f', 0.0)    # ang_vel_y
    packet[0x34:0x38] = struct.pack('f', 0.5)    # ang_vel_z

    # Body height / ride height (0x38) - 65mm = 0.065m
    packet[0x38:0x3C] = struct.pack('f', 0.065)

    # RPM (0x3C) - 6000 RPM
    packet[0x3C:0x40] = struct.pack('f', 6000.0)

    # Fuel (0x44-0x4B) - 50L in 100L tank
    packet[0x44:0x48] = struct.pack('f', 50.0)   # fuel_level
    packet[0x48:0x4C] = struct.pack('f', 100.0)  # fuel_capacity

    # Speed (0x4C) - 50 m/s
    packet[0x4C:0x50] = struct.pack('f', 50.0)

    # Boost (0x50) - 1.0 = no boost
    packet[0x50:0x54] = struct.pack('f', 1.0)

    # Oil pressure (0x54)
    packet[0x54:0x58] = struct.pack('f', 5.5)

    # Water temp (0x58) - 90°C
    packet[0x58:0x5C] = struct.pack('f', 90.0)

    # Oil temp (0x5C) - 95°C
    packet[0x5C:0x60] = struct.pack('f', 95.0)

    # Tire temperatures (0x60-0x6F) - 85°C average
    packet[0x60:0x64] = struct.pack('f', 85.0)   # FL
    packet[0x64:0x68] = struct.pack('f', 85.0)   # FR
    packet[0x68:0x6C] = struct.pack('f', 82.0)   # RL
    packet[0x6C:0x70] = struct.pack('f', 82.0)   # RR

    # Packet ID (0x70)
    packet[0x70:0x74] = struct.pack('i', packet_id)

    # Current lap (0x74)
    packet[0x74:0x76] = struct.pack('h', lap)

    # Total laps (0x76)
    packet[0x76:0x78] = struct.pack('h', 5)

    # Best lap time (0x78) - 90 seconds
    packet[0x78:0x7C] = struct.pack('i', 90000)

    # Last lap time (0x7C) - 92 seconds
    packet[0x7C:0x80] = struct.pack('i', 92000)

    # Time on track (0x80) - 5 minutes
    packet[0x80:0x84] = struct.pack('i', 300000)

    # Race start position (0x84)
    packet[0x84:0x86] = struct.pack('h', 3)

    # Num cars (0x86)
    packet[0x86:0x88] = struct.pack('h', 20)

    # Rev warning (0x88) - 7000 RPM
    packet[0x88:0x8A] = struct.pack('H', 7000)

    # Rev limiter (0x8A) - 7500 RPM
    packet[0x8A:0x8C] = struct.pack('H', 7500)

    # Estimated top speed (0x8C)
    packet[0x8C:0x8E] = struct.pack('h', 320)

    # Flags (0x8E) - TCS on, ASM off
    flags = 0x0040  # TCS bit set
    packet[0x8E:0x90] = struct.pack('H', flags)

    # Gear data (0x90) - 4th gear, suggest 5th
    current_gear = 4
    suggested_gear = 5
    gear_byte = (suggested_gear << 4) | current_gear
    packet[0x90:0x91] = struct.pack('B', gear_byte)

    # Throttle (0x91) - 80%
    packet[0x91:0x92] = struct.pack('B', int(80 * 2.55))

    # Brake (0x92) - 0%
    packet[0x92:0x93] = struct.pack('B', 0)

    # Road plane (0x94-0xA3)
    packet[0x94:0x98] = struct.pack('f', 0.0)    # plane_x
    packet[0x98:0x9C] = struct.pack('f', -1.0)   # plane_y (pointing down)
    packet[0x9C:0xA0] = struct.pack('f', 0.0)    # plane_z
    packet[0xA0:0xA4] = struct.pack('f', 0.065)  # distance

    # Tire RPS (0xA4-0xB3) - ~8 RPS at 50 m/s
    packet[0xA4:0xA8] = struct.pack('f', 8.0)    # FL
    packet[0xA8:0xAC] = struct.pack('f', 8.0)    # FR
    packet[0xAC:0xB0] = struct.pack('f', 8.2)    # RL (slight slip)
    packet[0xB0:0xB4] = struct.pack('f', 8.2)    # RR

    # Tire radius (0xB4-0xC3) - 0.33m radius
    packet[0xB4:0xB8] = struct.pack('f', 0.33)   # FL
    packet[0xB8:0xBC] = struct.pack('f', 0.33)   # FR
    packet[0xBC:0xC0] = struct.pack('f', 0.33)   # RL
    packet[0xC0:0xC4] = struct.pack('f', 0.33)   # RR

    # Suspension height (0xC4-0xD3) - 30mm = 0.030m
    packet[0xC4:0xC8] = struct.pack('f', 0.030)  # FL
    packet[0xC8:0xCC] = struct.pack('f', 0.030)  # FR
    packet[0xCC:0xD0] = struct.pack('f', 0.032)  # RL
    packet[0xD0:0xD4] = struct.pack('f', 0.032)  # RR

    # Clutch (0xF4-0xFF)
    packet[0xF4:0xF8] = struct.pack('f', 0.0)    # pedal
    packet[0xF8:0xFC] = struct.pack('f', 1.0)    # engagement
    packet[0xFC:0x100] = struct.pack('f', 6000.0) # rpm_gearbox

    # Transmission top speed (0x100)
    packet[0x100:0x104] = struct.pack('f', 320.0)

    # Gear ratios (0x104-0x123)
    gear_ratios = [3.5, 2.5, 1.8, 1.4, 1.1, 0.9, 0.0, 0.0]
    for i, ratio in enumerate(gear_ratios):
        packet[0x104 + i*4:0x108 + i*4] = struct.pack('f', ratio)

    # Car code (0x124) - LaFerrari by default
    packet[0x124:0x128] = struct.pack('i', car_code)

    return bytes(packet)


def encrypt_packet(packet):
    """Encrypt packet using GT7's Salsa20 encryption"""
    # Salsa20 requires exactly 32 bytes - truncate the GT7 key
    KEY = b'Simulator Interface Packet GT7 ver 0.0'[:32]

    # Use packet ID as IV seed (at 0x40 in unencrypted packet)
    # For simplicity, use a fixed IV
    oiv = struct.pack('I', 12345)  # Arbitrary IV seed
    iv1 = int.from_bytes(oiv, byteorder='little')
    iv2 = iv1 ^ 0xDEADBEAF  # GT7's magic number

    IV = bytearray()
    IV.extend(iv2.to_bytes(4, 'little'))
    IV.extend(iv1.to_bytes(4, 'little'))  # Match gt7_1r decryption: [iv2, iv1]

    # Encrypt
    cipher = Salsa20.new(key=KEY, nonce=IV)
    encrypted = cipher.encrypt(packet)

    # Insert IV at position 0x40 (unencrypted)
    encrypted_with_iv = bytearray(encrypted)
    encrypted_with_iv[0x40:0x44] = oiv

    return bytes(encrypted_with_iv)


def send_mock_packets(target_ip='127.0.0.1', target_port=33740, num_packets=15):
    """Send mock UDP packets to gt7_1r.py"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"Sending {num_packets} mock GT7 packets to {target_ip}:{target_port}")
    print(f"This will trigger {num_packets // 10} buffer flushes (buffer=10 packets)")
    print()

    for i in range(num_packets):
        # Create packet (increment packet_id, lap changes every 5 packets)
        packet_id = i + 1
        lap = (i // 5) + 1  # Lap 1 for packets 0-4, lap 2 for 5-9, etc.

        packet = create_mock_gt7_packet(packet_id=packet_id, lap=lap, car_code=3462)
        encrypted = encrypt_packet(packet)

        # Send packet
        sock.sendto(encrypted, (target_ip, target_port))
        print(f"Sent packet {packet_id:3d} (lap {lap}) - {len(encrypted)} bytes")

        # Small delay between packets (simulate 60 Hz = ~16ms)
        time.sleep(0.02)

    print()
    print(f"✅ Sent {num_packets} packets")
    print(f"Expected buffer flushes: {num_packets // 10}")
    print()
    print("Check sessions/ directory for domain JSON files!")

    sock.close()


if __name__ == '__main__':
    import sys

    print("=" * 60)
    print("Mock GT7 UDP Packet Sender - Phase 1 Testing")
    print("=" * 60)
    print()

    # Check if gt7_1r.py is likely running
    print("⚠️  Make sure gt7_1r_phase1.py is running first!")
    print("   Run in another terminal:")
    print("   cd dev/phase1")
    print("   python3 gt7_1r_phase1.py 127.0.0.1")
    print()

    response = input("Is gt7_1r_phase1.py running? (y/n): ")
    if response.lower() != 'y':
        print("Start gt7_1r_phase1.py first, then run this test again.")
        sys.exit(0)

    print()
    send_mock_packets(num_packets=15)
