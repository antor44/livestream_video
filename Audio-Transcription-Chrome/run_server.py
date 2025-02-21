import argparse
from whisper_live.server import TranscriptionServer, ClientManager, BackendType
from websockets.sync.server import serve
import functools
import json

class MyTranscriptionServer(TranscriptionServer):
    def __init__(self, max_connection_time, max_clients, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_connection_time = max_connection_time
        self.max_clients = max_clients


    def handle_new_connection(self, websocket, faster_whisper_custom_model_path,
                              whisper_tensorrt_path, trt_multilingual):
        try:
            options_str = websocket.recv()
            options = json.loads(options_str)
        except Exception:
            options = {}

        #  Modify options BEFORE ClientManager is initialized
        options['max_connection_time'] = self.max_connection_time
        options['max_clients'] = self.max_clients #Also, set max_clients

        if self.client_manager is None:
            # max_clients is not really used if we have set it in the options dict.
            max_clients = options.get('max_clients', 4) #Get, or default
             # Use modified options dictionary here
            max_connection_time = options['max_connection_time']
            self.client_manager = ClientManager(max_clients, max_connection_time)
        # Remainder of handle_new_connection is mostly the same
        self.use_vad = options.get('use_vad', True)
        if self.client_manager.is_server_full(websocket, options):
            websocket.close()
            return False

        if self.backend.is_tensorrt():
            self.vad_detector = VoiceActivityDetector(frame_rate=self.RATE)
        self.initialize_client(websocket, options, faster_whisper_custom_model_path,
                               whisper_tensorrt_path, trt_multilingual)
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1', help="Host address")
    parser.add_argument('--port', '-p', type=int, default=9090, help="Websocket port")
    parser.add_argument('--backend', '-b', type=str, default='faster_whisper',
                        help='Backends from ["tensorrt", "faster_whisper"]')
    parser.add_argument('--faster_whisper_custom_model_path', '-fw', type=str, default=None,
                        help="Custom Faster Whisper Model")
    parser.add_argument('--trt_model_path', '-trt', type=str, default=None,
                        help='Whisper TensorRT model path')
    parser.add_argument('--trt_multilingual', '-m', action="store_true",
                        help='Boolean only for TensorRT model. True if multilingual.')
    # These are now set by the server, not expected from the client.
    parser.add_argument('--max_connection_time', type=int, default=7*24*60*60,  # 7 days
                        help="Max connection time in seconds")
    parser.add_argument('--max_clients', type=int, default=100, help="Max number of clients")

    args = parser.parse_args()

    if args.backend == "tensorrt" and args.trt_model_path is None:
        raise ValueError("Please Provide a valid tensorrt model path")

    # Create an instance of the subclass, passing in our desired values.
    server = MyTranscriptionServer(args.max_connection_time, args.max_clients)

    recv_audio_partial = functools.partial(
        server.recv_audio,
        backend=BackendType(args.backend),
        faster_whisper_custom_model_path=args.faster_whisper_custom_model_path,
        whisper_tensorrt_path=args.trt_model_path,
        trt_multilingual=args.trt_multilingual
    )

    with serve(recv_audio_partial, args.host, args.port) as websocket_server:
        websocket_server.serve_forever()
