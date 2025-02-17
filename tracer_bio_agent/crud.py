from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_
from typing import List, Dict, Tuple, Sequence
from tracer_bio_agent.models import (Execution, ExecutionLogSchema, Metrics,
                                     MetricsSchema, ProcessedExecution, ProcessedExecutionSchema)


class MetricsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_processes(self, processes: List[MetricsSchema]):
        db_processes = [Metrics(**process.dict()) for process in processes]

        try:
            async with self.session.begin():  # Ensures atomic transaction
                for process in db_processes:
                    self.session.add(process)

        except Exception as e:
            await self.session.rollback()  # Rollback if any issue occurs
            raise e  # Raise error for logging

    async def get_all_processes(self) -> Sequence[Metrics]:
        result = await self.session.execute(select(Metrics))
        return result.scalars().all()



class ExecutionRepository:
    """Handles CRUD operations for Execution table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_execution(self, log: ExecutionLogSchema):
        """Insert a new execution log into the database."""
        execution = Execution(**log.dict())
        self.session.add(execution)
        await self.session.commit()

    async def get_executions(self, pid: int) -> Sequence[Execution]:
        """Retrieve executions by PID."""
        result = await self.session.execute(select(Execution).filter(Execution.pid == pid))
        return result.scalars().all()

    async def get_all_executions(self) -> Sequence[Execution]:
        """Retrieve all execution events."""
        result = await self.session.execute(select(Execution))
        return result.scalars().all()

    async def get_pipeline_parents(self, filtered_executables: Dict[str, str]) -> Dict[str, List[Tuple[int, str]]]:
        """Retrieve pipeline parent executions based on filtered executables."""
        pipeline_pids = {}

        if not filtered_executables:
            return {}

        async with self.session.begin():
            for pipeline_filter in filtered_executables.keys():
                query = (
                    select(Execution.pid, Execution.timestamp)
                    .where(and_(Execution.command == "bash", Execution.args.like(f"%{pipeline_filter}%")))
                )
                result = await self.session.execute(query)
                pipeline_pids[pipeline_filter] = [(row[0], row[1]) for row in result.fetchall()]

        return pipeline_pids

    async def get_pipeline_commands(
            self, pipeline_pids: Dict[str, List[Tuple[int, str]]]
    ) -> Dict[Tuple[str, int, str], Sequence[Execution]]:
        """Retrieve execution events for given pipeline PIDs."""
        commands_by_pipeline = {}

        if not pipeline_pids:
            return {}

        for pipeline_name, run in pipeline_pids.items():
            for (pipeline_pid, timestamp) in run:
                async with self.session.begin():
                    query = select(Execution).where(Execution.ppid == pipeline_pid)
                    result = await self.session.execute(query)
                    commands_by_pipeline[(pipeline_name, pipeline_pid, timestamp)] = result.scalars().all()

        return commands_by_pipeline

    async def clear_executions(self):
        """Delete all execution records after processing."""
        async with self.session.begin():
            await self.session.execute(delete(Execution))
            await self.session.commit()


class ProcessedExecutionRepository:
    """Handles CRUD operations for ProcessedExecution table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_processed_execution(self, execution: ProcessedExecutionSchema):
        """Insert a processed execution into the database."""
        processed_exec = ProcessedExecution(**execution.dict())
        self.session.add(processed_exec)  # No transaction here
        # Do NOT call `self.session.commit()`, let the calling function handle commits.

    async def check_duplicate(self, pid: int, timestamp: str, event_type: str) -> bool:
        """Check if a processed execution already exists."""
        exists_query = select(ProcessedExecution).where(
            (ProcessedExecution.pid == pid) &
            (ProcessedExecution.timestamp == timestamp) &
            (ProcessedExecution.event_type == event_type)
        )
        result = await self.session.execute(exists_query)
        return result.scalars().first() is not None

