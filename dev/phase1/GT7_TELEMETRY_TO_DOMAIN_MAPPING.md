# GT7 Telemetry → Domain JSON Mapping

**Purpose:** Complete mapping of GT7 UDP Packet fields to Phase 1 domain JSONs

---

## GT7 UDP Packet Structure (296 bytes total)

GT7 sends "Packet A" at 60 Hz over UDP port 33740. Here's **EVERY field** we receive:

### Complete Field List

| Offset | Field | Type | Description | Domain |
|--------|-------|------|-------------|--------|
| **POSITION & ORIENTATION** |||||
| 0x04-0x0F | pos_x, pos_y, pos_z | float×3 | 3D position coordinates | balance |
| 0x10-0x1B | vel_x, vel_y, vel_z | float×3 | 3D velocity vectors | balance |
| 0x1C-0x27 | rot_pitch, rot_yaw, rot_roll | float×3 | Body rotation | balance |
| 0x28 | north_orientation | float | Compass heading | metadata |
| 0x2C-0x37 | ang_vel_x, ang_vel_y, ang_vel_z | float×3 | Angular velocity | balance |
| **SUSPENSION & RIDE HEIGHT** |||||
| 0x38 | body_height | float | Ride height (ground clearance) | suspension |
| 0xC4-0xD3 | suspension_fl/fr/rl/rr | float×4 | Suspension travel (mm) | suspension |
| **ENGINE** |||||
| 0x3C | rpm | float | Engine RPM | drivetrain |
| 0x91 | throttle | byte | Throttle position (0-100%) | drivetrain |
| 0x92 | brake | byte | Brake pressure (0-100%) | drivetrain |
| 0x58 | water_temp | float | Water temperature (°C) | drivetrain |
| 0x5C | oil_temp | float | Oil temperature (°C) | drivetrain |
| 0x54 | oil_pressure | float | Oil pressure (bar) | drivetrain |
| 0x50 | boost_pressure | float | Turbo boost (bar) | drivetrain |
| **FUEL** |||||
| 0x44-0x4B | fuel_level, fuel_capacity | float×2 | Fuel level/capacity (L) | metadata |
| **SPEED** |||||
| 0x4C | speed_mps | float | Car speed (m/s) | metadata |
| **TIRES** |||||
| 0x60-0x6F | tire_temp_fl/fr/rl/rr | float×4 | Tire surface temps (°C) | tires |
| 0xA4-0xB3 | tire_rps_fl/fr/rl/rr | float×4 | Tire rotation speed (RPS) | tires |
| 0xB4-0xC3 | tire_radius_fl/fr/rl/rr | float×4 | Tire radius (m) | tires |
| (calculated) | tire_slip_ratio_fl/fr/rl/rr | float×4 | Slip ratio (tire_speed/car_speed) | tires |
| **LAP TIMING** |||||
| 0x70 | pktid | int32 | Packet counter | metadata |
| 0x74 | curlap | int16 | Current lap number | metadata |
| 0x76 | total_laps | int16 | Total laps in session | metadata |
| 0x78 | best_lap_time_ms | int32 | Best lap time (ms) | metadata |
| 0x7C | last_lap_time_ms | int32 | Last lap time (ms) | metadata |
| 0x80 | time_on_track_ms | int32 | Total time on track (ms) | metadata |
| **GEARING** |||||
| 0x90 | current_gear | byte | Current gear (0-8) | drivetrain |
| 0x90 | suggested_gear | byte | Suggested gear (0-8) | drivetrain |
| 0x104-0x123 | gear_ratio_1..8 | float×8 | Gear ratios | drivetrain |
| 0x100 | transmission_top_speed | float | Max speed in top gear | drivetrain |
| **CLUTCH** |||||
| 0xF4-0xFF | clutch_pedal, clutch_engagement, rpm_clutch_gearbox | float×3 | Clutch data | drivetrain |
| **CAR INFO** |||||
| 0x124 | car_code | int32 | GT7 car database ID | metadata |
| **RACE INFO** |||||
| 0x84 | pre_race_start_position | int16 | Starting grid position | metadata |
| 0x86 | pre_race_num_cars | int16 | Number of cars in race | metadata |
| **ENGINE LIMITS** |||||
| 0x88 | rev_warning | uint16 | Warning RPM (shift light) | drivetrain |
| 0x8A | rev_limiter | uint16 | Max RPM (limiter) | drivetrain |
| 0x8C | estimated_top_speed | int16 | Estimated top speed (kph) | drivetrain |
| **FLAGS** |||||
| 0x8E | flags | uint16 | Simulator state flags | metadata |
| **ROAD SURFACE** |||||
| 0x94-0xA3 | road_plane_x/y/z/distance | float×4 | Road surface normal vector | suspension |
| **UNKNOWN** |||||
| 0xD4-0xF3 | unknown_float_1..8 | float×8 | Unknown (possibly tire zones?) | (skip for now) |

---

## Domain JSON Mappings

### 1. metadata.json

