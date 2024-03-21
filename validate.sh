#! /usr/bin/env bash

test_input() {
    truth_table=$1
    echo "Testing ${truth_table}"
    ./qsyn -c "logger debug; qcir oracle -a 2 ${truth_table}; qcir write /tmp/test.qasm; quit -f" > /dev/null
    if ! python3 ./validate.py /tmp/test.qasm "${truth_table}" > /tmp/validate.log ; then
        echo "Failed: ${truth_table}"
        cat /tmp/validate.log
    fi
}

truth_table=$1
if [ -z "${truth_table}" ]; then
    python3 -c '[print(f"{n:04b}") for n in range(1<<4)]' | while read -r line; do
        test_input "${line}"
    done
else
    echo "Testing ${truth_table}"
    ./qsyn -c "logger debug; qcir oracle -a 2 ${truth_table}; qcir write /tmp/test.qasm; quit -f"
    python3 ./validate.py /tmp/test.qasm "${truth_table}"
fi
