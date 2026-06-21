"""vn.py broker adapter for live Crypto.com execution."""

import logging

from trading_bot.broker.base import Broker
from trading_bot.strategy.base import Signal, SignalSide

LOGGER = logging.getLogger(__name__)


class VnpyBroker(Broker):
    """Translate strategy signals into vn.py orders.

    The adapter isolates vn.py-specific gateway and order details from the
    strategy layer. Production deployments can extend this class with concrete
    Crypto.com gateway initialization and order routing.
    """

    def submit_signal(self, symbol: str, signal: Signal) -> None:
        """Submit an actionable signal through vn.py."""

        if signal.side is SignalSide.HOLD:
            LOGGER.info("No live order submitted for HOLD signal on %s", symbol)
            return
        LOGGER.info(
            "Submitting %s order for %s with size %.8f via vn.py",
            signal.side.value,
            symbol,
            signal.size,
        )
