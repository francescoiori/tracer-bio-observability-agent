import asyncio
import logging
import toml
import pwd
from sqlalchemy.ext.asyncio import AsyncSession
from tracer_bio_agent.models import ProcessedExecutionSchema
from tracer_bio_agent.crud import ExecutionRepository, ProcessedExecutionRepository
from tracer_bio_agent.config import Config
from tracer_bio_agent.services.base_services import BaseService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ExecutionProcessingService(BaseService):
    """
    Service that processes execution events and filters them based on rules defined in a TOML config file.
    """

    def __init__(self, session: AsyncSession):
        """Initialize processing service with database session and repositories."""
        super().__init__()
        self.session = session
        self.exec_repo = ExecutionRepository(session)
        self.proc_exec_repo = ProcessedExecutionRepository(session)

        self.filtered_users = set()
        self.filtered_executables = {}

        self.load_filters()

    def load_filters(self):
        """Load filtering rules from the TOML configuration file."""
        config = toml.load(Config.CONFIG_FILE)
        self.filtered_users = set(config.get("filters", {}).get("users", []))
        self.filtered_executables = config.get("filters", {}).get("executables", {})

    async def process_executions(self):
        """Filter and move execution events based on defined rules using optimized SQL queries."""
        logger.info("Processing execution events...")

        pipeline_pids = await self.exec_repo.get_pipeline_parents(self.filtered_executables)
        pipeline_commands = await self.exec_repo.get_pipeline_commands(pipeline_pids)

        if not pipeline_commands:
            logger.info("No relevant execution events found.")
            return

        async with self.session.begin():  # Start transaction only once
            for pipeline_run, exec_events in pipeline_commands.items():
                for exec_event in exec_events:
                    try:
                        user = pwd.getpwuid(exec_event.uid).pw_name
                    except KeyError:
                        logger.warning(f"Could not find username for UID {exec_event.uid}")
                        continue  # Skip if no username found

                    if user not in self.filtered_users:
                        continue  # Skip execution if user is not in the allowed list

                    # Call check_duplicate **before** inserting into the database
                    is_duplicate = await self.proc_exec_repo.check_duplicate(
                        exec_event.pid, exec_event.timestamp, exec_event.event_type
                    )
                    if is_duplicate:
                        logger.info(
                            f"Skipping duplicate execution event for PID {exec_event.pid} at {exec_event.timestamp}")
                        continue  # Skip duplicate record

                    # Assign a unique run ID for the pipeline execution
                    run_id = hash(pipeline_run)
                    pipeline_name = pipeline_run[0]

                    if exec_event.event_type == 'START':
                        command = exec_event.args.split(',')[0]
                        args = ','.join(exec_event.args.split(',')[1:])
                    else:
                        command = exec_event.command
                        args = exec_event.args

                    # Move valid execution to ProcessedExecution
                    processed_exec = ProcessedExecutionSchema(
                        user=user,
                        event_type=exec_event.event_type,
                        timestamp=exec_event.timestamp,
                        pid=exec_event.pid,
                        ppid=exec_event.ppid,
                        uid=exec_event.uid,
                        command=command,
                        args=args,
                        duration=exec_event.duration,
                        cpu_ticks=exec_event.cpu_ticks,
                        pipeline=pipeline_name,
                        run_id=str(run_id),
                    )

                    # Add to session (transaction is managed at a higher level)
                    await self.proc_exec_repo.add_processed_execution(processed_exec)

    async def cleanup_buffer_tables(self):
        """Delete all records from the executions table after processing."""
        await self.exec_repo.clear_executions()
        logger.info("Cleared buffer table (executions).")

    async def run(self):
        """Main processing loop."""
        try:
            while not self.stop_event.is_set():
                await self.process_executions()
                await asyncio.sleep(Config.PROCESSING_INTERVAL)

        except asyncio.CancelledError:
            logger.info("ExecutionProcessingService: Shutting down gracefully.")