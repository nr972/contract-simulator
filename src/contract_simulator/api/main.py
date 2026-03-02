import os
import signal
import sys
import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contract_simulator.api.routes import contracts, scenarios, simulations


def _send_sigterm() -> None:
    """Send SIGTERM to the process group (or just this process on Windows).

    Sleeps briefly so the HTTP response is returned before the process dies.
    """
    time.sleep(0.5)
    if sys.platform == "win32":
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        os.killpg(os.getpgrp(), signal.SIGTERM)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Contract Simulator",
        description="Simulate how contract clauses play out under various scenarios",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
    app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
    app.include_router(simulations.router, prefix="/simulations", tags=["simulations"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    @app.post("/api/v1/shutdown")
    async def shutdown() -> dict[str, str]:
        """Gracefully shut down all services.

        Returns a response, then sends SIGTERM to the process group
        so the startup script's trap can clean up all child processes.
        """
        threading.Thread(target=_send_sigterm, daemon=True).start()
        return {"status": "shutting_down"}

    return app


app = create_app()
