"""
Sanos y Salvos — Match Service RabbitMQ Consumer
Listens for 'pet.reported' events and triggers match processing.
"""

import json
import logging
import asyncio
import aio_pika

from app.config import RABBITMQ_URL
from app.services.match_engine import MatchEngine
from app.events.publisher import publisher

logger = logging.getLogger("match.consumer")

EXCHANGE_NAME = "sanos_y_salvos"
QUEUE_NAME = "match_queue"
ROUTING_KEY = "pet.reported"


async def on_message(message: aio_pika.IncomingMessage):
    """Process incoming pet.reported events."""
    async with message.process():
        try:
            report_data = json.loads(message.body.decode())
            logger.info(f"📥 Received event: pet.reported — Report #{report_data.get('report_id')}")

            # Run match engine
            matches = await MatchEngine.process_new_report(report_data)

            # Publish match.found events for each match
            for match in matches:
                await publisher.publish_match_found(match)
                logger.info(f"📤 Published match.found — Score: {match.get('score')}%")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)


async def start_consumer():
    """Start consuming pet.reported events from RabbitMQ."""
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()

        # Declare exchange and queue
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, ROUTING_KEY)

        # Start consuming
        await queue.consume(on_message)
        logger.info(f"✅ Match consumer started — Listening on '{ROUTING_KEY}'")

    except Exception as e:
        logger.error(f"❌ Failed to start consumer: {e}")
        # Retry after delay
        await asyncio.sleep(5)
        await start_consumer()
