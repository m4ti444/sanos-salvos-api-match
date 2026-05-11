"""
Sanos y Salvos — Match Service RabbitMQ Publisher
Publishes 'match.found' events when matches are detected.
"""

import json
import logging
import aio_pika
from typing import Optional

from app.config import RABBITMQ_URL

logger = logging.getLogger("match.publisher")

EXCHANGE_NAME = "sanos_y_salvos"
ROUTING_KEY_MATCH_FOUND = "match.found"


class MatchPublisher:
    """Publishes match.found events to RabbitMQ."""

    def __init__(self):
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        try:
            self._connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self._channel = await self._connection.channel()
            await self._channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info("✅ Match publisher connected to RabbitMQ")
        except Exception as e:
            logger.error(f"❌ Failed to connect publisher: {e}")

    async def publish_match_found(self, match_data: dict):
        if not self._channel:
            await self.connect()

        try:
            exchange = await self._channel.get_exchange(EXCHANGE_NAME)
            message = aio_pika.Message(
                body=json.dumps(match_data, default=str).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key=ROUTING_KEY_MATCH_FOUND)
            logger.info(f"📤 Published: {ROUTING_KEY_MATCH_FOUND}")
        except Exception as e:
            logger.error(f"❌ Failed to publish match.found: {e}")

    async def close(self):
        if self._connection:
            await self._connection.close()


publisher = MatchPublisher()
