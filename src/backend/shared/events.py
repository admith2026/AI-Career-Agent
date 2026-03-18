"""Event bus abstraction using RabbitMQ (aio-pika)."""

import json
import logging
from typing import Any, Callable, Awaitable

import aio_pika
from aio_pika import ExchangeType

logger = logging.getLogger(__name__)


class EventBus:
    """Async RabbitMQ event bus for publishing and subscribing to domain events."""

    def __init__(self, rabbitmq_url: str):
        self._url = rabbitmq_url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()

    async def publish(self, exchange_name: str, message: dict[str, Any]) -> None:
        if not self._channel:
            await self.connect()
        exchange = await self._channel.declare_exchange(
            exchange_name, ExchangeType.FANOUT, durable=True
        )
        body = json.dumps(message, default=str).encode()
        await exchange.publish(
            aio_pika.Message(body=body, content_type="application/json"),
            routing_key="",
        )

    async def subscribe(
        self,
        exchange_name: str,
        queue_name: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if not self._channel:
            await self.connect()
        exchange = await self._channel.declare_exchange(
            exchange_name, ExchangeType.FANOUT, durable=True
        )
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange)

        async def _on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await handler(data)
                except Exception:
                    logger.exception("Error processing message from %s", exchange_name)

        await queue.consume(_on_message)


# Exchange name constants
class Exchanges:
    JOB_DISCOVERED = "career.job.discovered"
    JOB_ANALYZED = "career.job.analyzed"
    JOB_SCORED = "career.job.scored"
    RESUME_GENERATED = "career.resume.generated"
    APPLICATION_SUBMITTED = "career.application.submitted"
    SEND_NOTIFICATION = "career.notification.send"
    CRAWL_COMPLETED = "career.crawl.completed"
