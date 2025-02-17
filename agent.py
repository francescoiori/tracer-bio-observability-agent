import os
import logging
import asyncio
from tracer_bio_agent.database import init_db, AsyncSessionLocal
from tracer_bio_agent.services.metrics_service import MetricsService
from tracer_bio_agent.services.ebpf_execve_service import ExecveLoggerService
from tracer_bio_agent.services.execution_processing_service import ExecutionProcessingService
from tracer_bio_agent.services.metrics_processing_service import MetricsProcessingService
from tracer_bio_agent.crud import MetricsRepository, ExecutionRepository

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def main():
    os.remove("tracer_bio.db")

    await init_db()

    async with AsyncSessionLocal() as log_session, \
               AsyncSessionLocal() as metrics_session, \
               AsyncSessionLocal() as exec_processing_session, \
               AsyncSessionLocal() as metrics_processing_session:

        log_service = ExecveLoggerService(log_session)
        metrics_service = MetricsService(metrics_session)
        exec_processing_service = ExecutionProcessingService(exec_processing_session)
        metrics_processing_service = MetricsProcessingService(metrics_processing_session)

        services = [log_service, metrics_service]
        # services = [exec_processing_service, metrics_processing_service]

        try:
            await asyncio.gather(*(service.run() for service in services))
        except asyncio.CancelledError:
            logger.info("Shutting down application...")

        finally:
            for service in services:
                await service.stop()  # Ensure all services stop gracefully

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down...")
