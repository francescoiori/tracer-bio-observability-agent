import logging
import asyncio
import re
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from tracer_bio_agent.models import ExecutionLogSchema
from tracer_bio_agent.crud import ExecutionRepository
from tracer_bio_agent.services.base_services import BaseService
from tracer_bio_agent.config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ExecveLoggerService(BaseService):
    """
    Service to process execution logs in real-time and store them in the database.
    """
    pattern = r"(?P<event_type>START|END): Timestamp: (?P<timestamp>[\d-]+\s[\d:]+), PID: (?P<pid>\d+), PPID: (?P<ppid>\d+), UID: (?P<uid>\d+), Command: (?P<command>[^\s,]+)(?:, Args: (?P<args>[^,]+(?:,[^,]+)*))?(?:, Duration: (?P<duration>\d+) ms)?(?:, CPU: (?P<cpu_ticks>\d+) ticks)?"
    LOG_PATTERN = re.compile(pattern)

    def __init__(self, session: AsyncSession):
        """Initialize service with a database session and script path."""
        super().__init__()
        self.session = session
        self.repository = ExecutionRepository(session)
        self.command = f"bash {Config.EBPF_SCRIPT}"

    def parse_log(self, log_line: str) -> Dict[str, str] | None:
        """Parses a log line into an ExecutionLog object."""
        match = self.LOG_PATTERN.match(log_line)
        if not match:
            return None

        log_data = match.groupdict()
        return log_data

    async def process_start_event(self, log_data):
        """Handles the processing of a START event."""
        # Create new execution entry
        execution = ExecutionLogSchema(
            event_type=log_data["event_type"],
            timestamp=datetime.datetime.strptime(log_data["timestamp"], "%Y-%m-%d %H:%M:%S"),
            pid=int(log_data["pid"]),
            ppid=int(log_data["ppid"]),
            uid=int(log_data["uid"]),
            command=log_data["command"],
            args=log_data["args"],
            duration=None,
            cpu_ticks=None,
        )

        logger.info(f"Added START event to database: PID {execution.pid}, Command {execution.command}")

        # Add to the database
        await self.repository.add_execution(execution)

    async def process_end_event(self, log_data):
        """Handles the processing of an END event."""
        execution = ExecutionLogSchema(
            event_type=log_data["event_type"],
            timestamp=datetime.datetime.strptime(log_data["timestamp"], "%Y-%m-%d %H:%M:%S"),
            pid=int(log_data["pid"]),
            ppid=int(log_data["ppid"]),
            uid=int(log_data["uid"]),
            command=log_data["command"],
            args=None,
            duration=int(log_data["duration"] or 0),
            cpu_ticks=int(log_data["cpu_ticks"] or 0),
        )

        logger.info(f"Added END event to database: PID {execution.pid}, Duration {execution.duration} ms")
        # Update the database
        await self.repository.add_execution(execution)

    async def process_log_line(self, log_line: str):
        """Processes a single log line and stores it in the database."""
        log_data = self.parse_log(log_line)
        if not log_data:
            return

        # Handle based on the event type
        if log_data["event_type"] == "START":
            await self.process_start_event(log_data)
        elif log_data["event_type"] == "END":
            await self.process_end_event(log_data)

    async def stream_logs(self):
        """Executes the script and streams logs asynchronously, with shutdown handling."""
        process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            async for line in process.stdout:
                log_line = line.decode().strip()
                if log_line:
                    await self.process_log_line(log_line)

            await process.wait()

        except asyncio.TimeoutError:
            pass  # Continue checking the stop event
        except asyncio.CancelledError:
            logger.info("ExecveLoggerService: Cancelled, stopping...")
        finally:
            process.terminate()
            await process.wait()
            logger.info("ExecveLoggerService: Stopped streaming logs.")

    async def run(self):
        """Starts log processing with shutdown handling."""
        try:
            await self.stream_logs()
        except asyncio.CancelledError:
            logger.info("ExecveLoggerService: Shutting down gracefully.")