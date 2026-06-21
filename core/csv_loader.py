"""CSV Loader for CN Futures local data files.

Loads OHLCV data from CSV files in the data_prod directory and converts them
to the internal ohlcv format expected by the dashboard.

Supported CSV formats:
  - 7-column: datetime,open,high,low,close,volume,hold
  - 8-column: datetime,open,high,low,close,volume,hold,open_interest (with BOM)
"""

import csv
import os
import logging
from datetime import datetime

log = logging.getLogger(__name__)


class CSVLoader:
    """Load CN Futures OHLCV data from local CSV files.

    Contract code mapping:
        ag2506 -> AG/ag2606_{timeframe}.csv
        au2506 -> AU/au2606_{timeframe}.csv
    """

    # contract_code -> {prefix, contract, timeframe}
    CONTRACT_MAP = {
        'ag2506': {'prefix': 'AG', 'contract': 'ag2606'},
        'au2506': {'prefix': 'AU', 'contract': 'au2606'},
    }

    # Timeframe suffix mapping
    TIMEFRAME_MAP = {
        '1min': '1min',
        '5min': '5min',
        '15min': '15min',
        '60min': '60min',
        '1h': '60min',
        '1d': 'daily',
    }

    @classmethod
    def find_csv(cls, csv_dir, contract_code, timeframe='60min'):
        """Find the CSV file path for a given contract + timeframe.

        Returns the absolute path or None if not found.
        """
        mapping = cls.CONTRACT_MAP.get(contract_code)
        if not mapping:
            return None

        prefix = mapping['prefix']
        contract = mapping['contract']
        tf = cls.TIMEFRAME_MAP.get(timeframe, timeframe)

        filename = f"{prefix}_{contract}_{tf}.csv"
        filepath = os.path.join(csv_dir, filename)

        if os.path.isfile(filepath):
            return filepath

        # Try alternative naming: prefix_contract-timeframe.csv
        alt_filename = f"{prefix}_{contract}-{tf}.csv"
        alt_filepath = os.path.join(csv_dir, alt_filename)
        if os.path.isfile(alt_filepath):
            return alt_filepath

        return None

    @classmethod
    def parse_csv(cls, filepath):
        """Parse a CSV file and return raw rows as dicts.

        Handles:
        - UTF-8 BOM
        - 7-column format (no open_interest)
        - 8-column format (with open_interest)
        - Missing/empty values
        """
        rows = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    parsed = cls._parse_row(row)
                    if parsed:
                        rows.append(parsed)
        except FileNotFoundError:
            log.warning("CSV file not found: %s", filepath)
        except Exception as e:
            log.error("Failed to parse CSV %s: %s", filepath, e)

        return rows

    @staticmethod
    def _parse_row(row):
        """Parse a single CSV row into standardized fields.

        Returns dict with keys: datetime, open, high, low, close, volume, hold
        or None if row is invalid.
        """
        try:
            dt_str = row.get('datetime', '').strip()
            if not dt_str:
                return None

            dt = datetime.fromisoformat(dt_str)

            open_p = float(row.get('open', 0) or 0)
            high = float(row.get('high', 0) or 0)
            low = float(row.get('low', 0) or 0)
            close = float(row.get('close', 0) or 0)
            volume = int(float(row.get('volume', 0) or 0))
            hold = float(row.get('hold', 0) or 0)

            # Skip rows with zero price data
            if open_p == 0 and high == 0 and low == 0 and close == 0:
                return None

            return {
                'datetime': dt,
                'open': open_p,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'hold': hold,
            }
        except (ValueError, TypeError, KeyError):
            return None

    @classmethod
    def load_ohlcv(cls, csv_dir, contract_code, timeframe='60min'):
        """Load CSV data and convert to internal ohlcv format.

        Args:
            csv_dir: Path to the directory containing CSV files.
            contract_code: Contract code like 'ag2506' or 'au2506'.
            timeframe: Timeframe like '15min', '60min'.

        Returns:
            {
                'ohlcv': [
                    {'o': float, 'h': float, 'l': float, 'c': float, 'v': int, 't': str},
                    ...
                ],
                'latest': {
                    'price': float, 'open': float, 'high': float, 'low': float,
                    'volume': int, 'openInterest': float
                },
                'prevClose': float,
                'file': str,
                'count': int,
            }
            Returns None if CSV not found or empty.
        """
        filepath = cls.find_csv(csv_dir, contract_code, timeframe)
        if not filepath:
            log.warning(
                "CSV not found for %s [%s] in %s",
                contract_code, timeframe, csv_dir
            )
            return None

        rows = cls.parse_csv(filepath)
        if not rows:
            log.warning("CSV file has no valid data: %s", filepath)
            return None

        # Sort by datetime ascending
        rows.sort(key=lambda r: r['datetime'])

        # Convert to ohlcv format
        ohlcv = []
        for r in rows:
            ohlcv.append({
                'o': round(r['open'], 4),
                'h': round(r['high'], 4),
                'l': round(r['low'], 4),
                'c': round(r['close'], 4),
                'v': r['volume'],
                't': r['datetime'].isoformat(),
            })

        # Latest bar
        last = rows[-1]
        latest = {
            'price': round(last['close'], 4),
            'open': round(last['open'], 4),
            'high': round(last['high'], 4),
            'low': round(last['low'], 4),
            'volume': last['volume'],
            'openInterest': round(last['hold'], 0) if last['hold'] else 0,
        }

        # Previous close = close of second-to-last bar
        prev_close = round(rows[-2]['close'], 4) if len(rows) >= 2 else last['close']

        return {
            'ohlcv': ohlcv,
            'latest': latest,
            'prevClose': prev_close,
            'file': filepath,
            'count': len(ohlcv),
        }
