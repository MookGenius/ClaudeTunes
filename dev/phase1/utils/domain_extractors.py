#!/usr/bin/env python3
"""
Domain Extractors for GT7 Telemetry Data
Phase 1: Domain JSON Architecture

Extracts UDP packet data into 6 domain-specific structures:
1. MetadataExtractor - Session info, car, track, lap times
2. SuspensionExtractor - Travel, bottoming, ride height
3. TireExtractor - Temps, slip, wear
4. AeroExtractor - Ride height, downforce, rake
5. DrivetrainExtractor - Power delivery, wheel spin, gearing
6. BalanceExtractor - Weight transfer, stability, g-forces
"""

import struct
from datetime import datetime as dt
from collections import deque
from typing import Dict, List, Any, Optional


class StatBuffer:
    """Maintains rolling statistics with last N samples"""

    def __init__(self, max_samples: int = 10):
        self.samples = deque(maxlen=max_samples)
        self.max_samples = max_samples

    def add(self, value: float):
        """Add a new sample"""
        self.samples.append(value)

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        if not self.samples:
            return {
                'current': 0.0,
                'avg': 0.0,
                'max': 0.0,
                'min': 0.0,
                'samples': []
            }

        return {
            'current': self.samples[-1],
            'avg': sum(self.samples) / len(self.samples),
            'max': max(self.samples),
            'min': min(self.samples),
            'samples': list(self.samples)
        }


class MetadataExtractor:
    """Extract session metadata, car info, lap times"""

    def __init__(self, car_database: Dict[int, str]):
        self.car_database = car_database
        self.session_start = dt.now()

    def extract(self, ddata: bytes, timestamp: dt) -> Dict[str, Any]:
        """Extract metadata from UDP packet"""

        # Packet info
        pktid = struct.unpack('i', ddata[0x70:0x74])[0]
        curlap = struct.unpack('h', ddata[0x74:0x76])[0]
        total_laps = struct.unpack('h', ddata[0x76:0x78])[0]

        # Lap times
        best_lap_ms = struct.unpack('i', ddata[0x78:0x7C])[0]
        last_lap_ms = struct.unpack('i', ddata[0x7C:0x80])[0]
        time_on_track_ms = struct.unpack('i', ddata[0x80:0x84])[0]

        # Car info
        car_code = struct.unpack('i', ddata[0x124:0x128])[0]
        car_name = self.car_database.get(car_code, f"Unknown Car ({car_code})")

        # Speed
        speed_mps = struct.unpack('f', ddata[0x4C:0x50])[0]
        speed_kph = 3.6 * speed_mps

        # Fuel
        fuel_level = struct.unpack('f', ddata[0x44:0x48])[0]
        fuel_capacity = struct.unpack('f', ddata[0x48:0x4C])[0]
        is_electric = fuel_capacity <= 0

        # Race info
        pre_race_start_pos = struct.unpack('h', ddata[0x84:0x86])[0]
        pre_race_num_cars = struct.unpack('h', ddata[0x86:0x88])[0]

        return {
            'session_id': self.session_start.strftime('%Y%m%d_%H%M%S'),
            'timestamp': timestamp.isoformat(),
            'packet_id': pktid,
            'car': {
                'code': car_code,
                'name': car_name,
                'classification': self._classify_car(car_code)
            },
            'track': {
                'name': 'Unknown',  # Not in UDP, user provides
                'type': 'balanced'  # Not in UDP, user provides
            },
            'session_summary': {
                'start_time': self.session_start.isoformat(),
                'current_lap': curlap,
                'total_laps': total_laps,
                'best_lap_ms': best_lap_ms,
                'last_lap_ms': last_lap_ms,
                'time_on_track_ms': time_on_track_ms,
                'speed_kph': speed_kph,
                'fuel_level': fuel_level,
                'fuel_capacity': fuel_capacity,
                'is_electric': is_electric
            },
            'race_info': {
                'start_position': pre_race_start_pos,
                'num_cars': pre_race_num_cars
            }
        }

    def _classify_car(self, car_code: int) -> str:
        """Classify car type (simple heuristic for now)"""
        # TODO: Use actual classification logic
        # For now, return generic classification
        return 'unknown'


