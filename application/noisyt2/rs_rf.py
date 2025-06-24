from programs.sender import SenderProgram
from programs.receiver0 import Receiver0Program
from programs.receiver1 import Receiver1Program
from program_conditions import ProgramConditions
from constants import DOMAIN_VIOLATION, ABORT

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

import numpy as  np

from concurrent.futures import ProcessPoolExecutor
import sys

def format_seconds_as_nanoseconds(seconds: int) -> str:
    nanoseconds = seconds * 1_000_000_000  
    return f"{int(nanoseconds):_}"

def prepare_process(x, p, i, runs=100):

    # Receiver0 faulty

    cfg = StackNetworkConfig.from_file("config.yaml")

    # change config for t2 params
    for stack in cfg.stacks:    
        stack.qdevice_cfg['carbon_T2'] = str(i)     

    result = run(
        config=cfg,
        programs={
            "Sender": p['s-rf'],
            "Receiver0": p['r0-rf'],
            "Receiver1": p['r1-rf']
        },
        num_times=runs,
    )

    result = [[list(a)[0], list(b)[0]] for a, b in zip(result[0], result[2])]
    fail_prob_r0f = sum([1 for r in result if r[1] == DOMAIN_VIOLATION or r[0] != r[1]]) / runs

    return fail_prob_r0f


if __name__ == "__main__":
    id = sys.argv[1] if len(sys.argv) > 1 else 0

    runs = 100
    m = 280
    x = 0
    linear_space = np.linspace(1e-6 ** (1/3), 10 ** (1/3), 15)
    scaled = linear_space ** 3
    t2 = scaled.tolist()

    output_failure_prob_r0f = [0] * len(t2)

    rfc = ProgramConditions(
        _m=m,
        _x=x,
        _s_faulty=False,
        _r0_faulty=True
    )

    programs = {
        's-rf' : SenderProgram(rfc),
        'r0-rf' : Receiver0Program(rfc),
        'r1-rf' : Receiver1Program(rfc)
    }

    with ProcessPoolExecutor(max_workers=15) as executor:
        futures = []
        for j, i in enumerate(t2):

            future = executor.submit(prepare_process, x, programs, i, runs)

            futures.append((future, j))


        for future, j in futures:
            fail_prob_r0f = future.result()
            output_failure_prob_r0f[j] = fail_prob_r0f


    with open(f"results/raw results/r0_faulty_{id}.txt", "w") as f:
        for item in output_failure_prob_r0f:
            f.write(f"{item}\n")