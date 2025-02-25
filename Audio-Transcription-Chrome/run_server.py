import argparse
import json
import functools
import logging
import signal
import sys
from websockets.sync.server import serve
from whisper_live.server import TranscriptionServer, ClientManager, BackendType
from whisper_live.vad import VoiceActivityDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyTranscriptionServer(TranscriptionServer):
    """
    A custom transcription server extending TranscriptionServer to enforce server-side control
    over maximum client connections and connection duration.

    This subclass overrides the handling of new connections to ensure that `max_clients` and
    `max_connection_time` are set by the server, not reliant on client-provided options.
    It is designed for compatibility with legacy clients.
    """

    def __init__(self, max_connection_time, max_clients, *args, **kwargs):
        """
        Initialize the MyTranscriptionServer with custom connection limits.

        Args:
            max_connection_time (int): Maximum duration in seconds a client can remain connected.
            max_clients (int): Maximum number of simultaneous client connections allowed.
            *args: Variable length argument list passed to the parent class.
            **kwargs: Arbitrary keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.max_connection_time = max_connection_time
        self.max_clients = max_clients

    def handle_new_connection(self, websocket, faster_whisper_custom_model_path,
                              whisper_tensorrt_path, trt_multilingual):
        """
        Handle a new WebSocket connection, enforcing server-defined connection limits.

        Overrides the parent class method to receive client options, enforce server-side
        `max_clients` and `max_connection_time`, and initialize the client manager and client.
        Returns False if the connection cannot proceed (e.g., server is full), True otherwise.

        Args:
            websocket: The WebSocket connection object for the incoming client.
            faster_whisper_custom_model_path (str): Path to a custom Faster Whisper model, if used.
            whisper_tensorrt_path (str): Path to a TensorRT model, if used.
            trt_multilingual (bool): Indicates if the TensorRT model supports multilingual transcription.

        Returns:
            bool: True if the connection is successfully established, False otherwise.
        """
        try:
            options_str = websocket.recv()
            options = json.loads(options_str)
        except Exception:
            options = {}

        # Enforce server-defined connection limits by modifying client options
        options['max_connection_time'] = self.max_connection_time
        options['max_clients'] = self.max_clients

        # Initialize ClientManager if not already created
        if self.client_manager is None:
            max_clients = options.get('max_clients', 4)
            max_connection_time = options['max_connection_time']
            self.client_manager = ClientManager(max_clients, max_connection_time)

        self.use_vad = options.get('use_vad', True)
        if self.client_manager.is_server_full(websocket, options):
            websocket.close()
            return False

        if self.backend.is_tensorrt():
            self.vad_detector = VoiceActivityDetector(frame_rate=self.RATE)
        self.initialize_client(
            websocket,
            options,
            faster_whisper_custom_model_path,
            whisper_tensorrt_path,
            trt_multilingual
        )
        return True

def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl+C) to gracefully shut down the server.

    Args:
        sig: Signal number received (e.g., SIGINT).
        frame: Current stack frame.
    """
    logger.info("Received interrupt signal. Shutting down server gracefully...")
    sys.exit(0)

def main():
    """
    Main function to start the transcription server with command-line configuration.

    Parses command-line arguments to configure the server host, port, backend, model paths,
    and connection limits. Launches a WebSocket server that runs indefinitely until interrupted.
    """
    parser = argparse.ArgumentParser(description="Start a local WebSocket transcription server.")
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help="Host address to bind the server (default: 127.0.0.1 for local loopback)."
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=9090,
        help="Port number for the WebSocket server (default: 9090)."
    )
    parser.add_argument(
        '--backend', '-b',
        type=str,
        default='faster_whisper',
        choices=['tensorrt', 'faster_whisper'],
        help="Transcription backend to use (default: faster_whisper)."
    )
    parser.add_argument(
        '--faster_whisper_custom_model_path', '-fw',
        type=str,
        default=None,
        help="Path to a custom Faster Whisper model (optional)."
    )
    parser.add_argument(
        '--trt_model_path', '-trt',
        type=str,
        default=None,
        help="Path to a Whisper TensorRT model (required if backend is tensorrt)."
    )
    parser.add_argument(
        '--trt_multilingual', '-m',
        action="store_true",
        help="Enable multilingual support for TensorRT backend (default: False)."
    )
    parser.add_argument(
        '--max_connection_time',
        type=int,
        default=7*24*60*60,  # 7 days in seconds
        help="Maximum connection time in seconds allowed per client (default: 7 days)."
    )
    parser.add_argument(
        '--max_clients',
        type=int,
        default=100,
        help="Maximum number of simultaneous client connections (default: 100)."
    )

    args = parser.parse_args()

    if args.backend == "tensorrt" and args.trt_model_path is None:
        raise ValueError("A valid TensorRT model path must be provided when using the tensorrt backend.")

    server = MyTranscriptionServer(args.max_connection_time, args.max_clients)

    # Prepare partial function for WebSocket server
    recv_audio_partial = functools.partial(
        server.recv_audio,
        backend=BackendType(args.backend),
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        whisper_tensorrt_path=args.trt_model_path,
        trt_multilingual=args.trt_multilingual
    )

    # Start the WebSocket server
    websocket_server = serve(recv_audio_partial, args.host, args.port)
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    logger.info(f"Server started on ws://{args.host}:{args.port}")
    websocket_server.serve_forever()

if __name__ == "__main__":
    main()
