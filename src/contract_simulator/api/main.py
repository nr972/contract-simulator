from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contract_simulator.api.routes import contracts, scenarios, simulations


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

    return app


app = create_app()
