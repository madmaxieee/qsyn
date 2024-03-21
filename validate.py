from argparse import ArgumentParser
from typing import Literal, Sequence, Union

from qiskit import Aer, QuantumCircuit, transpile
from qiskit.circuit import Qubit
from qiskit.transpiler.passmanager_config import pprint

CCCX_DEF = "gate cccx q0,q1,q2,q3 { h q3; p(pi/8) q0; p(pi/8) q1; p(pi/8) q2; p(pi/8) q3; cx q0,q1; p(-pi/8) q1; cx q0,q1; cx q1,q2; p(-pi/8) q2; cx q0,q2; p(pi/8) q2; cx q1,q2; p(-pi/8) q2; cx q0,q2; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; h q3; }"


def main():
    parser = ArgumentParser()
    parser.add_argument("qasm_file", help="The QASM file to test")
    parser.add_argument(
        "truth_table",
        help="the truth table to compare the results to",
    )
    args = parser.parse_args()

    print("=====================================")
    print(f"Testing {args.qasm_file} against {args.truth_table}")

    qasm_str = preprocess_qasm(args.qasm_file)
    qc = QuantumCircuit.from_qasm_str(qasm_str)
    print(qc.draw("text"))

    truth_table = args.truth_table[::-1]
    num_bits = len(truth_table)
    num_inputs = (num_bits - 1).bit_length()
    result = test_all_inputs(qc, range(num_inputs))
    has_error = False
    output_index = num_inputs
    for input, outputs in result.items():
        input_changed = input != outputs[:num_inputs]
        output_wrong = outputs[output_index] != truth_table[int(input[::-1], 2)]
        ancilla_changed = any(
            outputs[i] != "0" for i in range(output_index + 1, len(outputs))
        )

        has_error = input_changed or output_wrong or ancilla_changed

        print(f"{input} -> ", end="")

        if input_changed:
            print(f"\033[91m{outputs[:num_inputs]}\033[0m ", end="")
        else:
            print(f"{outputs[:num_inputs]} ", end="")

        if output_wrong:
            print(f"\033[91m{outputs[output_index]}\033[0m ", end="")
        else:
            print(f"{outputs[output_index]} ", end="")

        if ancilla_changed:
            print(f"\033[91m{outputs[output_index + 1:]}\033[0m ", end="")
        else:
            print(f"{outputs[output_index + 1:]} ", end="")

        if has_error:
            print(f" \033[91m(FAIL)\033[0m", end="")
        else:
            print(f" \033[92m(PASS)\033[0m", end="")

        print()

    if has_error:
        exit(1)


def measure_str(
    qc: QuantumCircuit,
    backend: Union[Literal["aer"], Literal["ibmq"]] = "aer",
):
    if backend == "aer":
        sim = Aer.get_backend("aer_simulator")
    elif backend == "ibmq":
        raise NotImplementedError
    transpiled_qc = transpile(qc, sim)
    job = sim.run(transpiled_qc)
    result = job.result().get_counts()

    measured_str = max(result, key=result.get)
    return measured_str


def measure(
    qc: QuantumCircuit,
    backend: Union[Literal["aer"], Literal["ibmq"]] = "aer",
):
    measured_str = measure_str(qc, backend)
    measured_int = int(measured_str, 2)
    return measured_int


def one_positions(i: int, n_bits: int):
    res = []
    for j in range(n_bits):
        if (1 << j) & i:
            res.append(j)
    return res


def test_all_inputs(to_test: QuantumCircuit, input_qubits: Sequence[Union[int, Qubit]]):
    data = {}
    for i in range(2 ** len(input_qubits)):
        one_pos = one_positions(i, len(input_qubits))
        qc = QuantumCircuit(to_test.num_qubits)
        for j in one_pos:
            qc.x(input_qubits[j])
        qc.append(to_test.to_gate(), list(range(qc.num_qubits)))
        qc.measure_all()
        measured_str = measure_str(qc)
        i_str = bin(i)[2:].zfill(len(input_qubits))[::-1]
        data[i_str] = measured_str[::-1]

    return data


def preprocess_qasm(file_name: str) -> str:
    with open(file_name, "r") as file:
        data = file.read()
    if data.find("cccx") != -1:
        lines = data.split("\n")
        lines.insert(2, CCCX_DEF)
        qasm = "\n".join(lines)
        return qasm
    else:
        return data


if __name__ == "__main__":
    main()
