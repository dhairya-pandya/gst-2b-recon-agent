from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="GST 2B Recon API")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
