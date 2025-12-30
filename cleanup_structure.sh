#!/bin/bash
# ClaudeTunes Directory Restructuring Script
# Transforms messy root directory into professional structure

set -e  # Exit on error

echo "======================================================"
echo "ClaudeTunes Directory Cleanup - Phase 0 to Professional"
echo "======================================================"
echo ""

# Define base directory
BASE_DIR="/Users/mookbookairm1/Desktop/CTPython"
cd "$BASE_DIR"

echo "Step 1: Creating new directory structure..."
mkdir -p src
mkdir -p config/archive
mkdir -p dev/phase0
mkdir -p dev/backups
mkdir -p dev/experimental
mkdir -p tests
mkdir -p legacy/corvette

echo "✅ Directories created"
echo ""

echo "Step 2: Moving production code to src/..."
if [ -f "claudetunes_cli.py" ]; then
    mv claudetunes_cli.py src/
    echo "  ✅ claudetunes_cli.py → src/"
fi

if [ -f "gt7_1r.py" ]; then
    mv gt7_1r.py src/
    echo "  ✅ gt7_1r.py → src/"
fi

if [ -f "gt7_2r.py" ]; then
    mv gt7_2r.py src/
    echo "  ✅ gt7_2r.py → src/"
fi

echo ""

echo "Step 3: Moving YAML configurations to config/..."
if [ -f "ClaudeTunes v8.5.3c.yaml" ]; then
    mv "ClaudeTunes v8.5.3c.yaml" "config/ClaudeTunes_v8.5.3c.yaml"
    echo "  ✅ ClaudeTunes v8.5.3c.yaml → config/ClaudeTunes_v8.5.3c.yaml (removed spaces)"
fi

if [ -f "ClaudeTunes v8.5.3b.yaml" ]; then
    mv "ClaudeTunes v8.5.3b.yaml" "config/archive/ClaudeTunes_v8.5.3b.yaml"
    echo "  ✅ ClaudeTunes v8.5.3b.yaml → config/archive/ (archived)"
fi

# Move old yaml files directory contents
if [ -d "yaml files" ]; then
    if [ -f "yaml files/ClaudeTunes v8.5.3RR.yaml" ]; then
        mv "yaml files/ClaudeTunes v8.5.3RR.yaml" "config/archive/ClaudeTunes_v8.5.3RR.yaml"
        echo "  ✅ ClaudeTunes v8.5.3RR.yaml → config/archive/"
    fi
    rmdir "yaml files" 2>/dev/null || echo "  ⚠️  'yaml files' directory not empty, leaving in place"
fi

echo ""

echo "Step 4: Creating active protocol symlink..."
cd config
ln -sf ClaudeTunes_v8.5.3c.yaml protocol.yaml
echo "  ✅ config/protocol.yaml → ClaudeTunes_v8.5.3c.yaml"
cd "$BASE_DIR"

echo ""

echo "Step 5: Moving Phase 0 development files..."
if [ -d "YAML_AGENT_DEV" ]; then
    mv YAML_AGENT_DEV/* dev/phase0/ 2>/dev/null || true
    rmdir YAML_AGENT_DEV
    echo "  ✅ YAML_AGENT_DEV/ → dev/phase0/"
fi

echo ""

echo "Step 6: Moving backups..."
if [ -f "claudetunes_cli_v8.5.3b_BACKUP.py" ]; then
    mv claudetunes_cli_v8.5.3b_BACKUP.py dev/backups/
    echo "  ✅ claudetunes_cli_v8.5.3b_BACKUP.py → dev/backups/"
fi

echo ""

echo "Step 7: Moving experimental/test files..."
if [ -f "gt7_2rTEST.py" ]; then
    mv gt7_2rTEST.py dev/experimental/
    echo "  ✅ gt7_2rTEST.py → dev/experimental/"
fi

echo ""

echo "Step 8: Moving test suite..."
if [ -f "test_all_features.sh" ]; then
    mv test_all_features.sh tests/
    chmod +x tests/test_all_features.sh
    echo "  ✅ test_all_features.sh → tests/"
fi

echo ""

echo "Step 9: Moving legacy files..."
if [ -d "Legacy files" ]; then
    # Move Corvette files
    if [ -f "Legacy files/Corvette Z06 C5 600hp.txt" ]; then
        mv "Legacy files/Corvette Z06 C5 600hp.txt" legacy/corvette/
        echo "  ✅ Corvette Z06 C5 600hp.txt → legacy/corvette/"
    fi
    if [ -f "Legacy files/corvette_enhanced_output.txt" ]; then
        mv "Legacy files/corvette_enhanced_output.txt" legacy/corvette/
        echo "  ✅ corvette_enhanced_output.txt → legacy/corvette/"
    fi
    if [ -f "Legacy files/Corvette_Nurburgring.json" ]; then
        mv "Legacy files/Corvette_Nurburgring.json" legacy/corvette/
        echo "  ✅ Corvette_Nurburgring.json → legacy/corvette/"
    fi
    if [ -f "Legacy files/corvette_setup.txt" ]; then
        mv "Legacy files/corvette_setup.txt" legacy/corvette/
        echo "  ✅ corvette_setup.txt → legacy/corvette/"
    fi

    # Remove empty Legacy files directory
    rmdir "Legacy files" 2>/dev/null || echo "  ⚠️  'Legacy files' directory not empty, leaving in place"
fi

echo ""

echo "Step 10: Moving random output files to sessions/..."
if [ -f "setup_sheet.txt" ]; then
    mv setup_sheet.txt sessions/
    echo "  ✅ setup_sheet.txt → sessions/"
fi

echo ""

echo "======================================================"
echo "✅ Directory restructuring complete!"
echo "======================================================"
echo ""
echo "New structure:"
echo "  src/          - Production code (3 files)"
echo "  config/       - YAML protocols (active + archive)"
echo "  dev/phase0/   - Phase 0 development work"
echo "  dev/backups/  - Version backups"
echo "  tests/        - Test suite"
echo "  legacy/       - Old files organized by car"
echo "  templates/    - Unchanged"
echo "  examples/     - Unchanged"
echo "  sessions/     - Unchanged"
echo "  docs/         - Unchanged"
echo ""
echo "Active protocol: config/protocol.yaml → ClaudeTunes_v8.5.3c.yaml"
echo ""
