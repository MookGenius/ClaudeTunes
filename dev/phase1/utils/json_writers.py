#!/usr/bin/env python3
"""
JSON Writers for Domain Data
Phase 1: Domain JSON Architecture

Provides atomic, crash-safe JSON writing for domain files.
Supports both full writes and incremental updates.
"""

import json
import os
import tempfile
from typing import Dict, Any
from pathlib import Path


class DomainJSONWriter:
    """Atomic JSON file writer with crash safety"""

    def __init__(self, session_folder: str):
        """
        Initialize writer for a session folder

        Args:
            session_folder: Path to session directory (e.g., /sessions/20251230_173045/)
        """
        self.session_folder = Path(session_folder)
        self.session_folder.mkdir(parents=True, exist_ok=True)

    def write_atomic(self, data: Dict[str, Any], filename: str) -> None:
        """
        Write JSON file atomically (crash-safe)

        Strategy:
        1. Write to temp file in same directory
        2. Rename temp → final (atomic operation on most filesystems)

        Args:
            data: Dictionary to write as JSON
            filename: JSON filename (e.g., 'metadata.json')
        """
        filepath = self.session_folder / filename

        # Write to temp file in same directory (for atomic rename)
        fd, temp_path = tempfile.mkstemp(
            dir=self.session_folder,
            prefix=f'.{filename}.',
            suffix='.tmp'
        )

        try:
            # Write JSON to temp file
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomic rename (replaces existing file if present)
            os.replace(temp_path, filepath)

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e

    def read_or_init(self, filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read existing JSON file or return default if doesn't exist

        Args:
            filename: JSON filename
            default: Default data structure if file doesn't exist

        Returns:
            Existing data or default
        """
        filepath = self.session_folder / filename

        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # File corrupted or unreadable, return default
                return default
        else:
            return default

    def update_incremental(self, new_data: Dict[str, Any], filename: str) -> None:
        """
        Update JSON file incrementally (merge new data with existing)

        Use this for buffered updates where you want to:
        - Append to arrays
        - Update statistics
        - Preserve existing fields

        Args:
            new_data: New data to merge
            filename: JSON filename
        """
        # Read existing data
        existing = self.read_or_init(filename, {})

        # Merge new data (new_data takes precedence)
        merged = self._deep_merge(existing, new_data)

        # Write atomically
        self.write_atomic(merged, filename)

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        Deep merge two dictionaries

        Strategy:
        - If both values are dicts, recurse
        - Otherwise, update value takes precedence

        Args:
            base: Base dictionary
            updates: Updates to apply

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Both are dicts, merge recursively
                result[key] = self._deep_merge(result[key], value)
            else:
                # Overwrite with new value
                result[key] = value

        return result

    def write_all_domains(self, domain_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Write all 6 domain JSONs atomically

        Args:
            domain_data: Dictionary mapping filename → data
                {
                    'metadata.json': {...},
                    'suspension.json': {...},
                    'tires.json': {...},
                    'aero.json': {...},
                    'drivetrain.json': {...},
                    'balance.json': {...}
                }
        """
        for filename, data in domain_data.items():
            self.write_atomic(data, filename)

    def get_session_path(self) -> Path:
        """Get full path to session folder"""
        return self.session_folder


class BufferedDomainWriter:
    """
    Buffered writer that accumulates data and writes every N updates

    Use this for real-time telemetry:
    - Buffer 10 packets
    - Write all 6 domain JSONs
    - Reset buffer
    """

    def __init__(self, session_folder: str, buffer_size: int = 10):
        """
        Initialize buffered writer

        Args:
            session_folder: Path to session directory
            buffer_size: Number of updates to buffer before writing (default: 10)
        """
        self.writer = DomainJSONWriter(session_folder)
        self.buffer_size = buffer_size
        self.update_count = 0

        # Domain buffers (accumulate data from extractors)
        self.domain_buffers = {
            'metadata': None,      # Last metadata (not buffered)
            'suspension': None,    # Last suspension data
            'tires': None,         # Last tire data
            'aero': None,          # Last aero data
            'drivetrain': None,    # Last drivetrain data
            'balance': None        # Last balance data
        }

    def update_domain(self, domain_name: str, data: Dict[str, Any]) -> bool:
        """
        Update a domain buffer with new data

        Args:
            domain_name: Domain name (metadata/suspension/tires/aero/drivetrain/balance)
            data: Extracted domain data

        Returns:
            True if buffer is full and needs flushing, False otherwise
        """
        # Store latest data
        self.domain_buffers[domain_name] = data

        # Increment counter
        self.update_count += 1

        # Check if buffer is full
        return self.update_count >= self.buffer_size

    def flush(self) -> None:
        """
        Write all buffered domain data to JSON files and reset buffers
        """
        if all(v is not None for v in self.domain_buffers.values()):
            # All domains have data, write them
            domain_files = {
                'metadata.json': self.domain_buffers['metadata'],
                'suspension.json': self.domain_buffers['suspension'],
                'tires.json': self.domain_buffers['tires'],
                'aero.json': self.domain_buffers['aero'],
                'drivetrain.json': self.domain_buffers['drivetrain'],
                'balance.json': self.domain_buffers['balance']
            }

            self.writer.write_all_domains(domain_files)

            # Reset counter (keep buffers for stats continuity)
            self.update_count = 0

    def force_write(self) -> None:
        """
        Force write current buffer state (e.g., on session end)
        """
        self.flush()
