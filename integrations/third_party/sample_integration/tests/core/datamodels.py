from __future__ import annotations

import dataclasses
import datetime
from typing import Iterable

from TIPCommon.types import SingleJson, JSON

dataclasses.dataclass(slots=True)
class BaseRate:
    date: datetime.date
    symbol: str
    rates: SingleJson

    def to_json(self, symbols: Iterable[str] = None) -> SingleJson:
        result = {
            'date': self.date.isoformat(),
            'symbol': self.symbol,
            'rates': self.rates,
        }
        if symbols:
            result['rates'] = {
                symbol: rate for symbol, rate in self.rates.items()
                if symbol in symbols
            }
        return result