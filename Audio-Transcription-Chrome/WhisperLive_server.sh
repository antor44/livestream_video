#!/bin/bash
# =============================================================================
# WhisperLive server launcher
#
# Usage:
#   ./WhisperLive_server.sh [mode] [backend] [options]
#
# Modes:
#   (none)              Local faster-whisper, no Docker
#   docker              Docker — auto-detect hardware
#   docker cpu          Docker — force CPU
#   docker cuda         Docker — force NVIDIA CUDA
#   docker openvino     Docker — force Intel OpenVINO
#   docker trt          Docker TensorRT (Collabora image)
#
# Options:
#   --model <name>      Whisper model: tiny/base/small/medium/large-v2/large-v3
#   --port <number>     WebSocket port (default: 9090)
#   --host <ip>         Host/IP to bind (default: 127.0.0.1)
#                       Use 0.0.0.0 to expose to LAN/internet
#   --multilingual      Enable multilingual mode for TensorRT (required for
#                       non-English languages with the TensorRT backend)
#   --help              Show this help message
#
# Examples:
#   ./WhisperLive_server.sh
#   ./WhisperLive_server.sh docker
#   ./WhisperLive_server.sh docker cuda --model large-v3
#   ./WhisperLive_server.sh docker cuda --model large-v3 --host 0.0.0.0
#   ./WhisperLive_server.sh docker cuda --model large-v3 --port 9091
#   ./WhisperLive_server.sh docker trt  --model large-v2 --multilingual
#
# Notes on language support:
#   - faster-whisper (local and Docker cpu/cuda): multilingual by default.
#     Set the language in the Chrome extension (or leave on Auto Detect).
#   - TensorRT: requires --multilingual flag for non-English languages.
#     Without it the engine defaults to English-only transcription.
#
# Notes on host/binding:
#   - In local mode, --host controls where the Python server listens.
#   - In Docker mode, --host controls the Docker -p binding on the host side.
#     Inside the container the process always listens on 0.0.0.0 (required).
#   - Default 127.0.0.1 means only the local machine can connect.
#   - Use 0.0.0.0 or a specific LAN IP to allow remote clients.
#
# Environment variables:
#   NO_EMOJI=1          Force plain ASCII labels instead of emoji
# =============================================================================

# ---------------------------------------------------------------------------
# Emoji / ASCII detection
# Set NO_EMOJI=1 to force ASCII labels (useful for xterm or piped output).
# ---------------------------------------------------------------------------
_use_emoji() {
    [ "${NO_EMOJI:-0}" = "1" ] && return 1
    case "${LANG:-}${LC_ALL:-}" in
        *UTF-8*|*utf8*) return 0 ;;
    esac
    local enc
    enc=$(locale 2>/dev/null | grep -i "utf-8\|utf8" | head -1)
    [ -n "$enc" ] && return 0
    return 1
}

if _use_emoji; then
    _S="🚀 "; _OK="✔  "; _W="⚠  "; _E="✖  "; _I="🔌 "
    _SEP="─────────────────────────────────────────────────"
else
    _S="[SERVER] "; _OK="[OK]     "; _W="[WARN]   "
    _E="[ERROR]  "; _I="[INFO]   "
    _SEP="================================================="
fi

# Colors — disabled when not writing to a terminal (piped/redirected output)
if [ -t 1 ]; then
    R="\033[0m"; BOLD="\033[1m"
    CY="\033[96m"; GR="\033[92m"; YE="\033[93m"; RE="\033[91m"
else
    R=""; BOLD=""; CY=""; GR=""; YE=""; RE=""
fi

log_server() { echo -e "${CY}${_S}${BOLD}$*${R}"; }
log_ok()     { echo -e "${GR}${_OK}$*${R}"; }
log_warn()   { echo -e "${YE}${_W}$*${R}"; }
log_error()  { echo -e "${RE}${_E}$*${R}"; }
log_info()   { echo -e "${CY}${_I}$*${R}"; }
log_sep()    { echo -e "${CY}${_SEP}${R}"; }

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST="127.0.0.1"
PORT="9090"
MAX_CLIENTS="100"
MAX_CONNECTION_TIME="604800"
OMP_THREADS="1"

# Replace with your published image name once available:
#   ghcr.io/yourusername/whisperlive-universal:latest
# Build locally with: docker build -t whisperlive-universal .
UNIVERSAL_IMAGE="whisperlive-universal"

TRT_IMAGE="ghcr.io/collabora/whisperlive-tensorrt:latest"
MODEL="large-v2"
ENGINES_DIR="$HOME/whisper-engines"
CACHE_DIR="$HOME/.cache/whisper-live-docker"
CONTAINER_NAME="whisperlive"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
show_help() {
    grep '^#' "$0" | head -48 | tail -n +2 | sed 's/^# \{0,3\}//'
    exit 0
}

