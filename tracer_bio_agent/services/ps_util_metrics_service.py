import asyncio
import logging
import psutil
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
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

    async def run(self):
        """Starts log processing."""
        try:
            await self.stream_process_info()
        except asyncio.CancelledError:
            logger.info("MetricsService: Shutting down gracefully...")

    async def stream_process_info(self) -> None:
        while not self.stop_event.is_set():  # Check for stop signal
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            snapshot = []

            # Iterate over all PIDs to ensure we capture root/system processes
            for pid in psutil.pids():
                try:
                    proc = psutil.Process(pid)
                    proc_info = proc.as_dict(attrs=[
                        'pid', 'ppid', 'cpu_percent', 'memory_info', 'name', 'status', 'create_time'
                    ])

                    print(proc_info['cpu_percent'])

                    process_data = MetricsSchema(
                        user=proc.username() if proc.username() else "unknown",
                        ppid=proc_info['ppid'],
                        pid=proc_info['pid'],
                        cpu=proc_info['cpu_percent'],
                        mem=proc_info['memory_info'].rss / (1024 * 1024),  # Convert RSS to MB
                        vsz=int(proc_info['memory_info'].vms / (1024 * 1024)),  # Virtual memory size in MB
                        rss=int(proc_info['memory_info'].rss / (1024 * 1024)),  # Resident set size in MB
                        tty=None,  # TTY info is unavailable directly in psutil, would need extra handling
                        stat=proc_info['status'],
                        start=datetime.datetime.fromtimestamp(proc_info['create_time']).isoformat(),
                        time="",  # psutil does not provide a direct `time` field
                        command=proc_info['name'],
                        snapshot_time=timestamp
                    )
                    snapshot.append(process_data)

                except (psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue  # Process has terminated, ignore
                except psutil.AccessDenied:
                    logger.warning(f"Access denied for PID {pid}. Skipping...")

            # Store data and log the count of processes captured
            if snapshot:
                await self.repository.add_processes(snapshot)
                logger.info(f"Stored {len(snapshot)} processes at {timestamp}.")

            # Delay the next snapshot, adjust interval as needed
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=Config.MONITORING_INTERVAL)
            except asyncio.TimeoutError:
                continue  # Continue looping if timeout occurs

        logger.info("MetricsService: Stopped streaming process info.")