class SuspensionExtractor:
    """Extract suspension travel, bottoming, ride height"""

    def __init__(self):
        self.fl_buffer = StatBuffer(10)
        self.fr_buffer = StatBuffer(10)
        self.rl_buffer = StatBuffer(10)
        self.rr_buffer = StatBuffer(10)
        self.bottoming_counters = {'FL': 0, 'FR': 0, 'RL': 0, 'RR': 0}
        self.BOTTOMING_THRESHOLD = 5.0  # mm - threshold for bottoming detection

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Extract suspension data from UDP packet"""

        # Suspension travel (in meters, convert to mm)
        susp_fl = struct.unpack('f', ddata[0xC4:0xC8])[0] * 1000  # m to mm
        susp_fr = struct.unpack('f', ddata[0xC8:0xCC])[0] * 1000
        susp_rl = struct.unpack('f', ddata[0xCC:0xD0])[0] * 1000
        susp_rr = struct.unpack('f', ddata[0xD0:0xD4])[0] * 1000

        # Add to buffers
        self.fl_buffer.add(susp_fl)
        self.fr_buffer.add(susp_fr)
        self.rl_buffer.add(susp_rl)
        self.rr_buffer.add(susp_rr)

        # Detect bottoming events (very low travel)
        if susp_fl < self.BOTTOMING_THRESHOLD:
            self.bottoming_counters['FL'] += 1
        if susp_fr < self.BOTTOMING_THRESHOLD:
            self.bottoming_counters['FR'] += 1
        if susp_rl < self.BOTTOMING_THRESHOLD:
            self.bottoming_counters['RL'] += 1
        if susp_rr < self.BOTTOMING_THRESHOLD:
            self.bottoming_counters['RR'] += 1

        # Body height / ride height
        body_height = struct.unpack('f', ddata[0x38:0x3C])[0] * 1000  # m to mm

        # Road plane data
        road_plane_x = struct.unpack('f', ddata[0x94:0x98])[0]
        road_plane_y = struct.unpack('f', ddata[0x98:0x9C])[0]
        road_plane_z = struct.unpack('f', ddata[0x9C:0xA0])[0]
        road_plane_dist = struct.unpack('f', ddata[0xA0:0xA4])[0]

        return {
            'travel_mm': {
                'FL': self.fl_buffer.get_stats(),
                'FR': self.fr_buffer.get_stats(),
                'RL': self.rl_buffer.get_stats(),
                'RR': self.rr_buffer.get_stats()
            },
            'bottoming_events': {
                'detected': any(v > 0 for v in self.bottoming_counters.values()),
                'FL_count': self.bottoming_counters['FL'],
                'FR_count': self.bottoming_counters['FR'],
                'RL_count': self.bottoming_counters['RL'],
                'RR_count': self.bottoming_counters['RR']
            },
            'current_ride_height_mm': {
                'front': body_height,
                'rear': body_height  # GT7 gives one value, same for front/rear
            },
            'road_surface': {
                'plane_x': road_plane_x,
                'plane_y': road_plane_y,
                'plane_z': road_plane_z,
                'distance': road_plane_dist
            }
        }


class TireExtractor:
    """Extract tire temps, slip ratios, rotation speeds"""

    def __init__(self):
        # Temperature buffers
        self.temp_fl = StatBuffer(10)
        self.temp_fr = StatBuffer(10)
        self.temp_rl = StatBuffer(10)
        self.temp_rr = StatBuffer(10)

        # Slip ratio buffers
        self.slip_fl = StatBuffer(10)
        self.slip_fr = StatBuffer(10)
        self.slip_rl = StatBuffer(10)
        self.slip_rr = StatBuffer(10)

        # Slip event counters
        self.slip_events = {'FL': 0, 'FR': 0, 'RL': 0, 'RR': 0}
        self.SLIP_THRESHOLD = 1.15  # 15% slip

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Extract tire data from UDP packet"""

        # Tire temperatures (Celsius)
        temp_fl = struct.unpack('f', ddata[0x60:0x64])[0]
        temp_fr = struct.unpack('f', ddata[0x64:0x68])[0]
        temp_rl = struct.unpack('f', ddata[0x68:0x6C])[0]
        temp_rr = struct.unpack('f', ddata[0x6C:0x70])[0]

        self.temp_fl.add(temp_fl)
        self.temp_fr.add(temp_fr)
        self.temp_rl.add(temp_rl)
        self.temp_rr.add(temp_rr)

        # Tire rotation speeds (RPS - revolutions per second)
        tire_rps_fl = struct.unpack('f', ddata[0xA4:0xA8])[0]
        tire_rps_fr = struct.unpack('f', ddata[0xA8:0xAC])[0]
        tire_rps_rl = struct.unpack('f', ddata[0xAC:0xB0])[0]
        tire_rps_rr = struct.unpack('f', ddata[0xB0:0xB4])[0]

        # Tire radius (meters)
        tire_radius_fl = struct.unpack('f', ddata[0xB4:0xB8])[0]
        tire_radius_fr = struct.unpack('f', ddata[0xB8:0xBC])[0]
        tire_radius_rl = struct.unpack('f', ddata[0xBC:0xC0])[0]
        tire_radius_rr = struct.unpack('f', ddata[0xC0:0xC4])[0]

        # Car speed
        speed_mps = struct.unpack('f', ddata[0x4C:0x50])[0]
        speed_kph = 3.6 * speed_mps

        # Calculate tire speeds (kph)
        tire_speed_fl = abs(3.6 * tire_radius_fl * tire_rps_fl)
        tire_speed_fr = abs(3.6 * tire_radius_fr * tire_rps_fr)
        tire_speed_rl = abs(3.6 * tire_radius_rl * tire_rps_rl)
        tire_speed_rr = abs(3.6 * tire_radius_rr * tire_rps_rr)

        # Calculate slip ratios
        if speed_kph > 1.0:  # Only calc when moving
            slip_fl = tire_speed_fl / speed_kph
            slip_fr = tire_speed_fr / speed_kph
            slip_rl = tire_speed_rl / speed_kph
            slip_rr = tire_speed_rr / speed_kph
        else:
            slip_fl = slip_fr = slip_rl = slip_rr = 0.0

        self.slip_fl.add(slip_fl)
        self.slip_fr.add(slip_fr)
        self.slip_rl.add(slip_rl)
        self.slip_rr.add(slip_rr)

        # Detect slip events
        if slip_fl > self.SLIP_THRESHOLD:
            self.slip_events['FL'] += 1
        if slip_fr > self.SLIP_THRESHOLD:
            self.slip_events['FR'] += 1
        if slip_rl > self.SLIP_THRESHOLD:
            self.slip_events['RL'] += 1
        if slip_rr > self.SLIP_THRESHOLD:
            self.slip_events['RR'] += 1

        return {
            'temps_celsius': {
                'FL': self.temp_fl.get_stats(),
                'FR': self.temp_fr.get_stats(),
                'RL': self.temp_rl.get_stats(),
                'RR': self.temp_rr.get_stats()
            },
            'slip_ratio': {
                'FL': {**self.slip_fl.get_stats(), 'events': self.slip_events['FL']},
                'FR': {**self.slip_fr.get_stats(), 'events': self.slip_events['FR']},
                'RL': {**self.slip_rl.get_stats(), 'events': self.slip_events['RL']},
                'RR': {**self.slip_rr.get_stats(), 'events': self.slip_events['RR']}
            },
            'rotation_speed_rps': {
                'FL': tire_rps_fl,
                'FR': tire_rps_fr,
                'RL': tire_rps_rl,
                'RR': tire_rps_rr
            },
            'wear_pct': {
                # Not in UDP - estimate from radius change or leave as 0
                'FL': 0.0,
                'FR': 0.0,
                'RL': 0.0,
                'RR': 0.0
            }
        }


