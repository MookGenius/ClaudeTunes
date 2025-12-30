# Directory Restructure - Professional Organization

**Date:** 2025-12-30
**Status:** ✅ Complete

---

## What Changed

Reorganized the ClaudeTunes project from a messy root directory into a professional, scalable structure.

## Before → After

```
Before (Messy):
CTPython/
├── claudetunes_cli.py                 ← Production mixed with...
├── gt7_1r.py, gt7_2r.py
├── gt7_2rTEST.py                      ← ...test files
├── claudetunes_cli_v8.5.3b_BACKUP.py  ← ...backups
├── ClaudeTunes v8.5.3b.yaml           ← ...old configs
├── ClaudeTunes v8.5.3c.yaml
├── setup_sheet.txt                    ← ...random outputs
├── YAML_AGENT_DEV/  (23 files!)       ← ...dev work
├── "yaml files/" (spaces in name)
└── "Legacy files/" (spaces in name)

After (Professional):
CTPython/
├── src/                               ← Production code
│   ├── claudetunes_cli.py
│   ├── gt7_1r.py
│   └── gt7_2r.py
│
├── config/                            ← YAML configurations
│   ├── protocol.yaml → v8.5.3c        ← Active config (symlink)
│   ├── ClaudeTunes_v8.5.3c.yaml
│   └── archive/                       ← Old versions
│       ├── ClaudeTunes_v8.5.3b.yaml
│       └── ClaudeTunes_v8.5.3RR.yaml
│
├── dev/                               ← Development work
│   ├── phase0/                        ← Phase 0 refactoring
│   ├── backups/                       ← Version backups
│   └── experimental/                  ← Test versions
│
├── tests/                             ← Test suite
│   └── test_all_features.sh
│
├── legacy/                            ← Old files (organized)
│   └── corvette/
│
├── templates/                         ← Unchanged
├── examples/                          ← Unchanged
├── sessions/                          ← Unchanged
└── docs/                              ← Unchanged
```

---

## Key Improvements

### 1. **Clear Separation of Concerns**
- **Production**: `src/` directory
- **Development**: `dev/` directory
- **Configuration**: `config/` directory
- **Tests**: `tests/` directory

### 2. **No Spaces in Directory Names**
- `yaml files/` → `config/`
- `Legacy files/` → `legacy/`

### 3. **Active Configuration Management**
- `config/protocol.yaml` symlink always points to current version
- Old versions archived in `config/archive/`

### 4. **Organized Development History**
- `dev/phase0/` - Complete Phase 0 work (YAML refactor)
- `dev/backups/` - Version backups
- `dev/experimental/` - Test versions

### 5. **Scalable for Future Phases**
- Easy to add `dev/phase1/`, `dev/phase2/`, etc.
- Clear separation makes git history cleaner

---

## Usage Changes

### Running ClaudeTunes (Production)

**Before:**
```bash
python3 claudetunes_cli.py car_data.txt telemetry.json
```

**After:**
```bash
python3 src/claudetunes_cli.py car_data.txt telemetry.json
# OR
cd src && python3 claudetunes_cli.py ../car_data.txt ../telemetry.json
```

### Using Active Protocol

**Before:**
```bash
# Had to specify exact version
python3 claudetunes_cli.py car_data.txt telemetry.json -p "ClaudeTunes v8.5.3c.yaml"
```

**After:**
```bash
# Use symlink (always current)
python3 src/claudetunes_cli.py car_data.txt telemetry.json -p config/protocol.yaml
```

### Running Tests

**Before:**
```bash
./test_all_features.sh
```

**After:**
```bash
./tests/test_all_features.sh
# OR
cd tests && ./test_all_features.sh
```

---

## Verification

All production code tested and working:

```
✅ ClaudeTunes CLI imports successfully
✅ Protocol loads from config/protocol.yaml
✅ Protocol version: 8.5.3c-phase0-resolved
✅ Downforce DB entries: 6
✅ Differential baselines: 6
✅ All YAML data loading correctly
```

---

## Benefits

1. **Professional Structure**: Follows industry best practices
2. **Easier Navigation**: Find files by purpose (src/dev/config/tests)
3. **Git-Friendly**: Cleaner commits, easier to review changes
4. **Scalable**: Ready for Phase 1, Phase 2, etc.
5. **Cleaner Root**: Only docs and essential files in root
6. **Version Management**: Active symlink + archived versions
7. **Isolated Development**: Dev work doesn't clutter production

---

## Files Moved

| File | From | To |
|------|------|-----|
| `claudetunes_cli.py` | Root | `src/` |
| `gt7_1r.py` | Root | `src/` |
| `gt7_2r.py` | Root | `src/` |
| `gt7_2rTEST.py` | Root | `dev/experimental/` |
| `ClaudeTunes v8.5.3c.yaml` | Root | `config/ClaudeTunes_v8.5.3c.yaml` |
| `ClaudeTunes v8.5.3b.yaml` | Root | `config/archive/` |
| `claudetunes_cli_v8.5.3b_BACKUP.py` | Root | `dev/backups/` |
| `YAML_AGENT_DEV/*` | Root | `dev/phase0/` |
| `test_all_features.sh` | Root | `tests/` |
| `Legacy files/*` | Root | `legacy/corvette/` |
| `setup_sheet.txt` | Root | `sessions/` |

---

## Next Steps

With the directory structure clean and professional:

- ✅ Phase 0: YAML-Driven Refactor (Complete)
- ⏳ **Phase 1: Domain JSON Architecture** (Ready to start)
- ⏳ Phase 2: Subagent Integration
- ⏳ Phase 3: Real-time telemetry enhancements

---

**The codebase is now production-ready and organized for professional development! 🚀**