**Purpose:** Session info, car, track, lap times

**Fields from UDP:**
```python
{
  "session_id": f"{timestamp}",  # Generated (not from UDP)
  "car": {
    "code": car_code,              # 0x124
    "name": CAR_DATABASE[car_code], # Lookup from database
    "classification": classify_car(car_code)  # Our logic
  },
  "track": {
    "name": "Unknown",  # Not in UDP! (user provides or we detect from coordinates)
    "type": "balanced"  # Not in UDP! (user provides)
  },
  "session_summary": {
    "start_time": session_start,   # Generated
    "current_lap": curlap,          # 0x74
    "total_laps": total_laps,       # 0x76
    "best_lap_ms": best_lap_time_ms, # 0x78
    "last_lap_ms": last_lap_time_ms, # 0x7C
    "time_on_track_ms": time_on_track_ms, # 0x80
    "speed_kph": speed_mps * 3.6,   # 0x4C (converted)
    "fuel_level": fuel_level,       # 0x44
    "fuel_capacity": fuel_capacity, # 0x48
    "is_electric": fuel_capacity <= 0
  }
}
```

---

### 2. suspension.json

**Purpose:** Suspension travel, bottoming, ride height

**Fields from UDP:**
```python
{
  "travel_mm": {
    "FL": {
      "current": suspension_fl,  # 0xC4 (converted to mm)
      "avg": calculate_avg(),
      "max": track_max(),
      "min": track_min(),
      "samples": last_10_samples
    },
    # Same for FR (0xC8), RL (0xCC), RR (0xD0)
  },
  "bottoming_events": {
    # Calculated: if travel < threshold, increment counter
    "detected": any_bottoming,
    "FL_count": fl_bottom_events,
    "FR_count": fr_bottom_events,
    "RL_count": rl_bottom_events,
    "RR_count": rr_bottom_events
  },
  "current_ride_height_mm": {
    "front": body_height,  # 0x38 (or avg of FL/FR travel)
    "rear": body_height    # Calculate from RL/RR
  },
  "road_surface": {
    # Road plane data (might indicate bumps/kerbs)
    "plane_x": road_plane_x,  # 0x94
    "plane_y": road_plane_y,  # 0x98
    "plane_z": road_plane_z,  # 0x9C
    "distance": road_plane_distance  # 0xA0
  }
}
```

---

### 3. tires.json

**Purpose:** Tire temps, slip, wear

**Fields from UDP:**
```python
{
  "temps_celsius": {
    "FL": {
      # GT7 only gives us ONE surface temp per tire (not 3 zones)
      "surface": tire_temp_fl,  # 0x60
      "avg": calculate_avg(),
      "max": track_max(),
      "min": track_min(),
      "samples": last_10_samples
    },
    # Same for FR (0x64), RL (0x68), RR (0x6C)
  },
  "slip_ratio": {
    "FL": {
      # Calculated: (tire_rps × tire_radius × 3.6) / car_speed
      "current": tire_slip_ratio_fl,
      "avg": calculate_avg(),
      "max": track_max(),
      "events": count_slip_events(ratio > 1.15),  # Threshold
      "samples": last_10_samples
    },
    # Same for FR, RL, RR
  },
  "rotation_speed_rps": {
    "FL": tire_rps_fl,  # 0xA4 (diagnostic data)
    # Same for FR (0xA8), RL (0xAC), RR (0xB0)
  },
  "wear_pct": {
    # NOT IN UDP! GT7 doesn't send wear data
    # We'd need to estimate from tire_radius changes over time
    "FL": estimate_wear_from_radius(),
    "FR": estimate_wear_from_radius(),
    "RL": estimate_wear_from_radius(),
    "RR": estimate_wear_from_radius()
  }
}
```

**NOTE:** GT7 UDP doesn't give us tire wear directly. We can either:
1. Estimate from tire radius changes (radius decreases as tire wears)
2. Leave as 0.0 for now
3. Add later if we find a formula

---

### 4. aero.json

**Purpose:** Ride height, downforce, rake

**Fields from UDP:**
```python
{
  "ride_height_mm": {
    "avg_front": body_height,  # 0x38 (or calc from suspension_fl/fr)
    "avg_rear": calculate_rear_height(),  # From suspension_rl/rr
    "min_front": track_min(),
    "min_rear": track_min(),
    "rake_mm": rear_height - front_height,
    "samples_front": last_10_samples,
    "samples_rear": last_10_samples
  },
  "downforce_estimate_lbs": {
    # NOT IN UDP! Must look up from car database
    "total": lookup_from_car_database(car_code),
    "source": "car_database_lookup"
  },
  "speed_correlation": {
    # Track when car is at high speed (for aero effects)
    "high_speed_zones_mph": high_speed_samples,
    "avg_high_speed_mph": avg_high_speed
  }
}
```

---

### 5. drivetrain.json

**Purpose:** Power delivery, wheel spin, gearing

