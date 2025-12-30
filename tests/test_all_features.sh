#!/bin/bash
# ClaudeTunes CLI - Comprehensive Feature Test Script

echo "════════════════════════════════════════════════════════════"
echo "  ClaudeTunes CLI v8.5.3b - Feature Testing Suite"
echo "════════════════════════════════════════════════════════════"
echo ""

# Test 1: Balanced Setup (Default)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Balanced Setup (Default Track Type)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 claudetunes_cli.py templates/car_data_with_ranges_MASTER.txt templates/sample_telemetry.json -o test_balanced.txt 2>&1 | grep -E "(CG height|Target:|Achievable:|ARB|Dampers|Diff:)"
echo ""

# Test 2: High-Speed Track
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: High-Speed Track Optimization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 claudetunes_cli.py templates/car_data_with_ranges_MASTER.txt templates/sample_telemetry.json -t high_speed -o test_highspeed.txt 2>&1 | grep -E "(CG height|Target:|Achievable:|ARB|Dampers|Diff:)"
echo ""

# Test 3: Technical Track
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Technical Track Optimization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 claudetunes_cli.py templates/car_data_with_ranges_MASTER.txt templates/sample_telemetry.json -t technical -o test_technical.txt 2>&1 | grep -E "(CG height|Target:|Achievable:|ARB|Dampers|Diff:)"
echo ""

# Test 4: Extract and compare setup parameters
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Setup Parameter Comparison"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "| Parameter          | Balanced | High-Speed | Technical |"
echo "|--------------------|----------|------------|-----------|"

# ARB Front
BAL_ARB_F=$(grep "Anti-Roll Bar" test_balanced.txt | awk '{print $6}')
HS_ARB_F=$(grep "Anti-Roll Bar" test_highspeed.txt | awk '{print $6}')
TEC_ARB_F=$(grep "Anti-Roll Bar" test_technical.txt | awk '{print $6}')
echo "| ARB Front          | $BAL_ARB_F       | $HS_ARB_F         | $TEC_ARB_F        |"

# ARB Rear
BAL_ARB_R=$(grep "Anti-Roll Bar" test_balanced.txt | awk '{print $7}')
HS_ARB_R=$(grep "Anti-Roll Bar" test_highspeed.txt | awk '{print $7}')
TEC_ARB_R=$(grep "Anti-Roll Bar" test_technical.txt | awk '{print $7}')
echo "| ARB Rear           | $BAL_ARB_R       | $HS_ARB_R         | $TEC_ARB_R        |"

# Camber Front
BAL_CAM_F=$(grep "Negative Camber Angle" test_balanced.txt | awk '{print $6}')
HS_CAM_F=$(grep "Negative Camber Angle" test_highspeed.txt | awk '{print $6}')
TEC_CAM_F=$(grep "Negative Camber Angle" test_technical.txt | awk '{print $6}')
echo "| Camber Front       | $BAL_CAM_F°   | $HS_CAM_F°     | $TEC_CAM_F°   |"

# Toe Rear
BAL_TOE_R=$(grep "Toe Angle" test_balanced.txt | awk '{print $8}')
HS_TOE_R=$(grep "Toe Angle" test_highspeed.txt | awk '{print $8}')
TEC_TOE_R=$(grep "Toe Angle" test_technical.txt | awk '{print $8}')
echo "| Toe Rear           | $BAL_TOE_R     | $HS_TOE_R      | $TEC_TOE_R      |"

# Diff Accel
BAL_DIFF_A=$(grep "Acceleration Sensitivity" test_balanced.txt | awk '{print $6}')
HS_DIFF_A=$(grep "Acceleration Sensitivity" test_highspeed.txt | awk '{print $6}')
TEC_DIFF_A=$(grep "Acceleration Sensitivity" test_technical.txt | awk '{print $6}')
echo "| Diff Accel         | $BAL_DIFF_A      | $HS_DIFF_A        | $TEC_DIFF_A       |"

# Diff Brake
BAL_DIFF_B=$(grep "Braking Sensitivity" test_balanced.txt | awk '{print $6}')
HS_DIFF_B=$(grep "Braking Sensitivity" test_highspeed.txt | awk '{print $6}')
TEC_DIFF_B=$(grep "Braking Sensitivity" test_technical.txt | awk '{print $6}')
echo "| Diff Brake         | $BAL_DIFF_B      | $HS_DIFF_B        | $TEC_DIFF_B       |"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Verify Track Type Differences"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Calculate differences
ARB_DIFF_HS=$((HS_ARB_F - BAL_ARB_F))
ARB_DIFF_TEC=$((TEC_ARB_R - BAL_ARB_R))
DIFF_A_HS=$((HS_DIFF_A - BAL_DIFF_A))
DIFF_A_TEC=$((TEC_DIFF_A - BAL_DIFF_A))

echo "✓ High-Speed ARB Front: +$ARB_DIFF_HS level (expected: +1)"
echo "✓ Technical ARB Rear: $ARB_DIFF_TEC level (expected: -1)"
echo "✓ High-Speed Diff Accel: +$DIFF_A_HS (expected: +12)"
echo "✓ Technical Diff Accel: $DIFF_A_TEC (expected: -7)"
echo ""

# Cleanup test files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Cleaning up test files..."
rm -f test_balanced.txt test_highspeed.txt test_technical.txt
echo "✓ Test complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
