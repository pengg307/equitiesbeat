"""Tests for CSV Watcher — TDD verified"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import tempfile
from pathlib import Path
from core.csv_watcher import CSVWatcher


class TestCSVWatcher:
    """Test CSVWatcher with mock CSV data."""

    def _write_csv(self, tmp_path, filename, rows):
        """Helper to write a mock CSV file with header + data rows."""
        header = "datetime,open,high,low,close,volume,hold\n"
        filepath = tmp_path / filename
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(header)
            for row in rows:
                f.write(",".join(str(v) for v in row) + "\n")
        return filepath

    def test_get_snapshot_counts_rows(self, tmp_path):
        """T1: _get_snapshot returns correct row count."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000],
                ["2026-06-17 09:15:00", 549, 551, 548, 550, 1100, 50100],
                ["2026-06-17 09:30:00", 550, 552, 549, 551, 1200, 50200],
            ]
        )
        csv_file = str(tmp_path / "AU_au2606_15min.csv")
        watcher = CSVWatcher(str(tmp_path))
        snapshot = watcher._get_snapshot(csv_file, "au2506")
        assert snapshot is not None
        assert snapshot["rows"] == 3
        assert snapshot["last_ts"] == "2026-06-17 09:30:00"

    def test_get_snapshot_missing_file(self, tmp_path):
        """T2: _get_snapshot returns None for nonexistent file."""
        watcher = CSVWatcher(str(tmp_path))
        snapshot = watcher._get_snapshot(str(tmp_path / "nonexistent.csv"), "au2506")
        assert snapshot is None

    def test_detect_changes_no_new_rows(self, tmp_path):
        """T3: detect_changes returns empty dict when no new rows."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        # First call populates snapshot
        changes1 = watcher.detect_changes()
        # Second call with no changes
        changes2 = watcher.detect_changes()
        assert len(changes2) == 0  # No new rows since snapshot unchanged

    def test_detect_changes_with_new_rows(self, tmp_path):
        """T4: detect_changes returns new rows when CSV grows."""
        # Initial CSV with 2 rows
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000],
                ["2026-06-17 09:15:00", 549, 551, 548, 550, 1100, 50100],
            ]
        )
        watcher = CSVWatcher(str(tmp_path))
        # First call — initial snapshot
        changes1 = watcher.detect_changes()
        
        # Now append 2 more rows to the CSV
        with open(tmp_path / "AU_au2606_15min.csv", "a", encoding="utf-8-sig") as f:
            f.write("2026-06-17 09:30:00,550,552,549,551,1200,50200\n")
            f.write("2026-06-17 09:45:00,551,553,550,552,1300,50300\n")
        
        # Second call should detect 2 new rows
        changes2 = watcher.detect_changes()
        assert "au2506" in changes2
        assert changes2["au2506"]["new_rows"] == 2

    def test_detect_changes_parses_new_data(self, tmp_path):
        """T5: New rows are correctly parsed into ohlcv format."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        watcher.detect_changes()  # Initial snapshot
        
        # Add 1 row
        with open(tmp_path / "AU_au2606_15min.csv", "a", encoding="utf-8-sig") as f:
            f.write("2026-06-17 09:15:00,549,551,548,550,1100,50100\n")
        
        changes = watcher.detect_changes()
        new_data = changes["au2506"]["new_data"]
        assert len(new_data) == 1
        assert new_data[0]["o"] == 549.0
        assert new_data[0]["h"] == 551.0
        assert new_data[0]["l"] == 548.0
        assert new_data[0]["c"] == 550.0
        assert new_data[0]["v"] == 1100

    def test_watch_loop_runs_once(self, tmp_path):
        """T6: watch_loop runs detection without crashing."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        
        async def _run_once():
            # Run one cycle then stop
            await asyncio.sleep(0.1)
            watcher.stop()
        
        # Start loop in background
        loop = asyncio.new_event_loop()
        loop.create_task(watcher.watch_loop(interval=1))
        loop.create_task(_run_once())
        loop.run_until_complete(asyncio.sleep(0.5))
        loop.close()
        
        # Should not crash
        assert not watcher._running

    def test_stop_causes_loop_exit(self, tmp_path):
        """T7: stop() sets _running to False."""
        watcher = CSVWatcher(str(tmp_path))
        assert watcher._running is False
        watcher._running = True
        watcher.stop()
        assert watcher._running is False

    def test_reset_snapshots_clears_state(self, tmp_path):
        """T8: reset_snapshots clears all tracked snapshots."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        watcher.detect_changes()  # Populate snapshot
        assert len(watcher._snapshots) > 0
        watcher.reset_snapshots()
        assert len(watcher._snapshots) == 0

    def test_detect_changes_multiple_timeframes(self, tmp_path):
        """T9: Watches both 15min and 60min CSVs."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        self._write_csv(
            tmp_path, "AU_au2606_60min.csv",
            [["2026-06-17 10:00:00", 547, 551, 546, 550, 3000, 150000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        # First call initializes snapshots (no changes reported)
        watcher.detect_changes()
        # Second call — no new data, so no changes
        changes = watcher.detect_changes()
        # Snapshot was recorded; verify internal state
        assert "au2506" in watcher._snapshots

    def test_detect_changes_skips_missing_csvs(self, tmp_path):
        """T10: Missing CSV files don't cause errors."""
        # No CSV files created
        watcher = CSVWatcher(str(tmp_path))
        changes = watcher.detect_changes()
        # Should not crash, returns empty
        assert isinstance(changes, dict)

    def test_detect_changes_handles_bad_rows(self, tmp_path):
        """T11: Malformed rows are gracefully skipped."""
        self._write_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        watcher = CSVWatcher(str(tmp_path))
        watcher.detect_changes()  # Initial snapshot
        
        # Append a bad row (missing columns)
        with open(tmp_path / "AU_au2606_15min.csv", "a", encoding="utf-8-sig") as f:
            f.write("2026-06-17 09:15:00,549,551\n")  # Too few columns
        
        # Append a good row
        with open(tmp_path / "AU_au2606_15min.csv", "a", encoding="utf-8-sig") as f:
            f.write("2026-06-17 09:30:00,550,552,549,551,1200,50200\n")
        
        changes = watcher.detect_changes()
        new_data = changes["au2506"]["new_data"]
        # Should only have the good row
        assert len(new_data) == 1
        assert new_data[0]["c"] == 551.0


if __name__ == "__main__":
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--override-ini=addopts="],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    sys.exit(result.returncode)
