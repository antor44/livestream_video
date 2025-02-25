import argparse
import functools
import logging
import signal
import sys
from websockets.sync.server import serve
from whisper_live.server import TranscriptionServer, BackendType, ClientManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl+C) to gracefully shut down the server.
    """
    logger.info("Received interrupt signal. Shutting down server gracefully...")
    sys.exit(0)

def main():
    """
    Main function to start the transcription server with configurable connection limits.
    """
    parser = argparse.ArgumentParser(description="Start a local WebSocket transcription server.")
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help="Host address to bind the server (default: 127.0.0.1).")
    parser.add_argument('--port', '-p', type=int, default=9090,
                        help="Port number for the WebSocket server (default: 9090).")
    parser.add_argument('--backend', '-b', type=str, default='faster_whisper',
                        choices=['tensorrt', 'faster_whisper'],
                        help="Transcription backend to use (default: faster_whisper).")
    parser.add_argument('--faster_whisper_custom_model_path', '-fw', type=str, default=None,
                        help="Path to a custom Faster Whisper model (optional).")
    parser.add_argument('--trt_model_path', '-trt', type=str, default=None,
                        help="Path to a Whisper TensorRT model (required if backend is tensorrt).")
    parser.add_argument('--trt_multilingual', '-m', action="store_true",
                        help="Enable multilingual support for TensorRT backend (default: False).")
    parser.add_argument('--max_clients', type=int, default=100,
                        help="Maximum number of simultaneous client connections (default: 100).")
    parser.add_argument('--max_connection_time', type=int, default=7*24*60*60,  # 7 days in seconds
                        help="Maximum connection time in seconds allowed per client (default: 7 days).")
    
    args = parser.parse_args()

    if args.backend == "tensorrt" and args.trt_model_path is None:
        raise ValueError("A valid TensorRT model path must be provided when using the tensorrt backend.")

    # Crear el servidor de transcripción
    server = TranscriptionServer()
    
    # Configurar max_clients y max_connection_time según los argumentos proporcionados
    server.client_manager = ClientManager(args.max_clients, args.max_connection_time)
    
    # Log de la configuración
    logger.info(f"Server configured with max_clients={args.max_clients}, max_connection_time={args.max_connection_time} seconds")

    # Preparar la función parcial para el servidor WebSocket
    recv_audio_partial = functools.partial(
        server.recv_audio,
        backend=BackendType(args.backend),
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        whisper_tensorrt_path=args.trt_model_path,
        trt_multilingual=args.trt_multilingual
    )

    # Registrar el manejador de señales para cierre correcto
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar servidor WebSocket
    websocket_server = serve(recv_audio_partial, args.host, args.port)
    logger.info(f"Server started on ws://{args.host}:{args.port}")
    websocket_server.serve_forever()

if __name__ == "__main__":
    main()
