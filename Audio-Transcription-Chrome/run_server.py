import argparse
import inspect
import logging
import os
import signal
import sys
 
# ─────────────────────────────────────────────────────────────────────────────
# Colored / categorized logging
# ─────────────────────────────────────────────────────────────────────────────
 
_R    = "\033[0m"
_BOLD = "\033[1m"
 
_C_SERVER = "\033[96m"   # bright cyan   — our startup / config lines
_C_CONN   = "\033[94m"   # bright blue   — client connect / disconnect
_C_AUDIO  = "\033[92m"   # bright green  — audio processing
_C_WARN   = "\033[93m"   # bright yellow — warnings
_C_ERR    = "\033[91m"   # bright red    — real errors
_C_MUTED  = "\033[90m"   # dark grey     — low-priority lib noise
_C_DISCO  = "\033[35m"   # magenta       — expected disconnect "errors"
 
_PFX_SERVER = "🚀 "
_PFX_CONN   = "🔌 "
_PFX_AUDIO  = "🎙  "
_PFX_WARN   = "⚠  "
_PFX_ERR    = "✖  "
_PFX_MUTED  = "·  "
_PFX_DISCO  = "↩  "
 
_DISCONNECT_PHRASES = (
    "1000 (ok)", "1001 (going away)",
    "client disconnected", "received 1000", "sent 1000",
)
 
 
def _is_normal_disconnect(record: logging.LogRecord) -> bool:
    return any(p in record.getMessage().lower() for p in _DISCONNECT_PHRASES)
 
 
def _categorize(record: logging.LogRecord):
    name  = record.name.lower()
    level = record.levelno
 
    if level >= logging.ERROR:
        if _is_normal_disconnect(record):
            return _C_DISCO, _PFX_DISCO
        return _C_ERR, _PFX_ERR
 
    if level >= logging.WARNING:
        return _C_WARN, _PFX_WARN
 
    if name == "__main__":
        return _C_SERVER, _PFX_SERVER
 
    if "faster_whisper" in name:
        return _C_AUDIO, _PFX_AUDIO
 
    if "websockets" in name:
        return _C_MUTED, _PFX_MUTED
 
    msg = record.getMessage().lower()
    conn_keywords = (
        "client connected", "connection closed", "new client",
        "cleaning up", "exiting speech", "connection open",
        "using device", "running faster", "running tensorrt",
        "running openvino", "single model",
    )
    if any(kw in msg for kw in conn_keywords):
        return _C_CONN, _PFX_CONN
 
    return _C_AUDIO, _PFX_AUDIO
 
 
class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color, prefix = _categorize(record)
        bold = _BOLD if record.levelno >= logging.WARNING else ""
 
        record.message = record.getMessage()
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
 
        if record.levelno >= logging.ERROR and _is_normal_disconnect(record):
            label = "INFO    "
        else:
            label = f"{record.levelname:<8}"
 
        line = (
            f"{color}{prefix}{bold}{label}{_R}"
            f"  {color}{record.message}{_R}"
        )
        if record.exc_text:
            line += f"\n{_C_ERR}{record.exc_text}{_R}"
        return line
 
 
def _setup_logging() -> None:
    fmt = ColorFormatter()
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.WARNING)
 
 
_setup_logging()
logger = logging.getLogger(__name__)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Signal handler
# ─────────────────────────────────────────────────────────────────────────────
 
def signal_handler(sig, frame):
    logger.info("Received interrupt signal. Shutting down gracefully…")
    sys.exit(0)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Runtime kwargs filtering
# ─────────────────────────────────────────────────────────────────────────────
 
def filter_kwargs_for(func, kwargs: dict) -> tuple[dict, list[str]]:
    """
    Return (accepted_kwargs, rejected_keys).
    If the function has **kwargs, everything is accepted and rejected_keys = [].
    """
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return kwargs, []
 
    has_var_keyword = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
    if has_var_keyword:
        return kwargs, []
 
    accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
    rejected = [k for k in kwargs if k not in sig.parameters]
    return accepted, rejected
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
 
