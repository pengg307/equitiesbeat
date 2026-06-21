"""Tests for CSV Loader — TDD verified"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from pathlib import Path
from core.csv_loader import CSVLoader


class TestCSVLoader:
    """Test CSVLoader with mock data."""

    def _write_mock_csv(self, tmp_path, filename, rows):
        """Helper to write a mock CSV file."""
        header = "datetime,open,high,low,close,volume,hold\n"
        filepath = tmp_path / filename
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(header)
            for row in rows:
                f.write(",".join(str(v) for v in row) + "\n")
        return filepath

    def test_find_csv_returns_path(self, tmp_path):
        """T1: find_csv returns correct path when file exists."""
        # Create mock file
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        result = CSVLoader.find_csv(str(tmp_path), "au2506", "15min")
        assert result is not None
        assert "AU_au2606_15min.csv" in result

    def test_find_csv_returns_none_missing(self, tmp_path):
        """T2: find_csv returns None for nonexistent contract."""
        result = CSVLoader.find_csv(str(tmp_path), "nonexistent", "15min")
        assert result is None

    def test_load_ohlcv_returns_correct_structure(self, tmp_path):
        """T3: load_ohlcv returns dict with ohlcv, latest, prevClose, count, file."""
        self._write_mock_csv(
            tmp_path, "AG_ag2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 16800, 16810, 16790, 16805, 5000, 100000],
                ["2026-06-17 09:15:00", 16805, 16820, 16800, 16815, 6000, 101000],
            ]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "ag2506", "15min")
        assert result is not None
        assert "ohlcv" in result
        assert "latest" in result
        assert "prevClose" in result
        assert "count" in result
        assert "file" in result

    def test_load_ohlcv_correct_ohlcv_format(self, tmp_path):
        """T4: Each ohlcv entry has o, h, l, c, v, t keys."""
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [["2026-06-17 09:00:00", 548, 550, 547, 549, 1000, 50000]]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        for bar in result["ohlcv"]:
            assert "o" in bar
            assert "h" in bar
            assert "l" in bar
            assert "c" in bar
            assert "v" in bar
            assert "t" in bar

    def test_load_ohlcv_prev_close_is_second_to_last(self, tmp_path):
        """T5: prevClose = close of second-to-last bar."""
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 100, 101, 99, 100, 100, 5000],
                ["2026-06-17 09:15:00", 100, 102, 99, 101, 200, 5100],
                ["2026-06-17 09:30:00", 101, 103, 100, 102, 300, 5200],
            ]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        assert result["prevClose"] == 101.0  # second-to-last close

    def test_load_ohlcv_latest_price_is_last_close(self, tmp_path):
        """T6: latest.price = close of last bar."""
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 100, 101, 99, 100, 100, 5000],
                ["2026-06-17 09:15:00", 100, 102, 99, 101, 200, 5100],
            ]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        assert result["latest"]["price"] == 101.0

    def test_load_ohlcv_empty_file_returns_none(self, tmp_path):
        """T7: Empty CSV (no data rows) returns None."""
        self._write_mock_csv(tmp_path, "AU_au2606_15min.csv", [])
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        assert result is None

    def test_load_ohlcv_zero_price_rows_skipped(self, tmp_path):
        """T8: Rows with all-zero prices are skipped."""
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:00:00", 0, 0, 0, 0, 0, 0],  # should be skipped
                ["2026-06-17 09:15:00", 100, 102, 99, 101, 200, 5100],
            ]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        assert result is not None
        assert result["count"] == 1  # only 1 valid row

    def test_load_ohlcv_sorts_by_datetime(self, tmp_path):
        """T9: Bars are sorted by datetime ascending."""
        self._write_mock_csv(
            tmp_path, "AU_au2606_15min.csv",
            [
                ["2026-06-17 09:30:00", 102, 103, 101, 102, 300, 5200],
                ["2026-06-17 09:00:00", 100, 101, 99, 100, 100, 5000],
                ["2026-06-17 09:15:00", 101, 102, 100, 101, 200, 5100],
            ]
        )
        result = CSVLoader.load_ohlcv(str(tmp_path), "au2506", "15min")
        assert result["ohlcv"][0]["c"] == 100.0  # earliest first
        assert result["ohlcv"][-1]["c"] == 102.0  # latest last

    def test_contract_map_keys(self):
        """T10: CONTRACT_MAP contains expected keys."""
        assert "ag2506" in CSVLoader.CONTRACT_MAP
        assert "au2506" in CSVLoader.CONTRACT_MAP
        assert CSVLoader.CONTRACT_MAP["ag2506"]["prefix"] == "AG"
        assert CSVLoader.CONTRACT_MAP["au2506"]["prefix"] == "AU"

    def test_find_csv_alt_naming(self, tmp_path):
        """T11: Alternative naming {prefix}_{contract}-{timeframe}.csv also works."""
        # Create alt-named file
        header = "datetime,open,high,low,close,volume,hold\n"
        filepath = tmp_path / "AU_au2606-15min.csv"
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(header)
            f.write("2026-06-17 09:00:00,548,550,547,549,1000,50000\n")
        result = CSVLoader.find_csv(str(tmp_path), "au2506", "15min")
        # Should find either naming variant
        assert result is not None


if __name__ == "__main__":
    import pytest
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--override-ini=addopts="],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    sys.exit(result.returncode)
