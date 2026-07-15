import os


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def allowed_origins() -> list[str]:
    configured = os.getenv("GHOSTGRAPH_ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    # `null` is the Origin sent by Electron when the renderer is loaded from file://.
    return ["null", "http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:8080"]