class AeroExtractor:
    """Extract ride height, downforce estimates, rake"""

    def __init__(self, downforce_database: Dict[int, int]):
        self.downforce_db = downforce_database
        self.front_height_buffer = StatBuffer(10)
        self.rear_height_buffer = StatBuffer(10)
        self.high_speed_samples = []
        self.HIGH_SPEED_THRESHOLD = 150  # kph

    def extract(self, ddata: bytes, car_code: int) -> Dict[str, Any]:
        """Extract aero data from UDP packet"""

        # Body height (ride height)
        body_height = struct.unpack('f', ddata[0x38:0x3C])[0] * 1000  # m to mm

        # Suspension heights (for front/rear differentiation)
        susp_fl = struct.unpack('f', ddata[0xC4:0xC8])[0] * 1000
        susp_fr = struct.unpack('f', ddata[0xC8:0xCC])[0] * 1000
        susp_rl = struct.unpack('f', ddata[0xCC:0xD0])[0] * 1000
        susp_rr = struct.unpack('f', ddata[0xD0:0xD4])[0] * 1000

        front_height = (susp_fl + susp_fr) / 2
        rear_height = (susp_rl + susp_rr) / 2

        self.front_height_buffer.add(front_height)
        self.rear_height_buffer.add(rear_height)

        # Speed (for high-speed tracking)
        speed_mps = struct.unpack('f', ddata[0x4C:0x50])[0]
        speed_kph = 3.6 * speed_mps

        if speed_kph > self.HIGH_SPEED_THRESHOLD:
            self.high_speed_samples.append(speed_kph)
            # Keep only last 10 high-speed samples
            if len(self.high_speed_samples) > 10:
                self.high_speed_samples.pop(0)

        # Downforce estimate from database
        downforce_estimate = self.downforce_db.get(car_code, 0)

        front_stats = self.front_height_buffer.get_stats()
        rear_stats = self.rear_height_buffer.get_stats()

        return {
            'ride_height_mm': {
                'avg_front': front_stats['avg'],
                'avg_rear': rear_stats['avg'],
                'min_front': front_stats['min'],
                'min_rear': rear_stats['min'],
                'rake_mm': rear_stats['avg'] - front_stats['avg'],
                'samples_front': front_stats['samples'],
                'samples_rear': rear_stats['samples']
            },
            'downforce_estimate_lbs': {
                'total': downforce_estimate,
                'source': 'car_database_lookup'
            },
            'speed_correlation': {
                'high_speed_zones_mph': [kph * 0.621371 for kph in self.high_speed_samples],
                'avg_high_speed_mph': (sum(self.high_speed_samples) / len(self.high_speed_samples) * 0.621371) if self.high_speed_samples else 0
            }
        }


