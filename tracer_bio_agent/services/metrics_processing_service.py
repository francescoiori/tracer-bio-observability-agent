import asyncio
import logging
import toml
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_, or_
from tracer_bio_agent.models import Metrics, ProcessedExecution, ProcessedMetrics
from tracer_bio_agent.crud import MetricsRepository
from tracer_bio_agent.config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetricsProcessingService:
    """
    Service that processes and filters metrics based on monitored executions.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the metrics processing service."""
        self.session = session
        self.metrics_repo = MetricsRepository(session)
        self.filtered_users = set()

        self.load_filters()

    def load_filters(self):
        """Load filtering rules from the TOML configuration file."""
        config = toml.load(Config.CONFIG_FILE)
        self.filtered_users = set(config.get("filters", {}).get("users", []))

    async def process_metrics(self):
        """Filter and move metrics data based on monitored executions."""
        logger.info("Processing metrics...")

        async with self.session.begin():
            # Fetch only metrics for PIDs that exist in `ProcessedExecutions`
            query = (
                select(Metrics, ProcessedExecution.pipeline)
                .join(ProcessedExecution, Metrics.pid == ProcessedExecution.pid or Metrics.ppid == ProcessedExecution.pid)
            )

            result = await self.session.execute(query)
            metrics_records = result.all()

            if not metrics_records:
                logger.info("No matching metrics found for processed executions.")
                return

            logger.info(f"Processing {len(metrics_records)} matched metric records.")

            for metric, pipeline in metrics_records:
                # Move valid metric to ProcessedMetrics
                processed_metric = ProcessedMetrics(
                    user=metric.user,
                    pid=metric.pid,
                    cpu=metric.cpu,
                    mem=metric.mem,
                    vsz=metric.vsz,
                    rss=metric.rss,
                    tty=metric.tty,
                    stat=metric.stat,
                    start=metric.start,
                    time=metric.time,
                    command=metric.command,
                    snapshot_time=metric.snapshot_time,
                    pipeline=pipeline,  # Store the pipeline name
                )
                self.session.add(processed_metric)

            await self.session.commit()

    async def cleanup_buffer_table(self):
        """Delete all records from the metrics buffer table."""
        async with self.session.begin():
            await self.session.execute(delete(Metrics))  # Cleanup buffer table
            await self.session.commit()
        logger.info("Cleared buffer table (metrics).")

    async def run(self):
        """Main processing loop."""
        while True:
            await self.process_metrics()
            # await self.cleanup_buffer_table()
            await asyncio.sleep(Config.PROCESSING_INTERVAL)  # Run processing every minute