**Fields from UDP:**
```python
{
  "power_delivery": {
    "rpm": rpm,  # 0x3C
    "avg_rpm": calculate_avg(),
    "max_rpm": rev_limiter,  # 0x8A
    "throttle_pct": throttle,  # 0x91
    "avg_throttle_pct": calculate_avg(),
    "samples_rpm": last_10_samples,
    "samples_throttle": last_10_samples
  },
  "wheel_spin_events": {
    # Calculated: if tire_slip_ratio > threshold while throttle > 50%
    "total_count": count_all_spin_events(),
    "FL_count": 0,  # FWD cars only
    "FR_count": 0,  # FWD cars only
    "RL_count": rr_spin_count,  # RWD/AWD
    "RR_count": rr_spin_count,  # RWD/AWD
    "severity_avg": avg_slip_ratio_during_events
  },
  "gear_usage": {
    # Track which gears are used (histogram)
    "1": gear_1_time_pct,
    "2": gear_2_time_pct,
    # ... calculated from current_gear samples
  },
  "gearing": {
    "current_gear": current_gear,  # 0x90
    "suggested_gear": suggested_gear,  # 0x90
    "ratios": [
      gear_ratio_1,  # 0x104
      gear_ratio_2,  # 0x108
      # ... through gear_ratio_8 (0x120)
    ],
    "transmission_top_speed": transmission_top_speed  # 0x100
  },
  "engine_temps": {
    "water_temp_c": water_temp,  # 0x58
    "oil_temp_c": oil_temp,      # 0x5C
    "oil_pressure_bar": oil_pressure  # 0x54
  }
}
```

---

### 6. balance.json

**Purpose:** Weight transfer, stability, g-forces

**Fields from UDP:**
```python
{
  "weight_transfer": {
    "lateral_g": {
      # Calculated from ang_vel_z or vel_x/vel_y changes
      "current": calculate_lateral_g(ang_vel_z),  # 0x34
      "avg": calculate_avg(),
      "max": track_max(),
      "min": track_min(),
      "samples": last_10_samples
    },
    "longitudinal_g": {
      # Calculated from vel_z changes (accel/brake)
      "current": calculate_longitudinal_g(vel_z),  # 0x18
      "avg": calculate_avg(),
      "max_braking": track_min(),  # Negative
      "max_accel": track_max(),    # Positive
      "samples": last_10_samples
    }
  },
  "rotation": {
    "pitch": rot_pitch,  # 0x1C (forward/back)
    "yaw": rot_yaw,      # 0x20 (turning)
    "roll": rot_roll     # 0x24 (side to side)
  },
  "stability_metrics": {
    # Analyzed from rotation and g-force patterns
    "understeer_events": count_understeer(),  # Low yaw change despite steering
    "oversteer_events": count_oversteer(),    # Excessive yaw change
    "balance_bias": analyze_balance()         # "understeer" / "oversteer" / "neutral"
  },
  "corner_analysis": {
    # Analyzed from brake→turn→accel patterns
    "entry_stability": "good",   # Based on pitch/roll during braking
    "mid_corner_grip": "excellent",  # Based on lateral_g vs slip
    "exit_traction": "moderate"  # Based on wheel spin events
  }
}
```

---

## What GT7 Does NOT Send

These fields we need to provide or calculate ourselves:

| Field | Why Not in UDP | Solution |
|-------|----------------|----------|
| **Track name** | Not transmitted | User provides or detect from GPS coordinates |
| **Track type** | Not transmitted | User provides (high_speed/technical/balanced) |
| **Tire wear** | Not directly sent | Estimate from tire_radius changes or skip |
| **Tire temps (3 zones)** | Only surface temp | GT7 limitation - only 1 temp per tire |
| **Downforce** | Not transmitted | Lookup from car database by car_code |
| **Car classification** | Not transmitted | We classify based on car_code |

---

## Data Flow Summary

```
GT7 PlayStation → UDP Packet (60 Hz) → gt7_1r.py
    ↓
gt7_1r.py extracts fields using struct.unpack()
    ↓
DomainExtractors parse fields into domain structures
    ↓
Buffer 10 packets → Calculate stats (min/max/avg)
    ↓
JSONWriters write 6 domain JSONs (every 10 packets = ~6 Hz)
    ↓
claudetunes_cli.py reads domain JSONs
    ↓
Phase A/B/C/D workflow generates setup
```

---

## Answer to Your Question

**"How do we know what car data goes into which JSON?"**

We know because:
1. ✅ **GT7's UDP packet structure is documented** (296 bytes, fixed offsets)
2. ✅ **gt7_1r.py already parses every field** (we can see them in the code)
3. ✅ **We logically group fields by domain** (suspension fields → suspension.json)
4. ✅ **The mapping is deterministic** (offset 0xC4 is ALWAYS suspension_fl)

The UDP packet is our **contract** with GT7. Every packet has the same structure, same offsets, same fields. We just need to organize them by domain instead of dumping everything to CSV.

---

**Does this answer your question? Want to see the actual extractor code next?** 🚀
