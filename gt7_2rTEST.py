#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GT7 Analyzer v3.1 (TEST) - Phase 2 Enhancements
- Includes all v3 fixes (Auto-classification, validation, cleaning)
- ADDS: Platform Dynamics (Heave)
- ADDS: Damper Velocity Histograms (Time-domain analysis)
"""
import csv
import os
import sys
import json
from datetime import datetime
import math

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Install it with: pip3 install numpy")
    sys.exit(1)

# ==================== CAR CLASSIFICATION ====================

CAR_THRESHOLDS = {
    'kart': {
        'braking_threshold': 15,
        'cornering_speed_min': 10,
        'acceleration_threshold': 40,
        'high_speed_threshold': 50,
        'slip_traction_loss': 1.20,
        'description': 'Kart - Light, responsive, low speeds'
    },
    'formula': {
        'braking_threshold': 25,
        'cornering_speed_min': 60,
        'acceleration_threshold': 60,
        'high_speed_threshold': 200,
        'slip_traction_loss': 1.08,
        'description': 'Formula - Extreme performance, high downforce'
    },
    'race_car': {
        'braking_threshold': 20,
        'cornering_speed_min': 40,
        'acceleration_threshold': 50,
        'high_speed_threshold': 120,
        'slip_traction_loss': 1.12,
        'description': 'Race Car - GT3, GT4, GT500'
    },
    'rally': {
        'braking_threshold': 18,
        'cornering_speed_min': 20,
        'acceleration_threshold': 45,
        'high_speed_threshold': 100,
        'slip_traction_loss': 1.25,
        'description': 'Rally - Off-road, loose surfaces'
    },
    'prototype': {
        'braking_threshold': 25,
        'cornering_speed_min': 80,
        'acceleration_threshold': 55,
        'high_speed_threshold': 180,
        'slip_traction_loss': 1.10,
        'description': 'Prototype - LMP1, Group C endurance racers'
    },
    'drift': {
        'braking_threshold': 20,
        'cornering_speed_min': 30,
        'acceleration_threshold': 50,
        'high_speed_threshold': 100,
        'slip_traction_loss': 1.35,
        'description': 'Drift - Slip is intentional'
    },
    'street': {
        'braking_threshold': 15,
        'cornering_speed_min': 25,
        'acceleration_threshold': 40,
        'high_speed_threshold': 80,
        'slip_traction_loss': 1.15,
        'description': 'Street Car - Production vehicles'
    },
}

def classify_car(car_name):
    """Auto-classify car type from name using keyword matching"""
    if not car_name:
        return 'street'
    
    name_lower = car_name.lower()
    
    # Check in priority order
    if 'kart' in name_lower or 'racing kart' in name_lower:
        return 'kart'
    if any(kw in name_lower for kw in ['formula', 'f1', 'mp4/', 'sf19', 'sf23']):
        return 'formula'
    if any(kw in name_lower for kw in ['rally', 'gr.b', 'gr b']):
        return 'rally'
    if any(kw in name_lower for kw in ['drift']):
        return 'drift'
    if any(kw in name_lower for kw in ['919', 'ts030', 'ts050', 'r18', 'gr010', 'group c', 'prototype']):
        return 'prototype'
    if any(kw in name_lower for kw in ['race car', 'gt3', 'gt4', 'gt500', 'gr.3', 'gr.4', 'gr3', 'gr4', 
                                         'gtr', 'racing', 'lm ', 'touring car']):
        return 'race_car'
    
    return 'street'

# ==================== DATA VALIDATION ====================

# Physical limits for data validation
VALIDATION_RANGES = {
    'speed_kph': (0, 500),
    'rpm': (0, 20000),
    'tire_temp_fl': (0, 150), 'tire_temp_fr': (0, 150),
    'tire_temp_rl': (0, 150), 'tire_temp_rr': (0, 150),
    'tire_slip_ratio_fl': (0, 5), 'tire_slip_ratio_fr': (0, 5),
    'tire_slip_ratio_rl': (0, 5), 'tire_slip_ratio_rr': (0, 5),
    'suspension_fl': (0, 2), 'suspension_fr': (0, 2),
    'suspension_rl': (0, 2), 'suspension_rr': (0, 2),
    'throttle_percent': (0, 100),
    'brake_percent': (0, 100),
    'body_height': (-100, 1000),  # Allow negative for lowered cars, up to 1m
    'current_gear': (0, 15),
}

def is_valid_value(value):
    """Check if value is not NaN or Inf"""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return not (math.isnan(value) or math.isinf(value))
    return True

def validate_data_row(row, stats):
    """Validate a single data row, return None if invalid"""
    
    # Filter game states - CRITICAL for data quality
    if to_float(row.get('flag_car_on_track'), 1) == 0:
        stats['filtered_off_track'] += 1
        return None
    if to_float(row.get('flag_loading'), 0) == 1:
        stats['filtered_loading'] += 1
        return None
    if to_float(row.get('flag_paused'), 0) == 1:
        stats['filtered_paused'] += 1
        return None
    
    # Range validation
    for field, (min_val, max_val) in VALIDATION_RANGES.items():
        if field in row:
            val = to_float(row.get(field), 0)
            if not is_valid_value(val) or val < min_val or val > max_val:
                stats['filtered_invalid_range'] += 1
                return None
    
    # Check for NaN/Inf in any numeric field
    for key, value in row.items():
        if isinstance(value, float):
            if not is_valid_value(value):
                stats['filtered_nan_inf'] += 1
                return None
    
    stats['valid_rows'] += 1
    return row

# ==================== UTILITIES ====================

def to_float(v, default=0.0):
    """Safely convert to float with default"""
    try:
        if v is None:
            return default
        if isinstance(v, (int, float)):
            val = float(v)
            if math.isnan(val) or math.isinf(val):
                return default
            return val
        v = str(v).strip()
        if v == "" or v.lower() == "nan":
            return default
        return float(v)
    except Exception:
        return default

def col(data, key, default=0.0):
    """Return list of floats for a column name, defaulting when missing"""
    return [to_float(row.get(key), default) for row in data]

def safe_mean(arr, default=0.0):
    """Calculate mean, filtering invalid values"""
    arr = [a for a in arr if a is not None and is_valid_value(a)]
    if not arr or len(arr) == 0:
        return default
    return float(np.mean(arr))

def safe_max(arr, default=0.0):
    """Calculate max, filtering invalid values"""
    arr = [a for a in arr if a is not None and is_valid_value(a)]
    if not arr:
        return default
    return float(np.max(arr))

def safe_min(arr, default=0.0):
    """Calculate min, filtering invalid values"""
    arr = [a for a in arr if a is not None and is_valid_value(a)]
    if not arr:
        return default
    return float(np.min(arr))

def safe_std(arr, default=0.0):
    """Calculate std deviation, filtering invalid values"""
    arr = [a for a in arr if a is not None and is_valid_value(a)]
    if not arr or len(arr) < 2:
        return 0.0
    return float(np.std(arr))

def safe_divide(numerator, denominator, default=0.0):
    """Safely divide with zero protection"""
    if denominator == 0 or not is_valid_value(denominator):
        return default
    if not is_valid_value(numerator):
        return default
    return numerator / denominator

# ==================== DERIVED CHANNELS ====================

def calculate_derived_metrics(data):
    """
    Calculate velocity and heave metrics (Phase 2)
    Adds:
    - susp_vel_fl/fr/rl/rr (mm/s)
    - heave (mm)
    Returns: (data, clamp_statistics)
    """
    if not data or len(data) < 2:
        return data, {'clamped_count': 0, 'total_samples': 0}

    # Track clamped values for data quality
    clamped_count = 0
    total_samples = 0

    # Initialize derived fields for the first row (velocities are 0)
    for corner in ['fl', 'fr', 'rl', 'rr']:
        data[0][f'susp_vel_{corner}'] = 0.0
    data[0]['heave'] = (data[0]['suspension_fl'] + data[0]['suspension_fr'] +
                        data[0]['suspension_rl'] + data[0]['suspension_rr']) / 4.0 * 1000.0

    for i in range(1, len(data)):
        curr = data[i]
        prev = data[i-1]

        # Time delta in seconds
        # Try using current_lap_time difference
        t_curr = to_float(curr.get('current_lap_time'), 0)
        t_prev = to_float(prev.get('current_lap_time'), 0)

        dt = t_curr - t_prev

        # Fallback if lap time resets or is weird (e.g. new lap boundary crossing, though file is per lap)
        # If dt is too small or negative, assume 60Hz (0.0166s)
        if dt <= 0.001 or dt > 0.2:
            dt = 1.0 / 60.0

        # Calculate suspension velocity for each corner
        # Input suspension is in METERS. Output we want MM/S.
        for corner in ['fl', 'fr', 'rl', 'rr']:
            pos_curr = to_float(curr.get(f'suspension_{corner}'), 0)
            pos_prev = to_float(prev.get(f'suspension_{corner}'), 0)

            # velocity = d_pos / dt
            # (m - m) / s = m/s -> * 1000 -> mm/s
            vel_mm_s = ((pos_curr - pos_prev) / dt) * 1000.0

            total_samples += 1

            # Clamp extreme values (telemetry glitches)
            if vel_mm_s > 2000 or vel_mm_s < -2000:
                clamped_count += 1
                vel_mm_s = max(-2000, min(2000, vel_mm_s))

            curr[f'susp_vel_{corner}'] = vel_mm_s

        # Calculate Heave (average of 4 corners) in mm
        # Input suspension is Meters
        heave_m = (to_float(curr.get('suspension_fl'), 0) +
                   to_float(curr.get('suspension_fr'), 0) +
                   to_float(curr.get('suspension_rl'), 0) +
                   to_float(curr.get('suspension_rr'), 0)) / 4.0
        curr['heave'] = heave_m * 1000.0

    clamp_stats = {
        'clamped_count': clamped_count,
        'total_samples': total_samples,
        'clamp_percentage': round(safe_divide(clamped_count, total_samples, 0) * 100, 2)
    }

    return data, clamp_stats

def calculate_damper_histogram(velocities, bin_size=25):
    """
    Generate histogram data for damper velocities
    Bins: < -200, -200..-175, ..., 0, ..., 175..200, > 200
    Research standard is 50mm/s but 25mm/s gives better resolution for GT7
    """
    # Define bins from -300 to +300
    bins = {}
    # Initialize bins
    r_range = range(-300, 325, bin_size)
    for b in r_range:
        bins[b] = 0

    total_counts = 0
    for v in velocities:
        if v is None: continue
        total_counts += 1
        # Round to nearest bin floor
        # e.g. 48 -> 25, -48 -> -50
        b = math.floor(v / bin_size) * bin_size

        # Clamp to range
        if b < -300: b = -300
        if b > 300: b = 300

        if b in bins:
            bins[b] += 1
        else:
            # Fallback for edge cases
            bins[b] = 1

    # Convert to percentages
    histogram = {}
    if total_counts > 0:
        for b, count in bins.items():
            histogram[b] = round((count / total_counts) * 100.0, 2)

    return histogram

def interpret_damper_histogram(histogram):
    """
    Interpret damper histogram shape for diagnostics

    Returns diagnostic metrics and warnings based on histogram distribution.
    Ideal histogram: 10-15% center peak, symmetric compression/rebound
    """
    center_bins = {-25: 0, 0: 0, 25: 0}  # Central 3 bins
    for b in center_bins.keys():
        center_bins[b] = histogram.get(b, 0)

    center_peak = sum(center_bins.values())

    comp_total = sum(v for k, v in histogram.items() if k < -100)
    reb_total = sum(v for k, v in histogram.items() if k > 100)

    # Ideal: 10-15% center peak, symmetric distribution
    diagnostics = {
        'center_peak_percent': round(center_peak, 2),
        'compression_percent': round(comp_total, 2),
        'rebound_percent': round(reb_total, 2),
        'symmetry_deviation': round(abs(comp_total - reb_total), 2),
        'warnings': []
    }

    # Add interpretation warnings
    if center_peak < 5:
        diagnostics['warnings'].append("Low center peak - dampers may be too soft")
    elif center_peak > 25:
        diagnostics['warnings'].append("High center peak - dampers may be too stiff")

    if diagnostics['symmetry_deviation'] > 10:
        diagnostics['warnings'].append("Asymmetric distribution - check comp/reb balance")

    # Overall assessment
    if 10 <= center_peak <= 15 and diagnostics['symmetry_deviation'] < 5:
        diagnostics['assessment'] = "OPTIMAL - Dampers operating in ideal range"
    elif 5 <= center_peak <= 20 and diagnostics['symmetry_deviation'] < 10:
        diagnostics['assessment'] = "GOOD - Dampers working well"
    else:
        diagnostics['assessment'] = "NEEDS ATTENTION - Review damper settings"

    return diagnostics

# ==================== CORE ANALYSIS ====================

def process_session_folder(session_folder):
    """Process all lap CSV files in a session folder"""
    if not os.path.exists(session_folder):
        print(f"Session folder '{session_folder}' not found")
        return None

    lap_files = [f for f in os.listdir(session_folder) 
                 if f.lower().endswith('.csv') and 'lap_' in f.lower()]
    if not lap_files:
        print(f"No lap CSV files found in {session_folder}")
        return None

    lap_files.sort()
    print(f"Found {len(lap_files)} lap files to process...")

    # Detect car type from first lap
    first_lap_path = os.path.join(session_folder, lap_files[0])
    car_type, car_name = detect_car_type(first_lap_path)
    thresholds = CAR_THRESHOLDS[car_type]
    
    print(f"\n🏎️  Car Detected: {car_name}")
    print(f"📊 Classification: {car_type.upper()}")
    print(f"ℹ️  {thresholds['description']}")
    print(f"\n⚙️  Thresholds:")
    print(f"   Braking: >{thresholds['braking_threshold']}%")
    print(f"   Cornering: >{thresholds['cornering_speed_min']} kph")
    print(f"   Acceleration: >{thresholds['acceleration_threshold']}%")
    print(f"   High-speed: >{thresholds['high_speed_threshold']} kph")
    print(f"   Slip threshold: >{thresholds['slip_traction_loss']}")
    print()

    all_lap_metrics = []
    total_stats = {
        'total_rows': 0,
        'valid_rows': 0,
        'filtered_off_track': 0,
        'filtered_loading': 0,
        'filtered_paused': 0,
        'filtered_invalid_range': 0,
        'filtered_nan_inf': 0,
        'damper_velocity_clamps': 0,
        'damper_velocity_samples': 0,
    }

    for lap_file in lap_files:
        lap_path = os.path.join(session_folder, lap_file)
        print(f"Processing {lap_file}...")
        lap_metrics = process_single_lap(lap_path, thresholds, total_stats)
        if lap_metrics:
            all_lap_metrics.append(lap_metrics)

    if not all_lap_metrics:
        print("No valid lap data processed")
        return None

    session_summary = calculate_session_summary(all_lap_metrics, car_type, car_name, thresholds)
    
    # Add data quality report
    session_summary['data_quality'] = {
        'total_rows_read': total_stats['total_rows'],
        'valid_rows_analyzed': total_stats['valid_rows'],
        'filtered_off_track': total_stats['filtered_off_track'],
        'filtered_loading': total_stats['filtered_loading'],
        'filtered_paused': total_stats['filtered_paused'],
        'filtered_invalid_range': total_stats['filtered_invalid_range'],
        'filtered_nan_inf': total_stats['filtered_nan_inf'],
        'data_quality_percentage': round(safe_divide(total_stats['valid_rows'],
                                                      total_stats['total_rows'], 0) * 100, 2),
        'damper_velocity_clamps': total_stats['damper_velocity_clamps'],
        'damper_velocity_samples': total_stats['damper_velocity_samples'],
        'damper_clamp_percentage': round(safe_divide(total_stats['damper_velocity_clamps'],
                                                      total_stats['damper_velocity_samples'], 0) * 100, 2)
    }

    output_file = os.path.join(session_folder, 'telemetry_analysis_v3_TEST.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(session_summary, f, indent=2)

    print(f"\n✅ Session analysis saved to: {output_file}")
    print(f"\n📊 Data Quality: {session_summary['data_quality']['data_quality_percentage']}% of data was valid")
    print(f"   Valid rows: {total_stats['valid_rows']:,}")
    print(f"   Filtered (off track): {total_stats['filtered_off_track']:,}")
    print(f"   Filtered (loading): {total_stats['filtered_loading']:,}")
    print(f"   Filtered (paused): {total_stats['filtered_paused']:,}")
    print(f"   Filtered (invalid range): {total_stats['filtered_invalid_range']:,}")
    print(f"   Filtered (NaN/Inf): {total_stats['filtered_nan_inf']:,}")
    print(f"\n🔧 Damper Velocity Quality:")
    print(f"   Clamped values: {total_stats['damper_velocity_clamps']:,} / {total_stats['damper_velocity_samples']:,}")
    print(f"   Clamp rate: {session_summary['data_quality']['damper_clamp_percentage']}%")
    if session_summary['data_quality']['damper_clamp_percentage'] > 5:
        print(f"   ⚠️  Warning: High clamp rate may indicate telemetry glitches")
    
    return session_summary

def detect_car_type(lap_file):
    """Detect car type from first lap CSV"""
    try:
        with open(lap_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            first_row = next(reader)
            car_name = first_row.get('car_name', 'Unknown')
            car_type = classify_car(car_name)
            return car_type, car_name
    except Exception as e:
        print(f"Warning: Could not detect car type: {e}")
        return 'street', 'Unknown'

def process_single_lap(lap_file, thresholds, total_stats):
    """Process a single lap CSV file"""
    try:
        with open(lap_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        total_stats['total_rows'] += len(data)

        if len(data) < 10:
            print(f"  Skipping {lap_file} - insufficient data points")
            return None

        # Convert numeric fields and validate
        validated_data = []
        for row in data:
            # Convert all numeric fields
            for key in row.keys():
                if key not in ['timestamp', 'car_name']:
                    row[key] = to_float(row.get(key), 0.0)
            
            # Validate row
            clean_row = validate_data_row(row, total_stats)
            if clean_row:
                validated_data.append(clean_row)

        if len(validated_data) < 5:
            print(f"  Skipping {lap_file} - insufficient valid data after cleaning")
            return None

        # Phase 2: Calculate derived metrics (velocity, heave)
        enriched_data, clamp_stats = calculate_derived_metrics(validated_data)

        # Track damper velocity clamp statistics
        total_stats['damper_velocity_clamps'] += clamp_stats['clamped_count']
        total_stats['damper_velocity_samples'] += clamp_stats['total_samples']

        lap_metrics = analyze_lap_data(enriched_data, thresholds)
        
        # Extract lap number from filename
        base = os.path.basename(lap_file).lower()
        lap_number = 0
        if 'lap_' in base and base.endswith('.csv'):
            try:
                lap_number = int(base.replace('lap_', '').replace('.csv', ''))
            except Exception:
                lap_number = 0

        lap_metrics['lap_number'] = lap_number
        lap_metrics['data_points_analyzed'] = len(enriched_data)
        lap_metrics['data_points_total'] = len(data)
        
        return lap_metrics

    except Exception as e:
        print(f"  Error processing {lap_file}: {e}")
        return None

def analyze_lap_data(data, thresholds):
    """Complete lap analysis with validated telemetry data"""
    
    # Phase detection using adaptive thresholds
    braking_data = [row for row in data if to_float(row.get('brake_percent'),0) > thresholds['braking_threshold']]
    cornering_data = [row for row in data if to_float(row.get('speed_kph'),0) > thresholds['cornering_speed_min'] 
                      and abs(to_float(row.get('rotation_roll'),0)) > 0.01]
    acceleration_data = [row for row in data if to_float(row.get('throttle_percent'),0) > thresholds['acceleration_threshold']]
    high_speed_data = [row for row in data if to_float(row.get('speed_kph'),0) > thresholds['high_speed_threshold']]

    def m(key): return safe_mean(col(data, key))
    def mx(key): return safe_max(col(data, key))
    def mn(key): return safe_min(col(data, key))
    def st(key): return safe_std(col(data, key))

    metrics = {
        'lap_summary': {
            'total_data_points': len(data),
            'lap_time': mx('current_lap_time'),
            'max_speed': mx('speed_kph'),
            'avg_speed': m('speed_kph'),
            'max_rpm': mx('rpm'),
            'avg_rpm': m('rpm'),
        },
        'platform_dynamics': {
            'avg_pitch': m('rotation_pitch'),
            'max_pitch_range': mx('rotation_pitch') - mn('rotation_pitch'),
            'avg_roll': safe_mean([abs(x) for x in col(data, 'rotation_roll')]),
            'max_roll': safe_max([abs(x) for x in col(data, 'rotation_roll')]),
            'avg_heave_mm': m('heave'),
            'heave_range_mm': mx('heave') - mn('heave'),
            'pitch_stability': st('rotation_pitch'),
            'roll_stability': st('rotation_roll'),
        },
        'damper_analysis': {
            'histograms': {
                'fl': calculate_damper_histogram(col(data, 'susp_vel_fl')),
                'fr': calculate_damper_histogram(col(data, 'susp_vel_fr')),
                'rl': calculate_damper_histogram(col(data, 'susp_vel_rl')),
                'rr': calculate_damper_histogram(col(data, 'susp_vel_rr')),
            },
            'diagnostics': {
                'fl': interpret_damper_histogram(calculate_damper_histogram(col(data, 'susp_vel_fl'))),
                'fr': interpret_damper_histogram(calculate_damper_histogram(col(data, 'susp_vel_fr'))),
                'rl': interpret_damper_histogram(calculate_damper_histogram(col(data, 'susp_vel_rl'))),
                'rr': interpret_damper_histogram(calculate_damper_histogram(col(data, 'susp_vel_rr'))),
            },
            'max_velocity': {
                'fl_comp': mn('susp_vel_fl'), 'fl_reb': mx('susp_vel_fl'),
                'fr_comp': mn('susp_vel_fr'), 'fr_reb': mx('susp_vel_fr'),
                'rl_comp': mn('susp_vel_rl'), 'rl_reb': mx('susp_vel_rl'),
                'rr_comp': mn('susp_vel_rr'), 'rr_reb': mx('susp_vel_rr'),
            }
        },
        'suspension_behavior': {
            'avg_body_height': m('body_height'),
            'min_body_height': mn('body_height'),
            'body_height_variation': st('body_height'),
            'suspension_travel': {
                'fl_avg': m('suspension_fl'),
                'fr_avg': m('suspension_fr'),
                'rl_avg': m('suspension_rl'),
                'rr_avg': m('suspension_rr'),
                'fl_max': mx('suspension_fl'),
                'fr_max': mx('suspension_fr'),
                'rl_max': mx('suspension_rl'),
                'rr_max': mx('suspension_rl'),
            },
            'front_rear_balance': {
                'avg_front_compression': safe_mean([m('suspension_fl'), m('suspension_fr')]),
                'avg_rear_compression' : safe_mean([m('suspension_rl'), m('suspension_rr')]),
            },
        },
        'road_analysis': {
            'banking': {
                'avg_angle': safe_mean([y * 57.2958 for y in col(data, 'road_plane_y')]),
                'max_left_bank': safe_min([y * 57.2958 for y in col(data, 'road_plane_y')]),
                'max_right_bank': safe_max([y * 57.2958 for y in col(data, 'road_plane_y')]),
            },
            'elevation': {
                'avg_gradient': m('road_plane_z'),
                'max_uphill': mx('road_plane_z'),
                'max_downhill': mn('road_plane_z'),
            },
        },
        'tire_analysis': {
            'temperatures': {
                'fl_avg': m('tire_temp_fl'), 'fr_avg': m('tire_temp_fr'),
                'rl_avg': m('tire_temp_rl'), 'rr_avg': m('tire_temp_rr'),
                'fl_max': mx('tire_temp_fl'), 'fr_max': mx('tire_temp_fr'),
                'rl_max': mx('tire_temp_rl'), 'rr_max': mx('tire_temp_rr'),
                'fl_min': mn('tire_temp_fl'), 'fr_min': mn('tire_temp_fr'),
                'rl_min': mn('tire_temp_rl'), 'rr_min': mn('tire_temp_rl'),
                'temp_spread': (safe_max([mx('tire_temp_fl'), mx('tire_temp_fr'), mx('tire_temp_rl'), mx('tire_temp_rr')]) - 
                                safe_min([mn('tire_temp_fl'), mn('tire_temp_fr'), mn('tire_temp_rl'), mn('tire_temp_rr')]))
            },
            'slip_ratios': {
                'fl_avg': m('tire_slip_ratio_fl'), 'fr_avg': m('tire_slip_ratio_fr'),
                'rl_avg': m('tire_slip_ratio_rl'), 'rr_avg': m('tire_slip_ratio_rr'),
                'fl_max': mx('tire_slip_ratio_fl'), 'fr_max': mx('tire_slip_ratio_fr'),
                'rl_max': mx('tire_slip_ratio_rl'), 'rr_max': mx('tire_slip_ratio_rr'),
                'front_slip_avg': safe_mean([m('tire_slip_ratio_fl'), m('tire_slip_ratio_fr')]),
                'rear_slip_avg' : safe_mean([m('tire_slip_ratio_rl'), m('tire_slip_ratio_rr')]),
            },
            'tire_work_distribution': {
                'front_vs_rear_temp': safe_mean([m('tire_temp_fl'), m('tire_temp_fr')]) - safe_mean([m('tire_temp_rl'), m('tire_temp_rr')]),
                'left_vs_right_temp' : safe_mean([m('tire_temp_fl'), m('tire_temp_rl')]) - safe_mean([m('tire_temp_fr'), m('tire_temp_rr')]),
            },
        },
        'engine_analysis': {
            'power_delivery': {
                'avg_rpm': m('rpm'),
                'max_rpm': mx('rpm'),
                'rpm_utilization': safe_divide(m('rpm'), mx('rev_limiter'), 0),
                'avg_gear': safe_mean([g for g in col(data, 'current_gear') if g > 0]),
            },
            'thermal_management': {
                'avg_oil_temp': m('oil_temp'),
                'max_oil_temp': mx('oil_temp'),
                'avg_water_temp': m('water_temp'),
                'max_water_temp': mx('water_temp'),
                'avg_oil_pressure': m('oil_pressure'),
            },
            'forced_induction': {
                'has_turbo': mx('has_turbo'),
                'avg_boost': m('boost_pressure') if mx('has_turbo') else 0.0,
                'max_boost': mx('boost_pressure') if mx('has_turbo') else 0.0,
            },
        },
        'transmission_analysis': {
            'gear_ratios': {
                'gear_1': to_float(data[0].get('gear_ratio_1', 0)),
                'gear_2': to_float(data[0].get('gear_ratio_2', 0)),
                'gear_3': to_float(data[0].get('gear_ratio_3', 0)),
                'gear_4': to_float(data[0].get('gear_ratio_4', 0)),
                'gear_5': to_float(data[0].get('gear_ratio_5', 0)),
                'gear_6': to_float(data[0].get('gear_ratio_6', 0)),
                'gear_7': to_float(data[0].get('gear_ratio_7', 0)),
                'gear_8': to_float(data[0].get('gear_ratio_8', 0)),
            },
            'transmission_top_speed': to_float(data[0].get('transmission_top_speed', 0)),
            'gear_usage': calculate_gear_usage(data),
        },
        'clutch_analysis': {
            'avg_clutch_position': m('clutch_pedal'),
            'avg_clutch_engagement': m('clutch_engagement'),
            'clutch_events': sum(1 for row in data if to_float(row.get('clutch_pedal'),0) > 0.1),
        },
        'phase_analysis': {
            'braking_phase': analyze_driving_phase(braking_data) if braking_data else None,
            'cornering_phase': analyze_driving_phase(cornering_data) if cornering_data else None,
            'acceleration_phase': analyze_driving_phase(acceleration_data) if acceleration_data else None,
            'high_speed_phase': analyze_driving_phase(high_speed_data) if high_speed_data else None,
        },
    }
    return metrics

def calculate_gear_usage(data):
    """Calculate percentage time spent in each gear"""
    gear_counts = {}
    for row in data:
        gear = int(to_float(row.get('current_gear'), 0))
        if 1 <= gear <= 8:
            gear_counts[gear] = gear_counts.get(gear, 0) + 1
    total = sum(gear_counts.values())
    return {f'gear_{g}': round((c / total) * 100.0, 2) for g, c in gear_counts.items()} if total else {}

def analyze_driving_phase(phase_data):
    """Analyze a specific driving phase (braking, cornering, etc.)"""
    if not phase_data:
        return None
    
    def m(key): return safe_mean(col(phase_data, key))
    
    return {
        'data_points': len(phase_data),
        'avg_pitch': m('rotation_pitch'),
        'avg_roll': safe_mean([abs(x) for x in col(phase_data, 'rotation_roll')]),
        'avg_body_height': m('body_height'),
        'avg_speed': m('speed_kph'),
        'suspension_compression': {
            'fl': m('suspension_fl'), 'fr': m('suspension_fr'),
            'rl': m('suspension_rl'), 'rr': m('suspension_rr'),
        },
        'tire_temps': {
            'fl': m('tire_temp_fl'), 'fr': m('tire_temp_fr'),
            'rl': m('tire_temp_rl'), 'rr': m('tire_temp_rr'),
        },
        'tire_slip_ratios': {
            'fl': m('tire_slip_ratio_fl'), 'fr': m('tire_slip_ratio_fr'),
            'rl': m('tire_slip_ratio_rl'), 'rr': m('tire_slip_ratio_rr'),
        },
        'engine_metrics': {
            'avg_rpm': m('rpm'),
            'avg_throttle': m('throttle_percent'),
            'avg_brake': m('brake_percent'),
        },
    }

def calculate_session_summary(all_lap_metrics, car_type, car_name, thresholds):
    """Calculate session-wide summary statistics"""
    num_laps = len(all_lap_metrics)
    if num_laps == 0:
        return None

    session = {
        'car_info': {
            'car_name': car_name,
            'car_type': car_type,
            'car_type_description': thresholds['description'],
            'thresholds_used': thresholds,
        },
        'session_info': {
            'total_laps': num_laps,
            'processed_at': datetime.now().isoformat(),
            'avg_lap_time': safe_mean([lap['lap_summary']['lap_time'] for lap in all_lap_metrics]),
            'fastest_lap': safe_min([lap['lap_summary']['lap_time'] for lap in all_lap_metrics if lap['lap_summary']['lap_time'] > 0]),
            'slowest_lap': safe_max([lap['lap_summary']['lap_time'] for lap in all_lap_metrics]),
            'avg_max_speed': safe_mean([lap['lap_summary']['max_speed'] for lap in all_lap_metrics]),
            'avg_max_rpm': safe_mean([lap['lap_summary']['max_rpm'] for lap in all_lap_metrics]),
        },
        'units_reference': {
            'speed': 'kph (kilometers per hour)',
            'temperature': 'Celsius (assumed from GT7 output)',
            'suspension': 'meters (compression distance)',
            'body_height': 'millimeters (ride height)',
            'rpm': 'revolutions per minute',
            'slip_ratio': 'dimensionless (tire_speed / car_speed)',
            'angles': 'radians for rotation, degrees for banking',
            'time': 'seconds',
            'susp_velocity': 'millimeters per second (mm/s)',
            'heave': 'millimeters (avg suspension compression)',
        },
        'consistency_analysis': calculate_consistency_scores(all_lap_metrics),
        'tire_degradation': track_tire_degradation(all_lap_metrics),
        'tire_slip_analysis': analyze_tire_slip_patterns(all_lap_metrics, thresholds),
        'platform_behavior': {
            'avg_pitch': safe_mean([lap['platform_dynamics']['avg_pitch'] for lap in all_lap_metrics]),
            'avg_pitch_range': safe_mean([lap['platform_dynamics']['max_pitch_range'] for lap in all_lap_metrics]),
            'avg_roll': safe_mean([lap['platform_dynamics']['avg_roll'] for lap in all_lap_metrics]),
            'max_roll': safe_mean([lap['platform_dynamics']['max_roll'] for lap in all_lap_metrics]),
            'avg_heave_mm': safe_mean([lap['platform_dynamics']['avg_heave_mm'] for lap in all_lap_metrics]),
            'heave_range_mm': safe_mean([lap['platform_dynamics']['heave_range_mm'] for lap in all_lap_metrics]),
            'pitch_consistency': safe_mean([lap['platform_dynamics']['pitch_stability'] for lap in all_lap_metrics]),
            'roll_consistency': safe_mean([lap['platform_dynamics']['roll_stability'] for lap in all_lap_metrics]),
        },
        'damper_summary': {
            'note': 'See individual_laps for full histograms',
            'max_velocities': {
                'fl_reb': safe_max([lap['damper_analysis']['max_velocity']['fl_reb'] for lap in all_lap_metrics]),
                'fl_comp': safe_min([lap['damper_analysis']['max_velocity']['fl_comp'] for lap in all_lap_metrics]),
            }
        },
        'road_summary': {
            'avg_banking': safe_mean([lap['road_analysis']['banking']['avg_angle'] for lap in all_lap_metrics]),
            'max_banking': safe_max([lap['road_analysis']['banking']['max_right_bank'] for lap in all_lap_metrics]),
        },
        'suspension_summary': {
            'avg_body_height': safe_mean([lap['suspension_behavior']['avg_body_height'] for lap in all_lap_metrics]),
            'lowest_body_height': safe_min([lap['suspension_behavior']['min_body_height'] for lap in all_lap_metrics]),
            'body_height_consistency': safe_mean([lap['suspension_behavior']['body_height_variation'] for lap in all_lap_metrics]),
            'corner_compression_avg': {
                'fl': safe_mean([lap['suspension_behavior']['suspension_travel']['fl_avg'] for lap in all_lap_metrics]),
                'fr': safe_mean([lap['suspension_behavior']['suspension_travel']['fr_avg'] for lap in all_lap_metrics]),
                'rl': safe_mean([lap['suspension_behavior']['suspension_travel']['rl_avg'] for lap in all_lap_metrics]),
                'rr': safe_mean([lap['suspension_behavior']['suspension_travel']['rr_avg'] for lap in all_lap_metrics]),
            },
        },
        'tire_summary': {
            'temperature_averages': {
                'fl': safe_mean([lap['tire_analysis']['temperatures']['fl_avg'] for lap in all_lap_metrics]),
                'fr': safe_mean([lap['tire_analysis']['temperatures']['fr_avg'] for lap in all_lap_metrics]),
                'rl': safe_mean([lap['tire_analysis']['temperatures']['rl_avg'] for lap in all_lap_metrics]),
                'rr': safe_mean([lap['tire_analysis']['temperatures']['rr_avg'] for lap in all_lap_metrics]),
            },
            'slip_ratio_averages': {
                'fl': safe_mean([lap['tire_analysis']['slip_ratios']['fl_avg'] for lap in all_lap_metrics]),
                'fr': safe_mean([lap['tire_analysis']['slip_ratios']['fr_avg'] for lap in all_lap_metrics]),
                'rl': safe_mean([lap['tire_analysis']['slip_ratios']['rl_avg'] for lap in all_lap_metrics]),
                'rr': safe_mean([lap['tire_analysis']['slip_ratios']['rr_avg'] for lap in all_lap_metrics]),
            },
        },
        'engine_summary': {
            'avg_rpm_utilization': safe_mean([lap['engine_analysis']['power_delivery']['rpm_utilization'] for lap in all_lap_metrics]),
            'avg_oil_temp': safe_mean([lap['engine_analysis']['thermal_management']['avg_oil_temp'] for lap in all_lap_metrics]),
            'avg_water_temp': safe_mean([lap['engine_analysis']['thermal_management']['avg_water_temp'] for lap in all_lap_metrics]),
        },
        'transmission_summary': {
            'gear_ratios': all_lap_metrics[0]['transmission_analysis']['gear_ratios'],
            'transmission_top_speed': all_lap_metrics[0]['transmission_analysis']['transmission_top_speed'],
        },
        'individual_laps': all_lap_metrics,
    }
    return session

def calculate_consistency_scores(all_lap_metrics):
    """Calculate driving consistency metrics"""
    if len(all_lap_metrics) < 2:
        return {'note': 'Need at least 2 laps for consistency analysis'}

    lap_times = [lap['lap_summary']['lap_time'] for lap in all_lap_metrics if lap['lap_summary']['lap_time'] > 0]
    if not lap_times:
        return {'note': 'No valid lap times found'}
    
    max_speeds = [lap['lap_summary']['max_speed'] for lap in all_lap_metrics]

    braking_speeds = []
    apex_speeds = []
    for lap in all_lap_metrics:
        bp = lap['phase_analysis'].get('braking_phase')
        if bp:
            braking_speeds.append(bp['avg_speed'])
        cp = lap['phase_analysis'].get('cornering_phase')
        if cp:
            apex_speeds.append(cp['avg_speed'])

    def cv(arr):
        """Coefficient of variation"""
        if not arr or len(arr) < 2:
            return 0.0
        mean_val = safe_mean(arr)
        if mean_val == 0:
            return 0.0
        return safe_divide(safe_std(arr), mean_val, 0) * 100.0

    def score_from_cv(c, scale):
        """Convert CV to 0-100 score"""
        s = 100.0 - min(c * scale, 100.0)
        return max(0.0, float(s))

    lap_time_cv = cv(lap_times)
    lap_time_score = score_from_cv(lap_time_cv, 10.0)
    apex_score = score_from_cv(cv(apex_speeds), 5.0) if apex_speeds else 100.0
    braking_score = score_from_cv(cv(braking_speeds), 5.0) if braking_speeds else 100.0
    overall = lap_time_score * 0.5 + apex_score * 0.3 + braking_score * 0.2

    return {
        'lap_time_consistency': {
            'std_deviation': float(safe_std(lap_times)),
            'coefficient_of_variation': lap_time_cv,
            'best_lap': float(safe_min(lap_times)),
            'worst_lap': float(safe_max(lap_times)),
            'delta': float(safe_max(lap_times) - safe_min(lap_times)),
        },
        'speed_consistency': {
            'max_speed_std': float(safe_std(max_speeds)),
            'max_speed_range': float(safe_max(max_speeds) - safe_min(max_speeds)),
        },
        'braking_consistency': {
            'speed_std': float(safe_std(braking_speeds)) if braking_speeds else 0.0,
            'note': 'Lower std = more consistent braking points',
        },
        'apex_speed_consistency': {
            'std_deviation': float(safe_std(apex_speeds)) if apex_speeds else 0.0,
            'coefficient_of_variation': cv(apex_speeds) if apex_speeds else 0.0,
            'note': 'Lower std = more consistent corner entry/apex speeds',
        },
        'overall_consistency_score': {
            'overall_score': round(overall, 2),
            'lap_time_score': round(lap_time_score, 2),
            'apex_score': round(apex_score, 2),
            'braking_score': round(braking_score, 2),
            'interpretation': interpret_consistency_score(overall),
        },
    }

def interpret_consistency_score(score):
    """Interpret consistency score"""
    if score >= 90: return 'Excellent - Very consistent driving'
    if score >= 75: return 'Good - Minor variations lap-to-lap'
    if score >= 60: return 'Fair - Moderate inconsistencies'
    if score >= 40: return 'Poor - Significant variations'
    return 'Very Poor - High inconsistency'

def track_tire_degradation(all_lap_metrics):
    """Track tire degradation over stint"""
    if len(all_lap_metrics) < 3:
        return {'note': 'Need at least 3 laps for degradation analysis'}

    corners = ['fl','fr','rl','rr']
    tire_temps = {c: [lap['tire_analysis']['temperatures'][f'{c}_avg'] for lap in all_lap_metrics] for c in corners}
    tire_slip = {c: [lap['tire_analysis']['slip_ratios'][f'{c}_avg'] for lap in all_lap_metrics] for c in corners}

    degradation = {
        'temperature_trends': {},
        'slip_trends': {},
        'degradation_rate': {},
    }

    n = len(all_lap_metrics)
    for c in corners:
        t0, t1 = tire_temps[c][0], tire_temps[c][-1]
        s0, s1 = tire_slip[c][0], tire_slip[c][-1]
        temp_rate = safe_divide(t1 - t0, n, 0)
        slip_rate = safe_divide(s1 - s0, n, 0)
        degradation['temperature_trends'][c] = {
            'start_temp': round(t0, 2), 
            'end_temp': round(t1, 2), 
            'total_change': round(t1 - t0, 2), 
            'rate_per_lap': round(temp_rate, 4)
        }
        degradation['slip_trends'][c] = {
            'start_slip': round(s0, 4), 
            'end_slip': round(s1, 4), 
            'total_change': round(s1 - s0, 4), 
            'rate_per_lap': round(slip_rate, 6)
        }
        score = abs(temp_rate) * 0.3 + abs(slip_rate) * 100.0 * 0.7
        degradation['degradation_rate'][c] = round(score, 4)

    avg_deg = float(safe_mean(list(degradation['degradation_rate'].values())))
    most = max(degradation['degradation_rate'], key=degradation['degradation_rate'].get) if degradation['degradation_rate'] else 'unknown'
    least = min(degradation['degradation_rate'], key=degradation['degradation_rate'].get) if degradation['degradation_rate'] else 'unknown'

    lap_times = [lap['lap_summary']['lap_time'] for lap in all_lap_metrics if lap['lap_summary']['lap_time'] > 0]
    stint = {
        'average_degradation_rate': round(avg_deg, 4),
        'most_degraded_tire': most,
        'least_degraded_tire': least,
        'interpretation': interpret_degradation(avg_deg),
    }
    if len(lap_times) >= 2:
        delta = lap_times[-1] - lap_times[0]
        stint['lap_time_delta'] = round(float(delta), 3)
        stint['time_lost_per_lap'] = round(safe_divide(delta, len(lap_times), 0), 3)

    degradation['stint_summary'] = stint
    return degradation

def interpret_degradation(rate):
    """Interpret degradation rate"""
    if rate < 0.5: return 'Minimal degradation - tires very stable'
    if rate < 1.0: return 'Low degradation - good tire management'
    if rate < 2.0: return 'Moderate degradation - normal tire wear'
    if rate < 4.0: return 'High degradation - aggressive driving or setup'
    return 'Very high degradation - tires wearing quickly'

def analyze_tire_slip_patterns(all_lap_metrics, thresholds):
    """Analyze tire slip patterns and provide setup recommendations"""
    corners = ['fl','fr','rl','rr']
    all_slip = {c: [] for c in corners}
    for lap in all_lap_metrics:
        for c in corners:
            all_slip[c].append(lap['tire_analysis']['slip_ratios'][f'{c}_avg'])

    overall = {}
    for c in corners:
        overall[c] = {
            'avg_slip': round(safe_mean(all_slip[c]), 4),
            'max_slip': round(safe_max(all_slip[c]), 4),
            'slip_variance': round(safe_std(all_slip[c]), 4),
        }

    front_avg = safe_mean([overall['fl']['avg_slip'], overall['fr']['avg_slip']])
    rear_avg = safe_mean([overall['rl']['avg_slip'], overall['rr']['avg_slip']])
    balance_metric = front_avg - rear_avg

    def tendency(x):
        if x > 0.05: return 'Oversteer tendency - Front tires losing grip more than rear'
        if x < -0.05: return 'Understeer tendency - Rear tires losing grip more than front'
        return 'Neutral balance - Good front/rear grip balance'

    # Detect traction loss incidents using adaptive threshold
    incidents = {}
    threshold = thresholds['slip_traction_loss']
    for lap in all_lap_metrics:
        lap_num = lap.get('lap_number', 0)
        found = []
        for c in corners:
            max_slip = lap['tire_analysis']['slip_ratios'][f'{c}_max']
            if max_slip > threshold:
                found.append({
                    'tire': c.upper(),
                    'max_slip_ratio': round(float(max_slip), 3),
                    'severity': 'High' if max_slip > (threshold + 0.1) else 'Moderate'
                })
        if found:
            incidents[f'lap_{lap_num}'] = found

    # Generate setup recommendations
    recs = []
    if balance_metric > 0.1:
        recs.append('OVERSTEER: Consider softer front anti-roll bar or stiffer rear')
        recs.append('OVERSTEER: Increase front tire pressure or reduce rear pressure')
    elif balance_metric < -0.1:
        recs.append('UNDERSTEER: Consider stiffer front anti-roll bar or softer rear')
        recs.append('UNDERSTEER: Reduce front tire pressure or increase rear pressure')
    else:
        recs.append('BALANCED: Good slip distribution front-to-rear')

    left = safe_mean([overall['fl']['avg_slip'], overall['rl']['avg_slip']])
    right = safe_mean([overall['fr']['avg_slip'], overall['rr']['avg_slip']])
    if abs(left - right) > 0.05:
        if left > right:
            recs.append('ASYMMETRIC: Left side slipping more - check alignment or tire pressures')
        else:
            recs.append('ASYMMETRIC: Right side slipping more - check alignment or tire pressures')

    avg_slip_all = safe_mean([overall[c]['avg_slip'] for c in corners])
    if avg_slip_all > 1.1:
        recs.append('HIGH SLIP: Overall grip low - consider softer suspension or better tires')
    elif avg_slip_all < 0.95:
        recs.append('LOW SLIP: Excellent grip - setup working well')

    # Phase-specific slip analysis
    phase_slip = {'braking': {'front': [], 'rear': []},
                  'cornering': {'front': [], 'rear': []},
                  'acceleration': {'front': [], 'rear': []}}
    
    for lap in all_lap_metrics:
        for phase in ('braking_phase','cornering_phase','acceleration_phase'):
            ph = lap['phase_analysis'].get(phase)
            if ph and ph.get('tire_slip_ratios'):
                d = ph['tire_slip_ratios']
                front = safe_divide(to_float(d.get('fl',0)) + to_float(d.get('fr',0)), 2, 0)
                rear = safe_divide(to_float(d.get('rl',0)) + to_float(d.get('rr',0)), 2, 0)
                if phase == 'braking_phase':
                    phase_slip['braking']['front'].append(front)
                    phase_slip['braking']['rear'].append(rear)
                elif phase == 'cornering_phase':
                    phase_slip['cornering']['front'].append(front)
                    phase_slip['cornering']['rear'].append(rear)
                elif phase == 'acceleration_phase':
                    phase_slip['acceleration']['front'].append(front)
                    phase_slip['acceleration']['rear'].append(rear)

    phase_results = {}
    for ph in ('braking','cornering','acceleration'):
        fr = phase_slip[ph]['front']
        rr = phase_slip[ph]['rear']
        if fr and rr:
            phase_results[ph] = {
                'front_avg_slip': round(float(safe_mean(fr)), 4),
                'rear_avg_slip': round(float(safe_mean(rr)), 4),
                'balance': round(float(safe_mean(fr) - safe_mean(rr)), 4),
            }

    return {
        'overall_slip_characteristics': overall,
        'traction_loss_incidents': incidents,
        'balance_analysis': {
            'front_avg_slip': round(float(front_avg), 4),
            'rear_avg_slip': round(float(rear_avg), 4),
            'balance_metric': round(float(balance_metric), 4),
            'tendency': tendency(balance_metric),
        },
        'recommendations': recs,
        'phase_slip_analysis': phase_results,
        'threshold_used': threshold,
    }

# ==================== MAIN ====================

def main():
    if len(sys.argv) != 2:
        print("Usage: python gt7_analyzer_fixed_v2.py <session_folder>")
        return

    session_folder = sys.argv[1]
    print(f"GT7 Telemetry Analyzer v3.1 (TEST) - Platform Dynamics & Damper Analysis")
    print(f"Processing telemetry session: {session_folder}")
    print("=" * 70)

    result = process_session_folder(session_folder)
    if not result:
        return

    print("\n" + "=" * 70)
    print("SESSION ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\n🏎️  CAR INFORMATION")
    print(f"  Car: {result['car_info']['car_name']}")
    print(f"  Type: {result['car_info']['car_type'].upper()}")
    print(f"  Description: {result['car_info']['car_type_description']}")

    print(f"\n📊 SESSION INFO")
    print(f"  Laps processed: {result['session_info']['total_laps']}")
    print(f"  Average lap time: {result['session_info']['avg_lap_time']:.3f}s")
    print(f"  Fastest lap: {result['session_info']['fastest_lap']:.3f}s")
    print(f"  Average max speed: {result['session_info']['avg_max_speed']:.1f} kph")

    print(f"\n🌊 PLATFORM DYNAMICS (NEW)")
    plat = result['platform_behavior']
    print(f"  Avg Heave: {plat['avg_heave_mm']:.2f} mm")
    print(f"  Heave Range: {plat['heave_range_mm']:.2f} mm")
    print(f"  Roll Stability (StdDev): {plat['roll_consistency']:.4f}")
    print(f"  Pitch Stability (StdDev): {plat['pitch_consistency']:.4f}")
    
    print(f"\n📉 DAMPER ANALYSIS (NEW)")
    damp = result.get('damper_summary', {})
    max_v = damp.get('max_velocities', {})
    print(f"  Max Compression Velocity: {max_v.get('fl_comp', 0):.1f} mm/s (FL)")
    print(f"  Max Rebound Velocity: {max_v.get('fl_reb', 0):.1f} mm/s (FL)")

    # Show FL histogram diagnostics from first lap
    if result['individual_laps']:
        fl_diag = result['individual_laps'][0]['damper_analysis']['diagnostics']['fl']
        print(f"  FL Histogram Analysis:")
        print(f"    Center Peak: {fl_diag['center_peak_percent']:.1f}% (ideal: 10-15%)")
        print(f"    Compression: {fl_diag['compression_percent']:.1f}% | Rebound: {fl_diag['rebound_percent']:.1f}%")
        print(f"    Assessment: {fl_diag['assessment']}")
        if fl_diag['warnings']:
            for warning in fl_diag['warnings']:
                print(f"    ⚠️  {warning}")

    print(f"  (See JSON for full histograms & all corners)")

    print(f"\n🎯 CONSISTENCY ANALYSIS")
    cons = result['consistency_analysis']
    overall = cons.get('overall_consistency_score', {})
    if overall:
        print(f"  Overall Score: {overall['overall_score']}/100 - {overall['interpretation']}")
        print(f"  Lap Time Consistency: {overall['lap_time_score']:.1f}/100")
    else:
        print("  Not enough laps for consistency analysis.")

    print(f"\n🔥 TIRE DEGRADATION")
    deg = result['tire_degradation']
    stint = deg.get('stint_summary', {})
    if stint:
        print(f"  {stint['interpretation']}")
    else:
        print("  Not enough laps for degradation analysis.")

    print(f"\n⚡ TIRE SLIP / TRACTION ANALYSIS")
    slip = result['tire_slip_analysis']
    balance = slip['balance_analysis']
    print(f"  {balance['tendency']}")
    print(f"  Balance metric: {balance['balance_metric']:+.4f}")
    
    print("\n" + "=" * 70)
    print("✅ Full analysis saved to JSON file")
    print("=" * 70)

if __name__ == "__main__":
    main()
