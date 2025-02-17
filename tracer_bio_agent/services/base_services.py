import logging
import signal
import asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BaseService:
    """
    Base service class to handle initialization and common methods.
    """
    def __init__(self):
        self.stop_event = asyncio.Event()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handles shutdown signals (Ctrl+C, system termination)"""
        logger.info(f"Received shutdown signal ({signum}), stopping services...")
        self.stop_event.set()  # Set the async event to notify running tasks

    async def run(self):
        """
        Abstract run method to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the run method.")

    async def stop(self):
        """Graceful stop logic, overridden in subclasses if needed"""
        logger.info(f"{self.__class__.__name__} shutting down...")
        self.stop_event.set()