for arg in "$@"; do
    [ "$arg" = "--help" ] || [ "$arg" = "-h" ] && show_help
done

MODE="local"
BACKEND="auto"
TRT_MULTILINGUAL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        docker)
            MODE="docker"
            if [[ "${2:-}" != --* ]] && [[ -n "${2:-}" ]]; then
                BACKEND="$2"; shift
            fi
            shift ;;
        --model)        MODEL="$2";  shift 2 ;;
        --port)         PORT="$2";   shift 2 ;;
        --host)         HOST="$2";   shift 2 ;;
        --multilingual) TRT_MULTILINGUAL="--trt_multilingual"; shift ;;
        --help|-h)      show_help ;;
        *)              shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------
check_docker_permission() {
    if ! docker info &>/dev/null 2>&1; then
        log_error "Cannot connect to Docker daemon."
        log_warn  "Run:  newgrp docker  (or log out and back in)"
        exit 1
    fi
}

cleanup_existing_container() {
    local name="$1"
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
        log_warn "Removing existing container '${name}'..."
        docker rm -f "$name" &>/dev/null || true
    fi
}

# ---------------------------------------------------------------------------
# Signal trap — catches Ctrl+C, window close (SIGHUP), and SIGTERM.
# _STOPPING flag prevents the trap body from running more than once,
# avoiding repeated "Stopping..." messages when Ctrl+C is pressed
# multiple times while Docker is shutting down.
# ---------------------------------------------------------------------------
_STOPPING=0
setup_docker_trap() {
    local name="$1"
    # shellcheck disable=SC2064
    trap "
        if [ \$_STOPPING -eq 0 ]; then
            _STOPPING=1
            echo ''
            log_warn 'Stopping container ${name}...'
            docker stop '${name}' &>/dev/null || true
        fi
        exit 0
    " INT TERM HUP
}

get_gpu_flag() {
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
        echo "--gpus all"
    else
        echo ""
    fi
}

# Checks that both encoder and decoder engine files exist
validate_trt_engine() {
    local path="$1"
    [ -f "${path}/encoder/rank0.engine" ] && \
    [ -f "${path}/decoder/rank0.engine" ]
}

show_engine_dir_contents() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        log_warn "Directory does not exist: $dir"
        return
    fi
    log_info "Contents of ${dir}:"
    find "$dir" -maxdepth 3 2>/dev/null | sed 's/^/    /'
}