class DrivetrainExtractor:
    """Extract power delivery, wheel spin, gearing"""

    def __init__(self):
        self.rpm_buffer = StatBuffer(10)
        self.throttle_buffer = StatBuffer(10)
        self.wheel_spin_events = {'FL': 0, 'FR': 0, 'RL': 0, 'RR': 0}
        self.gear_time = {str(i): 0 for i in range(9)}  # Gears 0-8
        self.total_samples = 0
        self.SPIN_THRESHOLD = 1.15  # 15% slip while on throttle

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Extract drivetrain data from UDP packet"""

        # Engine RPM
        rpm = struct.unpack('f', ddata[0x3C:0x40])[0]
        self.rpm_buffer.add(rpm)

        # Throttle & Brake
        throttle = struct.unpack('B', ddata[0x91:0x92])[0] / 2.55  # 0-100%
        brake = struct.unpack('B', ddata[0x92:0x93])[0] / 2.55
        self.throttle_buffer.add(throttle)

        # Gear data
        gear_raw = struct.unpack('B', ddata[0x90:0x91])[0]
        current_gear = gear_raw & 0b00001111
        suggested_gear = gear_raw >> 4

        # Track gear usage
        self.gear_time[str(current_gear)] += 1
        self.total_samples += 1

        # Gear ratios
        gear_ratios = [
            struct.unpack('f', ddata[0x104 + i*4:0x108 + i*4])[0]
            for i in range(8)
        ]

        # Transmission top speed
        trans_top_speed = struct.unpack('f', ddata[0x100:0x104])[0]

        # Engine limits
        rev_warning = struct.unpack('H', ddata[0x88:0x8A])[0]
        rev_limiter = struct.unpack('H', ddata[0x8A:0x8C])[0]

        # Engine temps
        water_temp = struct.unpack('f', ddata[0x58:0x5C])[0]
        oil_temp = struct.unpack('f', ddata[0x5C:0x60])[0]
        oil_pressure = struct.unpack('f', ddata[0x54:0x58])[0]

        # Wheel spin detection (if slip > threshold while throttle > 50%)
        # (We'd need tire slip data here - this is simplified)
        total_spin_count = sum(self.wheel_spin_events.values())

        # Calculate gear usage percentages
        gear_usage = {}
        if self.total_samples > 0:
            for gear, count in self.gear_time.items():
                gear_usage[gear] = round(100 * count / self.total_samples, 1)

        rpm_stats = self.rpm_buffer.get_stats()
        throttle_stats = self.throttle_buffer.get_stats()

        return {
            'power_delivery': {
                'rpm': rpm_stats['current'],
                'avg_rpm': rpm_stats['avg'],
                'max_rpm': rev_limiter,
                'throttle_pct': throttle_stats['current'],
                'avg_throttle_pct': throttle_stats['avg'],
                'samples_rpm': rpm_stats['samples'],
                'samples_throttle': throttle_stats['samples']
            },
            'wheel_spin_events': {
                'total_count': total_spin_count,
                'FL_count': self.wheel_spin_events['FL'],
                'FR_count': self.wheel_spin_events['FR'],
                'RL_count': self.wheel_spin_events['RL'],
                'RR_count': self.wheel_spin_events['RR'],
                'severity_avg': 0.0  # Calculate from slip ratios
            },
            'gear_usage': gear_usage,
            'gearing': {
                'current_gear': current_gear,
                'suggested_gear': suggested_gear,
                'ratios': gear_ratios,
                'transmission_top_speed': trans_top_speed
            },
            'engine_temps': {
                'water_temp_c': water_temp,
                'oil_temp_c': oil_temp,
                'oil_pressure_bar': oil_pressure
            }
        }


class BalanceExtractor:
    """Extract weight transfer, stability, g-forces"""

    def __init__(self):
        self.lateral_g_buffer = StatBuffer(10)
        self.longitudinal_g_buffer = StatBuffer(10)
        self.prev_vel_x = 0.0
        self.prev_vel_z = 0.0
        self.prev_time = dt.now()
        self.understeer_events = 0
        self.oversteer_events = 0

    def extract(self, ddata: bytes) -> Dict[str, Any]:
        """Extract balance data from UDP packet"""

        # Velocity vectors
        vel_x = struct.unpack('f', ddata[0x10:0x14])[0]
        vel_y = struct.unpack('f', ddata[0x14:0x18])[0]
        vel_z = struct.unpack('f', ddata[0x18:0x1C])[0]

        # Rotation
        rot_pitch = struct.unpack('f', ddata[0x1C:0x20])[0]
        rot_yaw = struct.unpack('f', ddata[0x20:0x24])[0]
        rot_roll = struct.unpack('f', ddata[0x24:0x28])[0]

        # Angular velocity
        ang_vel_x = struct.unpack('f', ddata[0x2C:0x30])[0]
        ang_vel_y = struct.unpack('f', ddata[0x30:0x34])[0]
        ang_vel_z = struct.unpack('f', ddata[0x34:0x38])[0]

        # Calculate g-forces (simplified)
        # Lateral G: from angular velocity Z (yaw rate)
        lateral_g = abs(ang_vel_z) / 9.81  # Rough approximation

        # Longitudinal G: from velocity Z change (accel/brake)
        now = dt.now()
        dt_seconds = (now - self.prev_time).total_seconds()
        if dt_seconds > 0:
            accel_z = (vel_z - self.prev_vel_z) / dt_seconds
            longitudinal_g = accel_z / 9.81
        else:
            longitudinal_g = 0.0

        self.lateral_g_buffer.add(lateral_g)
        self.longitudinal_g_buffer.add(longitudinal_g)

        self.prev_vel_x = vel_x
        self.prev_vel_z = vel_z
        self.prev_time = now

        lateral_stats = self.lateral_g_buffer.get_stats()
        long_stats = self.longitudinal_g_buffer.get_stats()

        # Analyze balance bias (simplified)
        balance_bias = 'neutral'
        # TODO: Implement proper understeer/oversteer detection

        return {
            'weight_transfer': {
                'lateral_g': lateral_stats,
                'longitudinal_g': long_stats
            },
            'rotation': {
                'pitch': rot_pitch,
                'yaw': rot_yaw,
                'roll': rot_roll
            },
            'angular_velocity': {
                'x': ang_vel_x,
                'y': ang_vel_y,
                'z': ang_vel_z
            },
            'stability_metrics': {
                'understeer_events': self.understeer_events,
                'oversteer_events': self.oversteer_events,
                'balance_bias': balance_bias
            },
            'corner_analysis': {
                'entry_stability': 'unknown',
                'mid_corner_grip': 'unknown',
                'exit_traction': 'unknown'
            }
        }
