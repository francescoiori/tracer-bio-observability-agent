import asyncio
import logging
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from tracer_bio_agent.config import Config
from tracer_bio_agent.models import MetricsSchema
from tracer_bio_agent.crud import MetricsRepository
from tracer_bio_agent.services.base_services import BaseService


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetricsService(BaseService):
    """
    Service to collect and store system metrics periodically.
    """
    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session
        self.repository = MetricsRepository(session)
        self.command = f"bash {Config.PS_SCRIPT_PATH}"

    async def stream_process_info(self) -> None:
        """Executes the script and processes output, with shutdown handling."""
        process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        snapshot = []  # Store lines of a single snapshot
        timestamp = None  # Store the timestamp of each snapshot

        try:
            while not self.stop_event.is_set():
                if process.stdout.at_eof():
                    break

                try:
                    line = await asyncio.wait_for(process.stdout.readline(), timeout=1)  # Allow interruption
                except asyncio.TimeoutError:
                    continue  # Check stop_event in the next loop iteration

                if not line:
                    continue

                decoded_line = line.decode().strip()

                # Detect start of a new snapshot and extract timestamp
                if decoded_line.startswith("Snapshot at"):
                    if snapshot:
                        await self.process_and_store_data(snapshot, timestamp)
                        snapshot = []  # Reset for new snapshot

                    timestamp = self.parse_timestamp(decoded_line)

                # Skip column headers, store valid data
                elif not decoded_line.startswith("USER") and decoded_line:
                    snapshot.append(decoded_line)

        except asyncio.CancelledError:
            logger.info("MetricsService: Received cancellation signal, shutting down...")

        finally:
            process.terminate()
            await process.wait()
            logger.info("MetricsService: Stopped streaming process info.")

    async def run(self):
        """Starts log processing."""
        try:
            await self.stream_process_info()
        except asyncio.CancelledError:
            logger.info("MetricsService: Shutting down gracefully.")

    @staticmethod
    def parse_timestamp(snapshot_line: str) -> str:
        """Extract and format timestamp from 'Snapshot at ...' line."""
        try:
            timestamp_str = snapshot_line.replace("Snapshot at ", "").strip()
            timestamp = datetime.datetime.strptime(timestamp_str, "%a %b %d %I:%M:%S %p %Z %Y")
            return timestamp.isoformat()  # Store in ISO format
        except ValueError as e:
            logger.warning(f"Invalid timestamp format: {snapshot_line}, error: {e}")
            return datetime.datetime.now(datetime.UTC).isoformat()  # Fallback to current UTC time

    async def process_and_store_data(self, raw_data: List[str], timestamp: str):
        """ Parse and store each snapshot's data with a timestamp """
        processes = []

        for line in raw_data:
            try:
                parts = line.split()
                if len(parts) < 12:
                    continue  # Ignore malformed lines

                process_data = MetricsSchema(
                    user=parts[0],
                    ppid=int(parts[1]),
                    pid=int(parts[2]),
                    cpu=float(parts[3]),
                    mem=float(parts[4]),
                    vsz=int(parts[5]),
                    rss=int(parts[6]),
                    tty=parts[7] if parts[7] != '?' else None,
                    stat=parts[8],
                    start=parts[9],
                    time=parts[10],
                    command=" ".join(parts[11:]),
                    snapshot_time=datetime.datetime.fromisoformat(timestamp)
                )
                processes.append(process_data)
            except Exception as e:
                logger.warning(f"Parsing error: {e}")

        if processes:
            await self.repository.add_processes(processes)
            logger.info(f"Stored {len(processes)} processes at {timestamp}.")