def main():
    parser = argparse.ArgumentParser(
        description="Start a local WebSocket transcription server (WhisperLive)."
    )
 
    # ── Network ───────────────────────────────────────────────────────────────
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1). "
             "Use 0.0.0.0 for LAN / remote access.",
    )
    parser.add_argument(
        "--port", "-p", type=int, default=9090,
        help="WebSocket port (default: 9090).",
    )
 
    # ── Backend ───────────────────────────────────────────────────────────────
    parser.add_argument(
        "--backend", "-b", type=str, default="faster_whisper",
        choices=["faster_whisper", "tensorrt", "openvino"],
        help="Transcription backend (default: faster_whisper).",
    )
 
    # ── Model paths ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--faster_whisper_custom_model_path", "-fw",
        type=str, default=None,
        help="Path to a custom Faster Whisper / OpenVINO model (optional).",
    )
    parser.add_argument(
        "--trt_model_path", "-trt",
        type=str, default=None,
        help="Path to a Whisper TensorRT model (required when backend=tensorrt).",
    )
    parser.add_argument(
        "--trt_multilingual", "-m", action="store_true",
        help="Enable multilingual support for TensorRT (default: False).",
    )
    parser.add_argument(
        "--trt_py_session", action="store_true",
        help="TensorRT only: use Python session instead of C++ session.",
    )
    parser.add_argument(
        "--cache_path", "-c", type=str, default="~/.cache/whisper-live/",
        help="Directory for cached ctranslate2 models.",
    )
 
    # ── Performance ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--omp_num_threads", "-omp", type=int, default=1,
        help="OpenMP threads for CPU inference (default: 1).",
    )
    parser.add_argument(
        "--no_single_model", "-nsm", action="store_true",
        help="Each client gets its own model instance instead of sharing one.",
    )
 
    # ── Connection limits ─────────────────────────────────────────────────────
    parser.add_argument(
        "--max_clients", type=int, default=100,
        help="Max simultaneous clients (default: 100).",
    )
    parser.add_argument(
        "--max_connection_time", type=int, default=7 * 24 * 60 * 60,
        help="Max connection time per client in seconds (default: 604800 = 7 days).",
    )
 
    # ── REST API ──────────────────────────────────────────────────────────────
    parser.add_argument("--rest_port", type=int, default=8000,
                        help="Port for the optional REST API (default: 8000).")
    parser.add_argument("--enable_rest", action="store_true",
                        help="Enable the OpenAI-compatible REST API endpoint.")
    parser.add_argument("--cors_origins", type=str, default=None,
                        help="Comma-separated CORS origins for the REST API.")
 
    # ── Batch GPU inference ───────────────────────────────────────────────────
    parser.add_argument("--batch_inference", action="store_true",
                        help="Enable batched GPU inference.")
    parser.add_argument("--batch_max_size", type=int, default=8,
                        help="Max batch size (default: 8).")
    parser.add_argument("--batch_window_ms", type=int, default=50,
                        help="Max ms to wait for batch to fill (default: 50).")
 
    args = parser.parse_args()
 
    # ── Validation ────────────────────────────────────────────────────────────
    if args.backend == "tensorrt" and args.trt_model_path is None:
        parser.error(
            "--trt_model_path is required when using the tensorrt backend."
        )
 
    if "OMP_NUM_THREADS" not in os.environ:
        os.environ["OMP_NUM_THREADS"] = str(args.omp_num_threads)
 
    # ── Import ────────────────────────────────────────────────────────────────
    try:
        from whisper_live.server import TranscriptionServer
    except ImportError as exc:
        logger.error("Could not import whisper_live — %s", exc)
        sys.exit(1)
 
    server = TranscriptionServer()
 
    # ── ClientManager ─────────────────────────────────────────────────────────
    # These two params are applied here and do NOT need to go into server.run().
    # We track them so we can exclude them from the "ignored params" warning.
    client_manager_params = set()
    try:
        from whisper_live.server import ClientManager
        server.client_manager = ClientManager(
            args.max_clients, args.max_connection_time
        )
        client_manager_params = {"max_clients", "max_connection_time"}
        logger.info(
            "ClientManager → max_clients=%d  max_connection_time=%d s",
            args.max_clients, args.max_connection_time,
        )
    except (ImportError, TypeError, AttributeError) as exc:
        logger.warning(
            "ClientManager not available (%s); passing limits via run() kwargs.", exc
        )
 
    logger.info(
        "Server ready → host=%s  port=%d  backend=%s",
        args.host, args.port, args.backend,
    )
 
    signal.signal(signal.SIGINT, signal_handler)
 
    # ── Build full kwargs dict ────────────────────────────────────────────────
    all_kwargs = dict(
        host=args.host,
        port=args.port,
        backend=args.backend,
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        whisper_tensorrt_path=args.trt_model_path,
        trt_multilingual=args.trt_multilingual,
        trt_py_session=args.trt_py_session,
        single_model=not args.no_single_model,
        max_clients=args.max_clients,
        max_connection_time=args.max_connection_time,
        cache_path=args.cache_path,
        rest_port=args.rest_port,
        enable_rest=args.enable_rest,
        cors_origins=args.cors_origins,
        batch_enabled=args.batch_inference,
        batch_max_size=args.batch_max_size,
        batch_window_ms=args.batch_window_ms,
    )
    # Strip None values
    all_kwargs = {k: v for k, v in all_kwargs.items() if v is not None}
 
    # ── Inspect server.run() and filter to what it actually accepts ───────────
    accepted_kwargs, rejected_keys = filter_kwargs_for(server.run, all_kwargs)
 
    # Separate rejected keys into two groups:
    #   - already_handled : applied via ClientManager, no action needed
    #   - truly_ignored   : not available at all in this pip version
    already_handled = [k for k in rejected_keys if k in client_manager_params]
    truly_ignored   = [k for k in rejected_keys if k not in client_manager_params]
 
    if truly_ignored:
        logger.warning(
            "The following parameters are not supported by the installed "
            "WhisperLive version and will have no effect: %s.",
            ", ".join(truly_ignored),
        )
 
    server.run(**accepted_kwargs)
 
 
if __name__ == "__main__":
    main()
