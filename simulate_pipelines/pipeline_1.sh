#!/bin/bash

LOG_DIR="logs"

if [ ! -d $LOG_DIR ]; then
    mkdir $LOG_DIR
fi

LOG_FILE="$LOG_DIR/pipeline_1_$(date +'%Y%m%d_%H%M%S').log"

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

run_stress_test() {
    local description=$1
    shift
    log "=== $description ==="
    stress "$@" | tee -a "$LOG_FILE"
    sleep 2
}

log "🚀 Starting pipeline_1..."

# Run stress tests
run_stress_test "Low stress (CPU only)" --cpu 2 --timeout 10
run_stress_test "Medium stress (CPU only)" --cpu 4 --timeout 10
run_stress_test "I/O operations with 4 workers" --io 4 --timeout 20
run_stress_test "Memory stress: 2 workers allocating 256MB" --vm 2 --vm-bytes 128M --timeout 20
run_stress_test "Combined CPU, Memory, and I/O stress test" --cpu 2 --vm 2 --vm-bytes 64M --io 2 --timeout 20

log "✅ Completed pipeline_1!"