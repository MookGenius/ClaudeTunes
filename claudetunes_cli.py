#!/usr/bin/env python3
"""
ClaudeTunes CLI - GT7 Physics-Based Suspension Tuning Tool
Version 8.5.3a-lite-hybrid

Generates GT7-calibrated suspension setups from telemetry data and car specifications
following the ClaudeTunes protocol.
"""

import json
import argparse
import sys
import math
from datetime import datetime
from pathlib import Path
import yaml


class ClaudeTunesCLI:
    """Main ClaudeTunes CLI application"""

    # Reference Tables from YAML Protocol (lines 353-434)
    GT7_DOWNFORCE_DATABASE = {
        'formula': {'df_range': (3000, 4000), 'freq_add': (0.4, 0.5), 'gt7_impact': '0.3-0.4s/1000lbs'},
        'gr2_lmp': {'df_range': (1500, 2000), 'freq_add': (0.3, 0.4), 'gt7_impact': '0.2-0.3s/1000lbs'},
        'gr3_gt3': {'df_range': (1000, 1500), 'freq_add': (0.2, 0.3), 'gt7_impact': '0.1-0.2s/1000lbs'},
        'gr4_race': {'df_range': (400, 800), 'freq_add': (0.1, 0.2), 'gt7_impact': '0.05-0.15s/1000lbs'},
        'street_perf': {'df_range': (100, 400), 'freq_add': (0.0, 0.1), 'gt7_impact': 'Minimal'},
        'street_std': {'df_range': (0, 100), 'freq_add': (0.0, 0.0), 'gt7_impact': 'Negligible'}
    }

    DIFFERENTIAL_BASELINES = {
        'FF': {'initial': (10, 15), 'accel': (30, 50), 'brake': (5, 10)},
        'FR': {'initial': (5, 20), 'accel': (15, 35), 'brake': (15, 40)},
        'MR': {'initial': (5, 20), 'accel': (15, 35), 'brake': (15, 40)},  # RWD
        'RR': {'initial': (10, 20), 'accel': (20, 35), 'brake': (20, 40)},
        'AWD': {'initial': (5, 15), 'accel': (15, 30), 'brake': (15, 35)}
    }

    PERFORMANCE_EXPECTATIONS = {
        'frequency_corrections': '0.3-2.0s',
        'drivetrain_architecture_fixes': '2.0-5.0s when bias wrong',
        'ride_height_optimization': '0.3-0.8s through CG/geometry',
        'cg_improvement': '5-8% per 25mm reduction',
        'corner_type_differential': '0.2-0.5s track-specific'
    }

    def __init__(self, protocol_path="ClaudeTunes v8.5.3b.yaml", track_type="balanced", conservative_ride_height=False):
        """Initialize with ClaudeTunes protocol"""
        self.protocol = self._load_protocol(protocol_path)
        self.car_data = {}
        self.telemetry = {}
        self.results = {}
        self.track_type = track_type  # 'high_speed', 'technical', or 'balanced'
        self.conservative_ride_height = conservative_ride_height  # Add 10mm buffer from minimum

    def _load_protocol(self, path):
        """Load ClaudeTunes YAML protocol"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Protocol file '{path}' not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing protocol YAML: {e}")
            sys.exit(1)

    def run(self, car_data_path, telemetry_path, output_path=None, session_folder=None):
        """Main execution workflow: A -> B -> C -> D"""
        print("═" * 60)
        print(f"  CLAUDETUNES v{self.protocol['claudetunes']['version']}")
        print("═" * 60)

        # Phase A: File Intake
        print("\n[Phase A] Loading and analyzing data...")
        self.phase_a_intake(car_data_path, telemetry_path)

        # Phase B: Physics Chain
        print("\n[Phase B] Calculating optimal frequencies...")
        self.phase_b_physics_chain()

        # Phase C: Constraint Evaluation
        print("\n[Phase C] Evaluating constraints and compensation...")
        self.phase_c_constraints()

        # Phase D: Setup Sheet Output
        print("\n[Phase D] Generating setup sheet...")
        setup_sheet = self.phase_d_output()

        # Determine output location
        if output_path:
            # If user specified a path, check if it should go in a session folder
            if session_folder:
                output_path = str(Path(session_folder) / Path(output_path).name)
            final_output_path = output_path
        elif session_folder:
            # Auto-generate filename in session folder
            car_name = self.car_data.get('name', 'Unknown').replace(' ', '_')
            track_suffix = f"_{self.track_type}" if self.track_type != 'balanced' else ""
            filename = f"{car_name}{track_suffix}_setup.txt"
            final_output_path = str(Path(session_folder) / filename)
        else:
            final_output_path = None

        # Save or display
        if final_output_path:
            # Ensure parent directory exists
            Path(final_output_path).parent.mkdir(parents=True, exist_ok=True)

            with open(final_output_path, 'w') as f:
                f.write(setup_sheet)
            print(f"\n✓ Setup sheet saved to: {final_output_path}")

        print("\n" + setup_sheet)
        return setup_sheet

    # ═══════════════════════════════════════════════════════════
    # PHASE A: TELEMETRY CORE
    # ═══════════════════════════════════════════════════════════

    def phase_a_intake(self, car_data_path, telemetry_path):
        """Phase A: Parse car data and telemetry, analyze suspension/balance"""

        # Load car data
        self.car_data = self._parse_car_data(car_data_path)
        print(f"  ✓ Loaded: {self.car_data['name']}")
        print(f"    Drivetrain: {self.car_data['drivetrain']} | {self.car_data['hp']} HP | {self.car_data['weight']} lbs")

        # Load telemetry JSON
        self.telemetry = self._parse_telemetry(telemetry_path)

        # Count data points from either format
        data_point_count = 0
        if 'suspension_travel' in self.telemetry:
            # Format 1: Direct suspension_travel arrays
            data_point_count = len(self.telemetry.get('suspension_travel', {}))
        elif 'individual_laps' in self.telemetry:
            # Format 2: gt7_2r.py analyzer format
            laps = self.telemetry.get('individual_laps', [])
            if laps and len(laps) > 0 and 'lap_summary' in laps[0]:
                data_point_count = laps[0]['lap_summary'].get('total_data_points', len(laps))
            else:
                data_point_count = len(laps)

        print(f"  ✓ Telemetry loaded: {data_point_count} data points")

        # Analyze suspension travel patterns
        self._analyze_suspension()

        # Analyze balance from telemetry
        self._analyze_balance()

        # Analyze tire temperatures
        self._analyze_tires()

        # Cross-validate all Phase A analyses (YAML protocol requirement)
        self._cross_validate_phase_a()

    def _parse_car_data(self, path):
        """Parse car data file into structured format"""
        data = {}
        with open(path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            if line == "CAR NAME":
                data['name'] = lines[i + 1]
                i += 2
            elif line == "DRIVETRAIN":
                data['drivetrain'] = lines[i + 1]
                i += 2
            elif line == "POWER OUTPUT AND WEIGHT":
                parts = lines[i + 1].split()
                data['hp'] = int(parts[0])
                data['torque'] = int(parts[2])
                data['weight'] = int(parts[4])
                data['balance'] = lines[i + 1].split('balance')[0].split(',')[1].strip()
                i += 2
            elif line == "TIRE COMPOUND":
                data['tire_compound'] = lines[i + 1]
                i += 2
            elif line == "CENTER OF GRAVITY HEIGHT":
                cg_line = lines[i + 1] if i + 1 < len(lines) else "450"
                # Parse CG height in mm (e.g., "450 mm" or just "450")
                data['cg_height'] = float(cg_line.replace('mm', '').strip())
                i += 2
            elif line == "SUSPENSION SETUP Front/Rear":
                # Parse ranges
                data['ranges'] = {}
                i += 1
            elif line == "BODY HEIGHT ADJUSTMENT":
                range_line = lines[i + 2] if i + 2 < len(lines) else ""
                if "range:" in range_line:
                    data['ranges']['ride_height'] = self._parse_range(range_line)
                i += 3
            elif line == "NATURAL FREQUENCY x.xx hz/x.xx hz":
                range_line = lines[i + 1] if i + 1 < len(lines) else ""
                if "range:" in range_line:
                    data['ranges']['frequency'] = self._parse_range(range_line)
                i += 2
            elif line == "ARB":
                data['ranges']['arb'] = {'front': (1, 10), 'rear': (1, 10)}
                i += 2
            elif line == "DIFFERENTIAL GEAR SETTINGS":
                data['ranges']['diff'] = {'min': 5, 'max': 60}
                # Parse front and rear differential current values
                # Format: "Front: 0/0/0 (range: 5 to 60 for all values)"
                # Format: "Rear: 10/20/30 (range: 5 to 60 for all values)"
                # Note: 0/0/0 means fully open diff (minimum locking), NOT "no diff"
                # Only absence of "Front:" line means no front differential
                if i + 1 < len(lines):
                    front_line = lines[i + 1]
                    if "Front:" in front_line:
                        # Has a front differential (even if values are 0/0/0)
                        data['has_front_diff'] = True
                    else:
                        data['has_front_diff'] = False
                if i + 2 < len(lines):
                    rear_line = lines[i + 2]
                # Parse torque split
                if i + 4 < len(lines) and "TORQUE SPLIT" in lines[i + 4]:
                    data['torque_split'] = lines[i + 5] if i + 5 < len(lines) else "0:100"
                    i += 6
                else:
                    data['torque_split'] = "0:100"
                    i += 3
            elif line == "AERODYNAMICS":
                if i + 2 < len(lines):
                    front_line = lines[i + 2]
                    rear_line = lines[i + 3] if i + 3 < len(lines) else ""
                    data['aero'] = {
                        'front': self._parse_aero_line(front_line),
                        'rear': self._parse_aero_line(rear_line)
                    }
                i += 4
            else:
                i += 1

        return data

    def _parse_range(self, line):
        """Parse range string like 'range: front: 2.50-3.40 hz rear: 2.60-3.50 hz'"""
        result = {}
        parts = line.split('range:')[1].strip()

        if 'front:' in parts and 'rear:' in parts:
            front_part = parts.split('front:')[1].split('rear:')[0].strip()
            rear_part = parts.split('rear:')[1].strip()

            result['front'] = self._extract_range(front_part)
            result['rear'] = self._extract_range(rear_part)

        return result

    def _extract_range(self, text):
        """Extract (min, max) from text like '2.50-3.40 hz' or '85-140mm'"""
        # Remove units and parentheses
        text = text.replace('mm', '').replace('hz', '').replace('°', '').replace(')', '').replace('(', '').strip()
        if '-' in text:
            parts = text.split('-')
            return (float(parts[0]), float(parts[1]))
        return (0, 0)

    def _parse_aero_line(self, line):
        """Parse aero line like 'front) current-xxx (range: min-250 max 350)' or 'front) current 25 (range: min 0 max 100)'"""
        if 'range:' in line:
            range_part = line.split('range:')[1].strip()
            # Handle both "min-250" and "min 250" formats
            if 'min-' in range_part:
                min_val = int(range_part.split('min-')[1].split()[0])
            elif 'min ' in range_part:
                min_val = int(range_part.split('min ')[1].split()[0])
            else:
                min_val = 0

            if 'max' in range_part:
                max_val = int(range_part.split('max')[1].strip().rstrip(')'))
            else:
                max_val = 0

            return {'min': min_val, 'max': max_val, 'current': (min_val + max_val) / 2}
        return {'min': 0, 'max': 0, 'current': 0}

    def _parse_telemetry(self, path):
        """Load telemetry JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Telemetry file '{path}' not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing telemetry JSON: {e}")
            return {}

    def _analyze_suspension(self):
        """Analyze suspension travel patterns from telemetry"""
        # Try to extract suspension data from multiple possible formats
        avg_compression = None

        # Format 1: Direct suspension_travel arrays (sample_telemetry.json format)
        if 'suspension_travel' in self.telemetry and isinstance(self.telemetry['suspension_travel'], dict):
            travel = self.telemetry['suspension_travel']
            if 'FL' in travel and isinstance(travel['FL'], list):
                avg_compression = {
                    'FL': sum(travel.get('FL', [0])) / max(len(travel.get('FL', [1])), 1),
                    'FR': sum(travel.get('FR', [0])) / max(len(travel.get('FR', [1])), 1),
                    'RL': sum(travel.get('RL', [0])) / max(len(travel.get('RL', [1])), 1),
                    'RR': sum(travel.get('RR', [0])) / max(len(travel.get('RR', [1])), 1)
                }

        # Format 2: gt7_2r.py format - individual_laps[0].suspension_behavior.suspension_travel
        if avg_compression is None and 'individual_laps' in self.telemetry:
            laps = self.telemetry['individual_laps']
            if len(laps) > 0 and 'suspension_behavior' in laps[0]:
                susp = laps[0]['suspension_behavior'].get('suspension_travel', {})
                avg_compression = {
                    'FL': susp.get('fl_avg', 0),
                    'FR': susp.get('fr_avg', 0),
                    'RL': susp.get('rl_avg', 0),
                    'RR': susp.get('rr_avg', 0)
                }

        # Format 3: Summary format
        if avg_compression is None and 'suspension_summary' in self.telemetry:
            corners = self.telemetry['suspension_summary'].get('corner_compression_avg', {})
            avg_compression = {
                'FL': corners.get('fl', 0),
                'FR': corners.get('fr', 0),
                'RL': corners.get('rl', 0),
                'RR': corners.get('rr', 0)
            }

        if avg_compression is None or all(v == 0 for v in avg_compression.values()):
            print("  ! No suspension data in telemetry")
            self.results['suspension_analysis'] = "No telemetry data"
            return

        # Calculate averages per axle and per side
        front_avg = (avg_compression['FL'] + avg_compression['FR']) / 2
        rear_avg = (avg_compression['RL'] + avg_compression['RR']) / 2
        left_avg = (avg_compression['FL'] + avg_compression['RL']) / 2
        right_avg = (avg_compression['FR'] + avg_compression['RR']) / 2

        # Per-corner analysis
        max_corner = max(avg_compression.items(), key=lambda x: x[1])
        min_corner = min(avg_compression.items(), key=lambda x: x[1])

        # Get max travel values if available
        max_travel = {}
        if 'individual_laps' in self.telemetry and len(self.telemetry['individual_laps']) > 0:
            susp_travel = self.telemetry['individual_laps'][0].get('suspension_behavior', {}).get('suspension_travel', {})
            max_travel = {
                'FL': susp_travel.get('fl_max', 0),
                'FR': susp_travel.get('fr_max', 0),
                'RL': susp_travel.get('rl_max', 0),
                'RR': susp_travel.get('rr_max', 0)
            }

        # Diagnose front vs rear
        if front_avg > rear_avg + 0.01:
            fr_interp = f"Front softer (+{(front_avg - rear_avg) * 1000:.0f}mm)"
        elif rear_avg > front_avg + 0.01:
            fr_interp = f"Rear softer (+{(rear_avg - front_avg) * 1000:.0f}mm)"
        else:
            fr_interp = "F/R balanced"

        # Diagnose left vs right (lateral balance)
        if left_avg > right_avg + 0.005:
            lr_interp = f"Left softer (+{(left_avg - right_avg) * 1000:.0f}mm)"
        elif right_avg > left_avg + 0.005:
            lr_interp = f"Right softer (+{(right_avg - left_avg) * 1000:.0f}mm)"
        else:
            lr_interp = "L/R balanced"

        # Check for bottoming per corner (>0.28m = moderate, >0.30m = severe)
        bottoming_corners = []
        if max_travel:
            for corner, max_val in max_travel.items():
                if max_val > 0.30:
                    bottoming_corners.append(f"{corner}:{max_val*1000:.0f}mm SEVERE")
                elif max_val > 0.28:
                    bottoming_corners.append(f"{corner}:{max_val*1000:.0f}mm")

        self.results['suspension_analysis'] = {
            'front_compression': front_avg,
            'rear_compression': rear_avg,
            'left_compression': left_avg,
            'right_compression': right_avg,
            'per_corner': avg_compression,
            'max_travel': max_travel,
            'bottoming_corners': bottoming_corners,
            'fr_interpretation': fr_interp,
            'lr_interpretation': lr_interp,
            'softest_corner': max_corner[0],
            'stiffest_corner': min_corner[0]
        }

        print(f"  • Suspension travel:")
        print(f"    F/R: {fr_interp}")
        print(f"    L/R: {lr_interp}")
        if bottoming_corners:
            print(f"    ⚠ Bottoming: {', '.join(bottoming_corners)}")
        print(f"    Softest: {max_corner[0]} ({max_corner[1]*1000:.0f}mm avg)")

    def _analyze_balance(self):
        """Analyze understeer/oversteer balance from telemetry"""
        gradient = None

        # Format 1: Direct balance.understeer_gradient (sample_telemetry.json format)
        if 'balance' in self.telemetry:
            balance_data = self.telemetry.get('balance', {})
            gradient = balance_data.get('understeer_gradient', None)

        # Format 2: gt7_2r.py format - tire_slip_analysis.balance_analysis.balance_metric
        if gradient is None and 'tire_slip_analysis' in self.telemetry:
            slip_balance = self.telemetry['tire_slip_analysis'].get('balance_analysis', {})
            balance_metric = slip_balance.get('balance_metric', None)
            tendency = slip_balance.get('tendency', '')

            # Convert balance_metric to understeer gradient approximation
            # Negative balance_metric means rear slip > front slip = oversteer
            # Positive means understeer
            if balance_metric is not None:
                # Scale from [-0.1, 0.1] to understeer gradient [-2, 6]
                gradient = -balance_metric * 40  # Rough conversion

                print(f"  • Balance: {tendency} (metric: {balance_metric:.3f})")
                self.results['balance'] = tendency
                return

        if gradient is None:
            self.results['balance'] = "Neutral (no telemetry)"
            print("  ! No balance data in telemetry")
            return

        if gradient < 0:
            classification = "Oversteer"
        elif gradient <= 2:
            classification = "Neutral"
        elif gradient <= 4:
            classification = "Moderate Understeer"
        else:
            classification = "Severe Understeer"

        self.results['balance'] = classification
        print(f"  • Balance: {classification} (gradient: {gradient:.2f})")

    def _analyze_tires(self):
        """Analyze tire temperature patterns"""
        temps = None
        diagnosis = []

        # Format 1: Direct tire_temps with I/M/O suffixes (sample_telemetry.json)
        if 'tire_temps' in self.telemetry:
            temps = self.telemetry['tire_temps']
            if temps.get('FL_O', 0) > temps.get('FL_I', 0) + 5:
                diagnosis.append("Hot front-outside → understeer")
            if temps.get('RL_O', 0) > temps.get('RL_I', 0) + 5:
                diagnosis.append("Hot rear-outside → oversteer")

        # Format 2: gt7_2r.py format - individual_laps[0].tire_analysis.temperatures
        elif 'individual_laps' in self.telemetry:
            laps = self.telemetry['individual_laps']
            if len(laps) > 0 and 'tire_analysis' in laps[0]:
                tire_temps = laps[0]['tire_analysis'].get('temperatures', {})
                fl_avg = tire_temps.get('fl_avg', 0)
                fr_avg = tire_temps.get('fr_avg', 0)
                rl_avg = tire_temps.get('rl_avg', 0)
                rr_avg = tire_temps.get('rr_avg', 0)

                front_avg = (fl_avg + fr_avg) / 2
                rear_avg = (rl_avg + rr_avg) / 2

                if rear_avg > front_avg + 3:
                    diagnosis.append(f"Rear tires hotter ({rear_avg:.1f}°C vs {front_avg:.1f}°C)")
                elif front_avg > rear_avg + 3:
                    diagnosis.append(f"Front tires hotter ({front_avg:.1f}°C vs {rear_avg:.1f}°C)")
                else:
                    diagnosis.append(f"Balanced temps (F:{front_avg:.1f}°C R:{rear_avg:.1f}°C)")

        # Format 3: tire_summary
        elif 'tire_summary' in self.telemetry:
            tire_temps = self.telemetry['tire_summary'].get('temperature_averages', {})
            fl = tire_temps.get('fl', 0)
            fr = tire_temps.get('fr', 0)
            rl = tire_temps.get('rl', 0)
            rr = tire_temps.get('rr', 0)

            front_avg = (fl + fr) / 2
            rear_avg = (rl + rr) / 2

            if rear_avg > front_avg + 3:
                diagnosis.append(f"Rear tires hotter ({rear_avg:.1f}°C vs {front_avg:.1f}°C)")
            elif front_avg > rear_avg + 3:
                diagnosis.append(f"Front tires hotter ({front_avg:.1f}°C vs {rear_avg:.1f}°C)")
            else:
                diagnosis.append(f"Balanced temps (F:{front_avg:.1f}°C R:{rear_avg:.1f}°C)")

        if not diagnosis:
            diagnosis = ["No tire data"]

        self.results['tire_diagnosis'] = diagnosis
        print(f"  • Tires: {', '.join(self.results['tire_diagnosis'])}")

    def _cross_validate_phase_a(self):
        """
        Cross-validate suspension + balance + tire temps (YAML Protocol Phase A requirement)
        Synthesizes all three analyses to provide comprehensive diagnosis and recommendations
        """
        if not self.telemetry:
            return

        # Skip if we don't have all three components
        if ('suspension_analysis' not in self.results or
            self.results['suspension_analysis'] == "No telemetry data"):
            return

        # Extract key data points
        susp = self.results.get('suspension_analysis', {})
        balance = self.results.get('balance', 'Unknown')
        tire_diag = self.results.get('tire_diagnosis', [])

        # Build cross-validation insights
        insights = []
        recommendations = []

        # Get numeric values for correlation
        front_comp = susp.get('front_compression', 0)
        rear_comp = susp.get('rear_compression', 0)
        left_comp = susp.get('left_compression', 0)
        right_comp = susp.get('right_compression', 0)

        # CORRELATION 1: Suspension compliance vs Balance vs Tire temps
        # Example: Rear softer + Oversteer + Rear temps higher = consistent diagnosis

        # Check if rear is softer
        rear_softer = rear_comp > front_comp + 0.01
        front_softer = front_comp > rear_comp + 0.01

        # Check balance
        is_oversteer = "Oversteer" in balance
        is_understeer = "Understeer" in balance
        is_neutral = "Neutral" in balance

        # Check tire temps (simplified - looking for "hotter" keywords)
        rear_hotter = any("Rear tires hotter" in d for d in tire_diag)
        front_hotter = any("Front tires hotter" in d for d in tire_diag)
        temps_balanced = any("Balanced temps" in d for d in tire_diag)

        # PATTERN 1: Rear softer + Neutral/Oversteer + Rear temps higher
        if rear_softer and (is_neutral or is_oversteer) and rear_hotter:
            insights.append("⚠ Rear softer + Balance neutral/oversteer + Rear temps higher")
            insights.append("  → Diagnosis: Rear suspension compliant, rear working harder")
            recommendations.append("Consider +0.05-0.10 Hz front to balance load distribution")

        # PATTERN 2: Front softer + Understeer + Front temps higher
        elif front_softer and is_understeer and front_hotter:
            insights.append("⚠ Front softer + Understeer + Front temps higher")
            insights.append("  → Diagnosis: Front suspension compliant, front overworked")
            recommendations.append("Consider +0.05-0.10 Hz rear to shift load rearward")

        # PATTERN 3: Mismatch - rear softer but understeer
        elif rear_softer and is_understeer:
            insights.append("⚠ Rear softer BUT understeer present")
            insights.append("  → Diagnosis: Rear compliance good, but ARB/diff causing push")
            recommendations.append("Check ARB balance (may need softer front ARB)")
            recommendations.append("Check diff accel sensitivity (may be too high)")

        # PATTERN 4: Mismatch - front softer but oversteer
        elif front_softer and is_oversteer:
            insights.append("⚠ Front softer BUT oversteer present")
            insights.append("  → Diagnosis: Front compliance good, but rear ARB/diff causing loose")
            recommendations.append("Check ARB balance (may need softer rear ARB)")
            recommendations.append("Check diff accel sensitivity (may be too low)")

        # PATTERN 5: All aligned (ideal)
        elif (rear_softer and is_neutral and rear_hotter) or (is_neutral and "Balanced temps" in str(tire_diag)):
            insights.append("✓ Suspension + Balance + Temps aligned")
            insights.append("  → Diagnosis: Setup fundamentally sound")

        # CORRELATION 2: Lateral balance (L vs R)
        left_softer = left_comp > right_comp + 0.005
        right_softer = right_comp > left_comp + 0.005

        if left_softer or right_softer:
            side = "left" if left_softer else "right"
            diff_mm = abs(left_comp - right_comp) * 1000
            insights.append(f"⚠ Lateral imbalance: {side} softer by {diff_mm:.0f}mm")
            recommendations.append(f"Check {side} spring rates or track banking effects")

        # CORRELATION 3: Bottoming + high temps + balance issues
        bottoming = susp.get('bottoming_corners', [])
        if bottoming:
            insights.append(f"⚠ Bottoming detected: {', '.join(bottoming)}")

            # Check which corners are bottoming
            rear_bottoming = any('RL' in corner or 'RR' in corner for corner in bottoming)
            front_bottoming = any('FL' in corner or 'FR' in corner for corner in bottoming)
            all_corners = rear_bottoming and front_bottoming

            if all_corners:
                insights.append("  → All corners bottoming = suspension globally too soft")
                recommendations.append("Increase frequency by +0.15-0.30 Hz (already applied via telemetry override)")
            elif rear_hotter and rear_bottoming:
                insights.append("  → Rear bottoming + higher temps = excessive rear compliance")
                recommendations.append("Increase rear frequency by +0.15-0.30 Hz (already applied via telemetry override)")
            elif front_hotter and front_bottoming:
                insights.append("  → Front bottoming + higher temps = excessive front compliance")
                recommendations.append("Increase front frequency by +0.15-0.30 Hz (already applied via telemetry override)")
            elif rear_bottoming:
                insights.append("  → Rear bottoming detected")
                recommendations.append("Rear frequency increased via telemetry override")
            elif front_bottoming:
                insights.append("  → Front bottoming detected")
                recommendations.append("Front frequency increased via telemetry override")

        # Store results
        if insights or recommendations:
            self.results['cross_validation'] = {
                'insights': insights,
                'recommendations': recommendations
            }

            print("\n  ━━━ Cross-Validation (Suspension + Balance + Temps) ━━━")
            for insight in insights:
                print(f"  {insight}")
            if recommendations:
                print(f"\n  📋 Recommendations:")
                for rec in recommendations:
                    print(f"    • {rec}")

    # ═══════════════════════════════════════════════════════════
    # PHASE B: PHYSICS CHAIN
    # ═══════════════════════════════════════════════════════════

    def phase_b_physics_chain(self):
        """Calculate optimal frequencies using ClaudeTunes methodology"""

        # 1. Base frequency from tire compound
        base_freq = self._get_base_frequency()
        print(f"  • Base frequency ({self.car_data['tire_compound']}): {base_freq:.2f} Hz")

        # 1b. TELEMETRY OVERRIDE: Adjust base frequency based on anomalies
        telemetry_adjustment = self._get_telemetry_frequency_override()
        if telemetry_adjustment != 0:
            base_freq += telemetry_adjustment
            reasons = self.results.get('telemetry_override', {}).get('reasons', [])
            reason_str = ", ".join(reasons) if reasons else "telemetry anomalies"
            print(f"  ⚡ Telemetry override: {telemetry_adjustment:+.2f} Hz (adjusted to {base_freq:.2f} Hz)")
            print(f"    Reason: {reason_str}")

        # 2. Apply drivetrain bias
        dt_bias = self._get_drivetrain_bias()
        front_freq = base_freq + dt_bias['front']
        rear_freq = base_freq + dt_bias['rear']
        print(f"  • Drivetrain bias ({self.car_data['drivetrain']}): F+{dt_bias['front']:.2f} R+{dt_bias['rear']:.2f}")

        # 3. Power platform control
        power_add = self._get_power_adder()
        front_freq += power_add
        rear_freq += power_add
        print(f"  • Power platform ({self.car_data['hp']} HP): +{power_add:.2f} Hz")

        # 4. CG height adjustments
        cg_add = self._get_cg_adjustment()
        front_freq += cg_add
        rear_freq += cg_add
        if cg_add != 0:
            print(f"  • CG height adjustment ({self.car_data.get('cg_height', 450):.0f}mm): {cg_add:+.2f} Hz")

        # 5. Aero adders (minimal in GT7)
        aero_add = self._get_aero_adder()
        front_freq += aero_add
        rear_freq += aero_add
        print(f"  • Aero adjustment: +{aero_add:.2f} Hz")

        # 6. Calculate roll center compensation
        self.results['roll_center'] = self._calculate_roll_center()

        # 7. Calculate stability index
        stability = (rear_freq - front_freq) / front_freq

        self.results['physics'] = {
            'front_frequency': front_freq,
            'rear_frequency': rear_freq,
            'stability_index': stability
        }

        print(f"  ✓ Target: F={front_freq:.2f} Hz | R={rear_freq:.2f} Hz | Stability={stability:.2f}")

        # Safety check
        if stability > 0:
            print("  ⚠ WARNING: Positive stability (oversteer tendency)")
        elif stability < -1.0:
            print("  ⚠ WARNING: Extreme understeer (<-1.00)")

    def _get_base_frequency(self):
        """Get base frequency from tire compound"""
        compound_map = {
            'Comfort Hard': 0.75,
            'Comfort Medium': 1.25,
            'Comfort Soft': 1.50,
            'Sport Hard': 1.85,
            'Sports Hard': 1.85,  # GT7 uses "Sports" sometimes
            'Sport Medium': 2.15,
            'Sports Medium': 2.15,
            'Sport Soft': 2.40,
            'Sports Soft': 2.40,
            'Racing Hard': 2.85,
            'Racing Medium': 3.15,
            'Racing Soft': 3.40
        }

        compound = self.car_data.get('tire_compound', 'Racing Hard').strip()

        # Try exact match first
        if compound in compound_map:
            return compound_map[compound]

        # Try normalized match (remove spaces, lowercase)
        compound_normalized = compound.lower().replace(' ', '').replace('tires', '').replace('tire', '').strip()
        for key in compound_map:
            key_normalized = key.lower().replace(' ', '')
            if compound_normalized == key_normalized or key_normalized in compound_normalized:
                return compound_map[key]

        # If still no match, default to Racing Hard
        print(f"  ⚠ Warning: Unknown tire compound '{compound}', defaulting to Racing Hard (2.85 Hz)")
        return 2.85

    def _get_telemetry_frequency_override(self):
        """
        Analyze telemetry anomalies and override base frequency if needed.
        Returns adjustment in Hz (positive = stiffen, negative = soften)
        """
        if not self.telemetry:
            return 0.0

        adjustment = 0.0
        reasons = []

        # ANOMALY 1: Excessive bottoming (suspension too soft)
        if 'individual_laps' in self.telemetry:
            laps = self.telemetry['individual_laps']
            if len(laps) > 0 and 'suspension_behavior' in laps[0]:
                susp_travel = laps[0]['suspension_behavior'].get('suspension_travel', {})
                max_values = [
                    susp_travel.get('fl_max', 0),
                    susp_travel.get('fr_max', 0),
                    susp_travel.get('rl_max', 0),
                    susp_travel.get('rr_max', 0)
                ]

                # Severe bottoming (>0.30m)
                if any(v > 0.30 for v in max_values):
                    adjustment += 0.30
                    reasons.append("severe bottoming")
                # Moderate bottoming (>0.28m)
                elif any(v > 0.28 for v in max_values):
                    adjustment += 0.15
                    reasons.append("moderate bottoming")

        # ANOMALY 2: Excessive slip (suspension too stiff or soft)
        if 'tire_slip_analysis' in self.telemetry:
            slip_analysis = self.telemetry['tire_slip_analysis']

            # Check phase-specific slip
            phase_slip = slip_analysis.get('phase_slip_analysis', {})

            # Braking phase: Front locking excessively (too stiff compression)
            braking = phase_slip.get('braking', {})
            front_brake_slip = braking.get('front_avg_slip', 1.0)
            if front_brake_slip < 0.85:  # >15% slip = locking
                adjustment -= 0.10
                reasons.append("front brake locking")

            # Acceleration phase: Rear wheelspin (too soft or diff issue)
            accel = phase_slip.get('acceleration', {})
            rear_accel_slip = accel.get('rear_avg_slip', 1.0)
            if rear_accel_slip > 1.10:  # >10% slip = wheelspin
                adjustment += 0.10
                reasons.append("rear wheelspin")

        # ANOMALY 3: Extreme tire temperature imbalance (camber/frequency mismatch)
        if 'tire_summary' in self.telemetry:
            tire_temps = self.telemetry['tire_summary'].get('temperature_averages', {})
            fl = tire_temps.get('fl', 0)
            fr = tire_temps.get('fr', 0)
            rl = tire_temps.get('rl', 0)
            rr = tire_temps.get('rr', 0)

            front_avg = (fl + fr) / 2 if (fl and fr) else 0
            rear_avg = (rl + rr) / 2 if (rl and rr) else 0

            # Rear massively hotter (>5°C) = rear working too hard (too soft front?)
            if rear_avg > front_avg + 5:
                adjustment += 0.10
                reasons.append("rear overheating")
            # Front massively hotter (>5°C) = front working too hard (too soft rear?)
            elif front_avg > rear_avg + 5:
                adjustment -= 0.05  # Less aggressive, might be aero
                reasons.append("front overheating")

        # ANOMALY 4: Platform instability (pitch/roll variance)
        if 'individual_laps' in self.telemetry:
            laps = self.telemetry['individual_laps']
            if len(laps) > 0 and 'platform_dynamics' in laps[0]:
                platform = laps[0]['platform_dynamics']

                # High pitch instability (>0.05 CoV) = too soft
                pitch_stability = platform.get('pitch_stability', 0)
                if pitch_stability > 0.05:
                    adjustment += 0.15
                    reasons.append("pitch instability")

                # High roll instability (>0.05 CoV) = ARB too soft (but freq related)
                roll_stability = platform.get('roll_stability', 0)
                if roll_stability > 0.05:
                    adjustment += 0.10
                    reasons.append("roll instability")

        # Log the telemetry-based adjustment
        if adjustment != 0.0 and reasons:
            self.results['telemetry_override'] = {
                'adjustment_hz': adjustment,
                'reasons': reasons
            }

        return round(adjustment, 2)

    def _get_drivetrain_bias(self):
        """Calculate drivetrain-specific frequency bias"""
        dt = self.car_data.get('drivetrain', 'FR')

        bias_map = {
            'FF': {'front': 0.4, 'rear': 0.0},
            'FR': {'front': 0.3, 'rear': 0.0},
            'MR': {'front': 0.0, 'rear': 0.1},
            'RR': {'front': 0.0, 'rear': 0.8},
            'AWD': {'front': 0.2, 'rear': 0.2}  # Simplified
        }

        return bias_map.get(dt, {'front': 0.2, 'rear': 0.0})

    def _get_power_adder(self):
        """Calculate power platform frequency adder using power-to-weight ratio"""
        hp = self.car_data.get('hp', 400)
        weight_lbs = self.car_data.get('weight', 3000)

        # Get base frequency
        base_freq = self._get_base_frequency()

        # Calculate power-to-weight ratio (HP per lb)
        power_to_weight = hp / weight_lbs

        # Reference ratio: 0.154 HP/lb (typical balanced sports car: 400HP / 2600lbs)
        # This is the baseline where no power adjustment is needed
        reference_ratio = 0.154

        # Formula: Base × (sqrt(PWR / reference_ratio) - 1.0)
        # - Cars above reference ratio get positive adjustment (need stiffer springs)
        # - Cars below reference ratio get negative adjustment (can use softer springs)
        # - Square root provides diminishing returns at very high PWR
        pwr_multiplier = math.sqrt(power_to_weight / reference_ratio)
        adder = base_freq * (pwr_multiplier - 1.0)

        # High absolute power brackets for very powerful cars
        # (Even heavy cars with 850+ HP need some extra stiffness)
        if hp > 850:
            adder += 0.2
        elif hp > 700:
            adder += 0.1

        return max(0, adder)

    def _get_cg_adjustment(self):
        """Calculate CG height frequency adjustment per YAML protocol"""
        cg_height = self.car_data.get('cg_height', 450)  # Default to standard

        # YAML protocol thresholds
        if cg_height > 500:
            # High CG: +0.1 to +0.3 Hz (use middle of range)
            return 0.2
        elif cg_height < 400:
            # Very low CG: -0.1 Hz
            return -0.1
        else:
            # Standard CG (400-500mm): 0
            return 0.0

    def _calculate_roll_center(self):
        """Calculate roll center height using YAML protocol formula"""
        cg_height = self.car_data.get('cg_height', 450)
        dt = self.car_data.get('drivetrain', 'FR')
        aero = self.car_data.get('aero', {})
        total_df = aero.get('front', {}).get('current', 0) + aero.get('rear', {}).get('current', 0)

        # Determine DF level multiplier
        if total_df > 1200:
            df_mult = 0.275  # High: 0.25-0.30
        elif total_df > 500:
            df_mult = 0.225  # Moderate: 0.20-0.25
        else:
            df_mult = 0.175  # Low: 0.15-0.20

        # Apply drivetrain-specific adjustments
        dt_mult_map = {
            'FF': 0.225,  # 0.20-0.25
            'FR': 0.225,  # 0.15-0.30 (use middle)
            'MR': 0.20,   # 0.15-0.25
            'RR': 0.25,   # 0.20-0.30
            'AWD': 0.225
        }

        # Use average of DF and drivetrain multipliers
        final_mult = (df_mult + dt_mult_map.get(dt, 0.20)) / 2
        rc_height = final_mult * cg_height

        return {
            'multiplier': final_mult,
            'height': rc_height,
            'cg_height': cg_height
        }

    def _get_aero_adder(self):
        """Calculate aero frequency adder using GT7 Downforce Database"""
        aero = self.car_data.get('aero', {})
        total_df = aero.get('front', {}).get('current', 0) + aero.get('rear', {}).get('current', 0)

        # Classify car using GT7 Downforce Database
        car_class = None
        for class_name, data in self.GT7_DOWNFORCE_DATABASE.items():
            df_min, df_max = data['df_range']
            if df_min <= total_df <= df_max:
                car_class = class_name
                freq_min, freq_max = data['freq_add']
                # Use middle of range for balanced approach
                aero_adder = (freq_min + freq_max) / 2

                # Store classification for reference
                self.results['car_class'] = {
                    'class': class_name,
                    'downforce': total_df,
                    'expected_impact': data['gt7_impact']
                }

                return aero_adder

        # Fallback for unclassified (shouldn't happen with our ranges)
        if total_df > 2000:
            return 0.4
        elif total_df > 1200:
            return 0.25
        elif total_df > 500:
            return 0.15
        else:
            return 0.0

    # ═══════════════════════════════════════════════════════════
    # PHASE C: CONSTRAINT EVALUATION
    # ═══════════════════════════════════════════════════════════

    def phase_c_constraints(self):
        """Evaluate constraints and apply compensation"""
        target_front = self.results['physics']['front_frequency']
        target_rear = self.results['physics']['rear_frequency']

        ranges = self.car_data.get('ranges', {}).get('frequency', {})
        front_range = ranges.get('front', (0, 10))
        rear_range = ranges.get('rear', (0, 10))

        # Check if targets are achievable
        achievable_front = min(max(target_front, front_range[0]), front_range[1])
        achievable_rear = min(max(target_rear, rear_range[0]), rear_range[1])

        # Calculate deficits
        front_deficit = target_front - achievable_front
        rear_deficit = target_rear - achievable_rear

        # Calculate severity
        front_pct = (achievable_front / target_front * 100) if target_front > 0 else 100
        rear_pct = (achievable_rear / target_rear * 100) if target_rear > 0 else 100
        avg_achievable = (front_pct + rear_pct) / 2

        severity = self._classify_severity(avg_achievable)

        self.results['constraints'] = {
            'severity': severity,
            'achievable_front': achievable_front,
            'achievable_rear': achievable_rear,
            'front_deficit': front_deficit,
            'rear_deficit': rear_deficit,
            'achievable_pct': avg_achievable
        }

        print(f"  • Achievable: {avg_achievable:.1f}% | Severity: {severity}")

        if front_deficit > 0.1 or rear_deficit > 0.1:
            print(f"  • Applying ARB/damper compensation...")
            self._apply_compensation()

    def _classify_severity(self, pct):
        """Classify constraint severity level"""
        if pct >= 90:
            return "L1 (Full Optimization)"
        elif pct >= 75:
            return "L2 (Moderate Constraints)"
        elif pct >= 60:
            return "L3 (Significant Constraints)"
        elif pct >= 45:
            return "L4 (Severe Constraints)"
        else:
            return "L5 (Critical Constraints)"

    def _apply_compensation(self):
        """Apply ARB/damper/diff compensation for frequency deficits"""
        front_deficit = self.results['constraints']['front_deficit']
        rear_deficit = self.results['constraints']['rear_deficit']
        total_deficit = max(front_deficit, rear_deficit)

        # ARB compensation: +1 level ≈ 0.15 Hz recovery
        self.results['arb_compensation'] = {
            'front': min(3, int(front_deficit / 0.15)),
            'rear': min(3, int(rear_deficit / 0.15))
        }

        # Damper compensation: +10% compression, +15% rebound
        self.results['damper_compensation'] = {
            'compression_add': 10 if (front_deficit > 0.2 or rear_deficit > 0.2) else 0,
            'expansion_add': 15 if (front_deficit > 0.2 or rear_deficit > 0.2) else 0
        }

        # Differential compensation per YAML: Accel +10-15, Initial +5, Brake +5
        # Recovery: 0.08 Hz per 10-point change
        if total_deficit > 0.3:
            diff_accel_add = min(15, int(total_deficit / 0.08) * 10)
            diff_initial_add = 5 if total_deficit > 0.4 else 0
            diff_brake_add = 5 if total_deficit > 0.4 else 0

            self.results['diff_compensation'] = {
                'accel': diff_accel_add,
                'initial': diff_initial_add,
                'brake': diff_brake_add,
                'recovery_hz': (diff_accel_add / 10) * 0.08
            }
        else:
            self.results['diff_compensation'] = {
                'accel': 0,
                'initial': 0,
                'brake': 0,
                'recovery_hz': 0.0
            }

        print(f"    ARB: +{self.results['arb_compensation']['front']}F / +{self.results['arb_compensation']['rear']}R")
        print(f"    Dampers: +{self.results['damper_compensation']['compression_add']}% comp, +{self.results['damper_compensation']['expansion_add']}% exp")

        if self.results['diff_compensation']['accel'] > 0:
            print(f"    Diff: +{self.results['diff_compensation']['initial']} initial, +{self.results['diff_compensation']['accel']} accel, +{self.results['diff_compensation']['brake']} brake (recovery: {self.results['diff_compensation']['recovery_hz']:.2f} Hz)")

    # ═══════════════════════════════════════════════════════════
    # PHASE D: SETUP SHEET OUTPUT
    # ═══════════════════════════════════════════════════════════

    def phase_d_output(self):
        """Generate GT7-formatted setup sheet"""

        # Calculate all setup parameters
        setup = self._calculate_complete_setup()

        # Check if vehicle has front differential
        has_front_diff = 'front' in setup['diff'] and 'rear' in setup['diff']

        # Build differential section based on vehicle type
        if has_front_diff:
            diff_section = f"""─────────────────────────── Differential Gear ────────────────
Differential            Fully Customized
                                Front         Rear
Initial Torque             Lv.       {setup['diff']['front']['initial']:2d}           {setup['diff']['rear']['initial']:2d}
Acceleration Sensitivity   Lv.       {setup['diff']['front']['accel']:2d}           {setup['diff']['rear']['accel']:2d}
Braking Sensitivity        Lv.       {setup['diff']['front']['brake']:2d}           {setup['diff']['rear']['brake']:2d}
Torque-Vectoring Center Differential         None
Front/Rear Torque Distribution              {setup['torque_split']}"""
        else:
            diff_section = f"""─────────────────────────── Differential Gear ────────────────
Differential            Fully Customized
                                Front         Rear
Initial Torque             Lv.        -           {setup['diff']['initial']:2d}
Acceleration Sensitivity   Lv.        -           {setup['diff']['accel']:2d}
Braking Sensitivity        Lv.        -           {setup['diff']['brake']:2d}
Torque-Vectoring Center Differential         None
Front/Rear Torque Distribution              {setup['torque_split']}"""

        # Format output
        sheet = f"""═══════════════════════════════════════════════════════
   CLAUDETUNES GT7 SETUP SHEET - {self.car_data['name']}
═══════════════════════════════════════════════════════
TRACK: [Track Name]         VERSION: v1.0
DATE: {datetime.now().strftime('%Y-%m-%d')}                BASELINE: ClaudeTunes Auto

─────────────────────────── Tires ────────────────────────────
Front    (33)  {self.car_data.get('tire_compound', 'Racing Hard')}
Rear     (33)  {self.car_data.get('tire_compound', 'Racing Hard')}

─────────────────────────── Suspension ───────────────────────
Suspension              Fully Customized Suspension
                                Front         Rear
Body Height Adjustment      mm      {setup['ride_height']['front']:3d}          {setup['ride_height']['rear']:3d}
Anti-Roll Bar              Lv.       {setup['arb']['front']:2d}           {setup['arb']['rear']:2d}
Damping Ratio (Compression) %        {setup['damping']['compression_front']:2d}           {setup['damping']['compression_rear']:2d}
Damping Ratio (Expansion)   %        {setup['damping']['expansion_front']:2d}           {setup['damping']['expansion_rear']:2d}
Natural Frequency          Hz      {setup['frequency']['front']:4.2f}        {setup['frequency']['rear']:4.2f}
Negative Camber Angle       °       {setup['camber']['front']:3.1f}          {setup['camber']['rear']:3.1f}
Toe Angle                   °     ▼ {abs(setup['toe']['front']):4.2f}      ▲ {setup['toe']['rear']:4.2f}

{diff_section}

─────────────────────────── Aerodynamics ─────────────────────
                                Front         Rear
Downforce                  Lv.      {setup['aero']['front']:3d}          {setup['aero']['rear']:3d}

═══════════════════════════════════════════════════════════════
PHYSICS: {setup['philosophy']} | Stability: {setup['stability']:.2f} | Gain: {setup['expected_gain']}
═══════════════════════════════════════════════════════════════
"""

        return sheet

    def _calculate_complete_setup(self):
        """Calculate all setup parameters following ClaudeTunes protocol"""
        setup = {}

        # Get common parameters used throughout
        dt = self.car_data.get('drivetrain', 'FR')
        hp = self.car_data.get('hp', 400)
        cg_height = self.car_data.get('cg_height', 450)

        # Frequencies (from Phase B, constrained from Phase C)
        setup['frequency'] = {
            'front': self.results['constraints']['achievable_front'],
            'rear': self.results['constraints']['achievable_rear']
        }

        # Ride height - lowest available with positive rake
        # Check for bottoming detection from telemetry (multiple format support)
        bottoming_detected = False

        # Format 1: Direct bottoming_detected flag
        if 'bottoming_detected' in self.telemetry:
            bottoming_detected = self.telemetry.get('bottoming_detected', False)

        # Format 2: gt7_2r.py format - check if max suspension travel > 90%
        if not bottoming_detected and 'individual_laps' in self.telemetry:
            laps = self.telemetry['individual_laps']
            if len(laps) > 0 and 'suspension_behavior' in laps[0]:
                susp_travel = laps[0]['suspension_behavior'].get('suspension_travel', {})
                # Check max travel values (>0.28m indicates bottoming for most GT7 cars)
                max_values = [
                    susp_travel.get('fl_max', 0),
                    susp_travel.get('fr_max', 0),
                    susp_travel.get('rl_max', 0),
                    susp_travel.get('rr_max', 0)
                ]
                if any(v > 0.28 for v in max_values):
                    bottoming_detected = True
        ride_ranges = self.car_data.get('ranges', {}).get('ride_height', {})

        # Calculate ride height offset
        # Priority: bottoming detection > conservative mode > aggressive (minimum)
        if bottoming_detected:
            ride_height_offset = 10
        elif self.conservative_ride_height:
            ride_height_offset = 10
        else:
            ride_height_offset = 0

        setup['ride_height'] = {
            'front': int(ride_ranges.get('front', (85, 140))[0]) + ride_height_offset,  # Minimum + offset
            'rear': int(ride_ranges.get('rear', (110, 165))[0]) + 5 + ride_height_offset  # Minimum + rake + offset
        }

        if bottoming_detected:
            print(f"  ⚠ Bottoming detected in telemetry - ride height raised by {ride_height_offset}mm")
        elif self.conservative_ride_height:
            print(f"  ℹ Conservative ride height mode: +{ride_height_offset}mm buffer from minimum")

        # ARB - base calculation + compensation + track type per YAML
        base_arb_f = int(setup['frequency']['front'] * 2.5)
        base_arb_r = int(setup['frequency']['rear'] * 2.5)

        # Drivetrain adjustments
        dt_arb_adj = {'FF': 1, 'FR': 1, 'MR': 0, 'RR': 1, 'AWD': 0}.get(dt, 0)

        # Track type adjustments
        track_arb_adj = 0
        if self.track_type == 'high_speed':
            track_arb_adj = 1  # +1 both for high-speed
        elif self.track_type == 'technical':
            track_arb_adj = -1  # -1 rear for technical rotation

        arb_comp = self.results.get('arb_compensation', {'front': 0, 'rear': 0})

        setup['arb'] = {
            'front': min(10, max(1, base_arb_f + dt_arb_adj + (track_arb_adj if self.track_type == 'high_speed' else 0) + arb_comp['front'])),
            'rear': min(10, max(1, base_arb_r + (1 if dt == 'RR' else 0) + track_arb_adj + arb_comp['rear']))
        }

        # Damping - OptimumG Physics-Based Calculation (YAML: tuning_subsystems.damping)
        # Philosophy: docs/claudetunes_philosophy.md, docs/damper_tuning_guide.md

        # Step 1: Calculate sprung mass per corner
        weight_lbs = self.car_data.get('weight', 2800)
        weight_kg = weight_lbs * 0.453592
        sprung_mass_total = weight_kg * 0.80  # 80% is sprung mass

        weight_dist = self.car_data.get('weight_distribution', {'front': 55, 'rear': 45})
        front_pct = weight_dist.get('front', 55) / 100
        rear_pct = weight_dist.get('rear', 45) / 100

        sprung_mass_front_corner = (sprung_mass_total * front_pct) / 2  # kg per corner
        sprung_mass_rear_corner = (sprung_mass_total * rear_pct) / 2

        # Step 2: Get target frequencies from Phase B
        freq_front = setup['frequency']['front']  # Hz
        freq_rear = setup['frequency']['rear']

        # Step 3: OptimumG formula - Initial slope = 4π × ζ × ω × m_sm
        import math
        zeta = 0.67  # Damping ratio (0.65-0.70 for racing, use mid-range)

        initial_slope_front = 4 * math.pi * zeta * freq_front * sprung_mass_front_corner  # N/(m/s)
        initial_slope_rear = 4 * math.pi * zeta * freq_rear * sprung_mass_rear_corner

        # Step 4: Energy flow split (compression 2/3, rebound 3/2)
        comp_force_front = (2/3) * initial_slope_front
        comp_force_rear = (2/3) * initial_slope_rear

        rebound_force_front = (3/2) * initial_slope_front
        rebound_force_rear = (3/2) * initial_slope_rear

        # Step 5: Convert physics forces to GT7 percentages
        # Use OptimumG ratio to differentiate F/R, anchor to YAML baselines (25%/35%)

        # Calculate average force to use as baseline anchor
        avg_comp_force = (comp_force_front + comp_force_rear) / 2
        avg_rebound_force = (rebound_force_front + rebound_force_rear) / 2

        # YAML baseline values (from philosophy: 25% comp, 35% rebound)
        baseline_comp = 25
        baseline_rebound = 35

        # Calculate F/R percentages maintaining OptimumG ratio
        comp_pct_front = baseline_comp * (comp_force_front / avg_comp_force)
        comp_pct_rear = baseline_comp * (comp_force_rear / avg_comp_force)

        rebound_pct_front = baseline_rebound * (rebound_force_front / avg_rebound_force)
        rebound_pct_rear = baseline_rebound * (rebound_force_rear / avg_rebound_force)

        # Step 6: Apply modifiers (drivetrain, power, CG, track)
        dt_adj = {'FF': 3, 'FR': 1, 'MR': 0, 'RR': -2, 'AWD': 1}.get(dt, 1)

        if hp > 700:
            power_adj = 8
        elif hp > 600:
            power_adj = 6
        elif hp > 400:
            power_adj = 2
        else:
            power_adj = 0

        if cg_height > 500:
            cg_adj = 2
        elif cg_height < 400:
            cg_adj = -1
        else:
            cg_adj = 0

        track_adj = 0
        if self.track_type == 'high_speed':
            track_adj = 3
        elif self.track_type == 'technical':
            track_adj = -2

        # Step 7: Telemetry reconciliation (if available)
        telem_adj_comp_f = 0
        telem_adj_comp_r = 0
        telem_adj_exp_f = 0
        telem_adj_exp_r = 0

        susp = self.results.get('suspension_analysis', {})
        if susp:
            front_comp = susp.get('front_compression', 0)
            rear_comp = susp.get('rear_compression', 0)

            # Front softer than rear
            if front_comp > rear_comp + 0.02:  # >20mm difference
                telem_adj_comp_f += 5
                print("  📊 Telemetry: Front compressing more → +5% front compression")
            # Rear softer than front
            elif rear_comp > front_comp + 0.02:
                telem_adj_comp_r += 5
                print("  📊 Telemetry: Rear compressing more → +5% rear compression")

            # Temperature-based adjustment
            tire_temps = self.results.get('tire_analysis', {})
            if tire_temps:
                front_avg = tire_temps.get('front_avg', 0)
                rear_avg = tire_temps.get('rear_avg', 0)
                if front_avg > rear_avg + 5:  # Front >5°C hotter
                    telem_adj_comp_f -= 2
                    telem_adj_comp_r += 2
                    print("  📊 Telemetry: Front tires hot → -2% front, +2% rear compression")

        damper_comp = self.results.get('damper_compensation', {'compression_add': 0, 'expansion_add': 0})

        # Final damping values (clamp to GT7 ranges: 20-40% comp, 30-50% rebound)
        setup['damping'] = {
            'compression_front': min(40, max(20, int(comp_pct_front + dt_adj + power_adj + cg_adj + track_adj + telem_adj_comp_f + damper_comp['compression_add']))),
            'compression_rear': min(40, max(20, int(comp_pct_rear + dt_adj + power_adj + cg_adj + track_adj + telem_adj_comp_r + damper_comp['compression_add']))),
            'expansion_front': min(50, max(30, int(rebound_pct_front + dt_adj + power_adj + cg_adj + track_adj + telem_adj_exp_f + damper_comp['expansion_add']))),
            'expansion_rear': min(50, max(30, int(rebound_pct_rear + dt_adj + power_adj + cg_adj + track_adj + telem_adj_exp_r + damper_comp['expansion_add'])))
        }

        # Camber - based on tire compound, track type, and CG per YAML
        tire = self.car_data.get('tire_compound', 'Racing Hard')
        if 'Racing' in tire:
            camber_base_f = -2.0
            camber_base_r = -1.5
            tire_adj = 0.5  # Racing: +0.5°
        elif 'Sport' in tire:
            camber_base_f = -2.0
            camber_base_r = -1.5
            tire_adj = 0.0  # Sport: 0
        else:
            camber_base_f = -2.0
            camber_base_r = -1.5
            tire_adj = -0.3  # Comfort: -0.3°

        # Track type adjustments
        track_camber_adj = 0
        if self.track_type == 'high_speed':
            track_camber_adj = 0.3  # +0.3° for high-speed
        elif self.track_type == 'technical':
            track_camber_adj = -0.2  # -0.2° for technical

        # CG adjustments
        cg_camber_adj = 0
        if cg_height > 500:
            cg_camber_adj = 0.2  # High CG: +0.2°
        elif cg_height < 400:
            cg_camber_adj = -0.1  # Low CG: -0.1°

        setup['camber'] = {
            'front': camber_base_f + tire_adj + track_camber_adj + cg_camber_adj,
            'rear': camber_base_r + tire_adj + track_camber_adj + cg_camber_adj
        }

        # Toe - with track type adjustments per YAML
        if dt == 'FF':
            toe_front = -0.10  # Toe out for FWD
        else:
            toe_front = 0.00

        # Rear toe adjustments for stability and track type
        toe_rear_base = 0.10

        # Track type adjustments
        if self.track_type == 'high_speed':
            toe_rear_base += 0.10  # +0.1° for high-speed stability
        elif self.track_type == 'technical':
            toe_rear_base = 0.00  # 0° for technical (rotation)

        # CG adjustments (high CG needs more stability)
        if cg_height > 500:
            toe_rear_base += 0.05

        setup['toe'] = {
            'front': toe_front,
            'rear': min(1.0, toe_rear_base)  # Cap at 1.0°
        }

        # Differential - base + compensation + track type per YAML
        diff_base = self._calculate_diff_settings()

        # Apply diff compensation from Phase C
        diff_comp = self.results.get('diff_compensation', {'initial': 0, 'accel': 0, 'brake': 0})

        # Track type adjustments per YAML
        track_diff_adj = {'accel': 0, 'brake': 0}
        if self.track_type == 'high_speed':
            track_diff_adj = {'accel': 12, 'brake': -7}  # +10-15 accel, -5-10 brake
        elif self.track_type == 'technical':
            track_diff_adj = {'accel': -7, 'brake': 7}  # -5-10 accel, +5-10 brake

        # Check if vehicle has front differential (AWD/4WD)
        if 'front' in diff_base and 'rear' in diff_base:
            # AWD/4WD vehicle with front and rear diffs
            setup['diff'] = {
                'front': {
                    'initial': min(60, max(5, diff_base['front']['initial'] + diff_comp['initial'])),
                    'accel': min(60, max(5, diff_base['front']['accel'] + diff_comp['accel'] + track_diff_adj['accel'])),
                    'brake': min(60, max(5, diff_base['front']['brake'] + diff_comp['brake'] + track_diff_adj['brake']))
                },
                'rear': {
                    'initial': min(60, max(5, diff_base['rear']['initial'] + diff_comp['initial'])),
                    'accel': min(60, max(5, diff_base['rear']['accel'] + diff_comp['accel'] + track_diff_adj['accel'])),
                    'brake': min(60, max(5, diff_base['rear']['brake'] + diff_comp['brake'] + track_diff_adj['brake']))
                }
            }
        else:
            # RWD/FWD vehicle with rear diff only
            setup['diff'] = {
                'initial': min(60, max(5, diff_base['initial'] + diff_comp['initial'])),
                'accel': min(60, max(5, diff_base['accel'] + diff_comp['accel'] + track_diff_adj['accel'])),
                'brake': min(60, max(5, diff_base['brake'] + diff_comp['brake'] + track_diff_adj['brake']))
            }

        # Torque split
        split = self.car_data.get('torque_split', '0:100')
        setup['torque_split'] = split

        # Aero - balanced around 40% front
        aero = self.car_data.get('aero', {})
        setup['aero'] = {
            'front': int(aero.get('front', {}).get('current', 250)),
            'rear': int(aero.get('rear', {}).get('current', 450))
        }

        # Philosophy and stability
        setup['philosophy'] = f"{dt} {self.car_data.get('hp', 400)}HP Natural Frequency"
        setup['stability'] = self.results['physics']['stability_index']

        # Calculate expected performance gain from Performance Expectations table
        setup['expected_gain'] = self._estimate_performance_gain()

        return setup

    def _estimate_performance_gain(self):
        """Estimate performance gain using Performance Expectations reference table"""
        # Base gain from frequency optimization (always present)
        gain_min = 0.5
        gain_max = 2.0

        # Check for additional gains from specific optimizations
        if self.results.get('telemetry_override'):
            # Telemetry-driven frequency correction
            gain_max += 0.5  # Can add 0.3-2.0s

        if self.results.get('constraints', {}).get('severity', '').startswith('L3'):
            # Significant constraints requiring compensation
            gain_min += 0.2  # ARB/damper/diff recovery adds time

        # Check for bottoming correction
        if self.telemetry:
            if 'individual_laps' in self.telemetry:
                laps = self.telemetry['individual_laps']
                if len(laps) > 0 and 'suspension_behavior' in laps[0]:
                    susp_travel = laps[0]['suspension_behavior'].get('suspension_travel', {})
                    max_values = [
                        susp_travel.get('fl_max', 0),
                        susp_travel.get('fr_max', 0),
                        susp_travel.get('rl_max', 0),
                        susp_travel.get('rr_max', 0)
                    ]
                    if any(v > 0.28 for v in max_values):
                        # Ride height optimization
                        gain_min += 0.3
                        gain_max += 0.8

        # Track type optimization
        if self.track_type != 'balanced':
            gain_min += 0.2
            gain_max += 0.5  # Corner-type differential: 0.2-0.5s

        return f"{gain_min:.1f}-{gain_max:.1f}s"

    def _calculate_diff_settings(self):
        """Calculate LSD settings using YAML Differential Baselines reference table"""
        dt = self.car_data.get('drivetrain', 'FR')
        hp = self.car_data.get('hp', 400)
        has_front_diff = self.car_data.get('has_front_diff', False)

        # Get baseline ranges from reference table (YAML lines 400-419)
        baselines = self.DIFFERENTIAL_BASELINES.get(dt, self.DIFFERENTIAL_BASELINES['FR'])

        # Use middle of range for each setting
        base_initial = sum(baselines['initial']) / 2
        base_accel = sum(baselines['accel']) / 2
        base_brake = sum(baselines['brake']) / 2

        # Power multipliers from YAML protocol (line 233)
        mult_map = {
            'FF': 0.035,
            'FR': 0.03,
            'MR': 0.025,
            'RR': 0.025,
            'AWD': 0.02
        }
        mult = mult_map.get(dt, 0.03)

        # Calculate power-based adjustment using YAML formula (line 232)
        power_add = int((hp - 300) * mult)

        # Rear differential (primary)
        rear_diff = {
            'initial': int(min(60, max(5, base_initial + power_add // 3))),
            'accel': int(min(60, max(5, base_accel + power_add))),
            'brake': int(min(60, max(5, base_brake + power_add // 2)))
        }

        # Front differential (for AWD/4WD vehicles)
        if has_front_diff:
            # Front diff is typically more conservative (lower values)
            # Use AWD baselines for front, scaled by 70-80%
            front_baselines = self.DIFFERENTIAL_BASELINES['AWD']
            front_base_initial = sum(front_baselines['initial']) / 2
            front_base_accel = sum(front_baselines['accel']) / 2
            front_base_brake = sum(front_baselines['brake']) / 2

            # Front gets less power-based adjustment (60% of rear)
            front_power_add = int(power_add * 0.6)

            front_diff = {
                'initial': int(min(60, max(5, front_base_initial + front_power_add // 3))),
                'accel': int(min(60, max(5, front_base_accel + front_power_add))),
                'brake': int(min(60, max(5, front_base_brake + front_power_add // 2)))
            }

            return {
                'front': front_diff,
                'rear': rear_diff
            }
        else:
            # Return rear only for RWD/FWD vehicles
            return rear_diff


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ClaudeTunes - GT7 Physics-Based Suspension Tuning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s car_data.txt telemetry.json
  %(prog)s car_data.txt telemetry.json -o setup_sheet.txt
  %(prog)s car_data.txt telemetry.json -t high_speed
  %(prog)s car_data.txt telemetry.json -t technical -o technical_setup.txt
  %(prog)s car_data.txt telemetry.json --protocol custom_protocol.yaml

Session Management:
  %(prog)s car_data.txt telemetry.json --auto-session
      Creates: ./sessions/session_YYYYMMDD_HHMMSS/Car_Name_setup.txt
  %(prog)s car_data.txt telemetry.json -s spa_weekend
      Creates: ./spa_weekend/Car_Name_setup.txt
  %(prog)s car_data.txt telemetry.json -s spa_weekend -o my_setup.txt
      Creates: ./spa_weekend/my_setup.txt

Track Types:
  high_speed  - Optimizes for high-speed tracks (Monza, Le Mans)
                +3%% damping, +1 ARB, +0.3° camber, +0.1° rear toe
                +12 diff accel, -7 diff brake
  technical   - Optimizes for technical tracks (Monaco, Suzuka)
                -2%% damping, -1 rear ARB, -0.2° camber, 0° rear toe
                -7 diff accel, +7 diff brake
  balanced    - Default balanced setup for mixed tracks

For more information, visit: https://github.com/yourrepo/claudetunes
        """
    )

    parser.add_argument('car_data', help='Path to car data file')
    parser.add_argument('telemetry', help='Path to telemetry JSON file')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-s', '--session', help='Session folder for organized output (optional)')
    parser.add_argument('--auto-session', action='store_true',
                        help='Automatically create session folder with timestamp')
    parser.add_argument('-p', '--protocol', default='ClaudeTunes v8.5.3b.yaml',
                        help='Path to ClaudeTunes protocol YAML file')
    parser.add_argument('-t', '--track-type', choices=['high_speed', 'technical', 'balanced'],
                        default='balanced',
                        help='Track type for setup optimization (default: balanced)')
    parser.add_argument('--conservative-ride-height', action='store_true',
                        help='Add 10mm buffer from minimum ride height to prevent suspension binding')
    parser.add_argument('-v', '--version', action='version', version='ClaudeTunes CLI v8.5.3b')

    args = parser.parse_args()

    # Determine session folder
    session_folder = None
    if args.auto_session:
        # Create timestamped session folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_folder = Path.cwd() / 'sessions' / f"session_{timestamp}"
        session_folder.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Auto-created session folder: {session_folder}")
    elif args.session:
        session_folder = Path(args.session)
        session_folder.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Using session folder: {session_folder}")

    # Initialize and run
    try:
        cli = ClaudeTunesCLI(args.protocol, track_type=args.track_type,
                            conservative_ride_height=args.conservative_ride_height)
        cli.run(args.car_data, args.telemetry, args.output, session_folder=session_folder)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
