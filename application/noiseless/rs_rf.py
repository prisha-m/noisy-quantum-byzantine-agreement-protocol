from programs.sender import SenderProgram
from programs.receiver0 import Receiver0Program
from programs.receiver1 import Receiver1Program
from program_conditions import ProgramConditions
from constants import DOMAIN_VIOLATION, ABORT

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

from concurrent.futures import ProcessPoolExecutor

import sys

def prepare_process(i, x, cfg, runs=100):
    # Receiver0 faulty

    conditions = ProgramConditions(
        _m=i,
        _x=x,
        _s_faulty=False,
        _r0_faulty=True,
        _print_status=False
    )

    sender_program = SenderProgram(conditions)
    receiver0_program = Receiver0Program(conditions)
    receiver1_program = Receiver1Program(conditions)

    result = run(
        config=cfg,
        programs={
            "Sender": sender_program,
            "Receiver0": receiver0_program,
            "Receiver1": receiver1_program
        },
        num_times=runs,
    )

    result = [[list(a)[0], list(b)[0]] for a, b in zip(result[0], result[2])]
    fail_prob_r0f = sum([1 for r in result if r[1] == DOMAIN_VIOLATION or r[0] != r[1]]) / runs

    return fail_prob_r0f


if __name__ == "__main__":
    id = sys.argv[1] if len(sys.argv) > 1 else 0

    runs = 100
    min_m = 20
    max_m = 400
    increment = 10
    m_values = list(range(min_m, max_m+1, increment))

    output_failure_prob_r0f = [0] * len(m_values)

    cfg = StackNetworkConfig.from_file("config.yaml")

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for j, i in enumerate(m_values):
            x = 0

            future = executor.submit(prepare_process, i, x, cfg, runs)

            futures.append((future, j))


        for future, j in futures:
            fail_prob_r0f = future.result()
            output_failure_prob_r0f[j] = fail_prob_r0f


    with open(f"results/raw/r0_faulty_{id}.txt", "w") as f:
        f.write("\n")
        for item in output_failure_prob_r0f:
            f.write(f"{item}\n")