# =============================================================================
# DOCKER MODE
# =============================================================================
if [ "$MODE" = "docker" ]; then

    check_docker_permission
    cleanup_existing_container "$CONTAINER_NAME"
    mkdir -p "$CACHE_DIR"

    log_sep
    log_server "WhisperLive — Docker mode  (backend: ${BACKEND})"
    log_info   "Host: ${HOST} | Model: ${MODEL} | Port: ${PORT}"
    [ -n "$TRT_MULTILINGUAL" ] && log_info "Multilingual: enabled"
    log_sep
    echo -e "Press ${BOLD}Ctrl+C${R} to stop — container is removed on exit"
    echo ""

    # -------------------------------------------------------------------------
    # TensorRT
    # -------------------------------------------------------------------------
    if [ "$BACKEND" = "trt" ] || [ "$BACKEND" = "tensorrt" ]; then

        ENGINE_PATH="${ENGINES_DIR}/${MODEL}"

        if validate_trt_engine "$ENGINE_PATH"; then
            ENC_SIZE=$(du -sh "${ENGINE_PATH}/encoder/rank0.engine" 2>/dev/null | cut -f1)
            DEC_SIZE=$(du -sh "${ENGINE_PATH}/decoder/rank0.engine" 2>/dev/null | cut -f1)
            log_ok "TensorRT engine: ${ENGINE_PATH}"
            log_info "  encoder: ${ENC_SIZE:-?}  |  decoder: ${DEC_SIZE:-?}"
            if [ -z "$TRT_MULTILINGUAL" ]; then
                log_warn "TensorRT defaulting to English-only."
                log_warn "Add --multilingual for Spanish or other languages."
            fi
        else
            log_error "No valid TensorRT engine at: ${ENGINE_PATH}"
            show_engine_dir_contents "$ENGINES_DIR"
            echo ""
            log_warn "Expected layout:"
            log_warn "  ${ENGINE_PATH}/encoder/rank0.engine"
            log_warn "  ${ENGINE_PATH}/decoder/rank0.engine"
            echo ""
            log_warn "To build engines, run:"
            log_warn "  docker run -it --gpus all \\"
            log_warn "    -v ${ENGINES_DIR}:/whisper-engines \\"
            log_warn "    ${TRT_IMAGE} bash"
            log_warn "  # Inside the container:"
            log_warn "  bash /app/build_whisper_tensorrt.sh \\"
            log_warn "    /app/TensorRT-LLM-examples ${MODEL} float16"
            log_warn "  cp -r /app/TensorRT-LLM-examples/whisper/whisper_${MODEL}-float16 \\"
            log_warn "        /whisper-engines/${MODEL}"
            exit 1
        fi

        setup_docker_trap "$CONTAINER_NAME"

        # Resolve absolute path to our run_server.py so it can be mounted
        # into the container, overriding the older Collabora version which
        # does not accept --max_clients or --max_connection_time.
        LOCAL_RUN_SERVER="$(cd "$(dirname "$0")" && pwd)/run_server.py"
        if [ ! -f "$LOCAL_RUN_SERVER" ]; then
            log_error "run_server.py not found at: $LOCAL_RUN_SERVER"
            log_warn  "Place run_server.py in the same directory as this script."
            exit 1
        fi
        log_info "Using local run_server.py: $LOCAL_RUN_SERVER"

        # --host 0.0.0.0 is required inside Docker — does NOT expose to network.
        # Docker -p 127.0.0.1:9090:9090 accepts only localhost connections from the host.
        docker run --rm --gpus all \
            --name "$CONTAINER_NAME" \
            -v "${ENGINES_DIR}":/engines \
            -v "${CACHE_DIR}":/root/.cache/whisper-live \
            -v "${LOCAL_RUN_SERVER}":/app/run_server.py:ro \
            -p "${HOST}:${PORT}:${PORT}" \
            "$TRT_IMAGE" \
            python3 /app/run_server.py \
                --backend tensorrt \
                --trt_model_path "/engines/${MODEL}" \
                --host 0.0.0.0 \
                --port "$PORT" \
                --max_clients "$MAX_CLIENTS" \
                --max_connection_time "$MAX_CONNECTION_TIME" \
                $TRT_MULTILINGUAL &

        wait $!

    # -------------------------------------------------------------------------
    # OpenVINO
    # -------------------------------------------------------------------------
    elif [ "$BACKEND" = "openvino" ]; then

        INTEL_DEV_FLAG=""
        ls /dev/dri/renderD* &>/dev/null 2>&1 && INTEL_DEV_FLAG="--device /dev/dri"

        setup_docker_trap "$CONTAINER_NAME"

        docker run --rm \
            --name "$CONTAINER_NAME" \
            $INTEL_DEV_FLAG \
            -v whisper_models:/models \
            -v "${CACHE_DIR}":/root/.cache/whisper-live \
            -p "${HOST}:${PORT}:${PORT}" \
            -e WHISPER_MODELS_DIR=/models \
            "$UNIVERSAL_IMAGE" \
            --backend openvino \
            --model "$MODEL" \
            --host 0.0.0.0 \
            --port "$PORT" &

        wait $!

    # -------------------------------------------------------------------------
    # auto / cpu / cuda
    # -------------------------------------------------------------------------
    else
        GPU_FLAG="$(get_gpu_flag)"

        setup_docker_trap "$CONTAINER_NAME"

        docker run --rm \
            --name "$CONTAINER_NAME" \
            $GPU_FLAG \
            -v whisper_models:/models \
            -v "${ENGINES_DIR}":/engines \
            -v "${CACHE_DIR}":/root/.cache/whisper-live \
            -p "${HOST}:${PORT}:${PORT}" \
            -e WHISPER_MODELS_DIR=/models \
            -e ENGINES_DIR=/engines \
            "$UNIVERSAL_IMAGE" \
            --backend "$BACKEND" \
            --model "$MODEL" \
            --host 0.0.0.0 \
            --port "$PORT" &

        wait $!
    fi

# =============================================================================
# LOCAL MODE
# =============================================================================
else
    log_sep
    log_server "WhisperLive — local server (faster-whisper)"
    log_info   "Host: ${HOST} | Port: ${PORT}"
    log_sep
    echo -e "Press ${BOLD}Ctrl+C${R} to stop"
    echo ""

    python3 run_server.py \
        --host            "$HOST" \
        --port            "$PORT" \
        --backend         faster_whisper \
        --max_clients     "$MAX_CLIENTS" \
        --max_connection_time "$MAX_CONNECTION_TIME" \
        --omp_num_threads "$OMP_THREADS"
fi
