# Phase 1 Testing Instructions

**Purpose:** Test that gt7_1r_phase1.py creates domain JSON files correctly

---

## Overview

We've modified `gt7_1r_phase1.py` to write domain JSONs instead of CSV files. This test verifies that:
- 6 domain JSON files are created
- Files have correct structure
- Data is extracted properly
- Buffer flushing works (every 10 packets)

---

## Test Files Created

| File | Purpose |
|------|---------|
| `test_gt7_1r_mock_udp.py` | Mock UDP packet sender (simulates GT7) |
| `verify_domain_jsons.py` | Validates generated JSON files |

---

## Testing Process

### Option A: Full Test (Recommended)

**Requires 2 terminals:**

**Terminal 1 - Start gt7_1r listener:**
```bash
cd /Users/mookbookairm1/Desktop/CTPython/dev/phase1
python3 gt7_1r_phase1.py 127.0.0.1
```

This starts the telemetry logger listening on port 33740.

**Terminal 2 - Send mock packets:**
```bash
cd /Users/mookbookairm1/Desktop/CTPython/dev/phase1
python3 test_gt7_1r_mock_udp.py
```

This sends 15 mock GT7 UDP packets to the listener.

**What to expect:**
- Terminal 1 will show "Domain JSONs updated" every 10 packets
- After 15 packets, you'll see updates at packet 10 and 15
- Press Ctrl+C in Terminal 1 to stop gt7_1r

**Verify the output:**
```bash
python3 verify_domain_jsons.py
```

This checks that all 6 domain JSONs were created correctly.

---

### Option B: Manual Verification

If you already ran the test or have real GT7 data:

```bash
cd /Users/mookbookairm1/Desktop/CTPython/dev/phase1
python3 verify_domain_jsons.py
```

This finds the latest session folder and verifies the JSON files.

---

## Expected Output

### After running test_gt7_1r_mock_udp.py:

```
Sending 15 mock GT7 packets to 127.0.0.1:33740
This will trigger 1 buffer flushes (buffer=10 packets)

Sent packet   1 (lap 1) - 296 bytes
Sent packet   2 (lap 1) - 296 bytes
...
Sent packet  15 (lap 3) - 296 bytes

✅ Sent 15 packets
Expected buffer flushes: 1

Check sessions/ directory for domain JSON files!
```

### After running verify_domain_jsons.py:

```
============================================================
Domain JSON Verification - Phase 1
============================================================

Finding latest session...
Latest session: sessions/20251230_181234

Verifying domain JSON files:

  ✅ metadata.json
     Car: 2013 Ferrari LaFerrari
     Session ID: 20251230_181234
     Speed: 180.0 kph

  ✅ suspension.json
     FL Travel: avg=30.0mm, samples=10

  ✅ tires.json
     FL Temp: avg=85.0°C, samples=10

  ✅ aero.json
     Avg Front Height: 30.0mm
     Downforce: 825 lbs

  ✅ drivetrain.json
     RPM: avg=6000
     Current Gear: 4

  ✅ balance.json
     Lateral G: avg=0.05

============================================================
✅ ALL DOMAIN JSON FILES VERIFIED!
============================================================

Phase 1 Step 1.2 (gt7_1r.py) is working correctly!

Domain JSONs are:
  - Created successfully
  - Properly structured
  - Containing valid data

Ready for Step 1.4 (modify claudetunes_cli.py)!
```

---

## What's Being Tested

### 1. **Domain Extraction** ✅
- All 6 extractors parse UDP packets correctly
- Data is organized by domain

### 2. **Statistical Buffering** ✅
- Rolling stats (min/max/avg) calculated
- Last 10 samples preserved
- Event counters working (bottoming, slip, etc.)

### 3. **JSON Writing** ✅
- Atomic writes (crash-safe)
- Buffered updates (every 10 packets)
- All 6 files created

### 4. **Data Accuracy** ✅
- Car name extracted correctly
- Speed/RPM/gear displayed correctly
- Suspension/tire/aero data present

---

## Session Folder Structure

After successful test:

```
sessions/20251230_181234/
├── metadata.json (session info, car, lap times)
├── suspension.json (travel stats + samples)
├── tires.json (temps, slip + samples)
├── aero.json (ride height, downforce)
├── drivetrain.json (RPM, gearing + samples)
├── balance.json (g-forces + samples)
└── session_summary.txt (text summary)
```

Each JSON file contains:
- Current values
- Rolling statistics (min/max/avg)
- Last 10 samples for pattern recognition
- Domain-specific fields

---

## Troubleshooting

### "sessions/ directory not found"
- The mock sender didn't run yet, or gt7_1r wasn't started
- Run gt7_1r_phase1.py first, then send packets

### "No session folders found"
- gt7_1r never received packets
- Check that both scripts use port 33740
- Verify gt7_1r is running before sending packets

### "Invalid JSON"
- Possible crash during write
- Try running test again
- Check that BufferedDomainWriter flushes properly

### "Missing keys in JSON"
- Extractor may have failed
- Check extractor initialization
- Verify UDP packet format is correct

---

## Next Steps

Once verification passes:

**✅ Step 1.2 Complete:** gt7_1r.py writes domain JSONs
**⏳ Step 1.4:** Modify claudetunes_cli.py to read domain JSONs

---

## Notes

- Mock packets simulate GT7 PlayStation telemetry
- Packets are Salsa20 encrypted (same as real GT7)
- 15 packets = 1.5 buffer flushes (buffer=10)
- Real GT7 sends 60 packets/second
- Test uses LaFerrari (car_code=3462)

---

**Test files ready! Run the tests to verify gt7_1r_phase1.py works correctly.** 🚀
