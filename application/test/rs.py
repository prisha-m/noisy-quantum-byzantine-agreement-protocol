

from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

import numpy as np

from concurrent.futures import ProcessPoolExecutor

from program import S, R


def format_seconds_as_nanoseconds(seconds: int) -> str:
    nanoseconds = seconds * 1_000_000_000  
    return f"{int(nanoseconds):_}"


if __name__ == "__main__":
    cfg = StackNetworkConfig.from_file("config.yaml")

    i = 1e-6

    for stack in cfg.stacks:    
        stack.qdevice_cfg['carbon_T1'] = str(format_seconds_as_nanoseconds(i))
        # rule: 2t1 >= t2 
        stack.qdevice_cfg['carbon_T2'] = str(format_seconds_as_nanoseconds(i/2))    

    p = S()

    result = run(
        config=cfg,
        programs={
            "S": S(),
            "R": R(),  # Using the same program for both S and R for simplicity
        },
        num_times=100,
    )

    result = list(zip(result[0], result[1]))
    print(result)
    bad = 0
    for r in result:
        
        if r[0][0] == 0 and r[0][1] == 0 and r[1][0] == 1 and r[1][1] == 1:
            pass
        elif r[0][0] == 1 and r[0][1] == 1 and r[1][0] == 0 and r[1][1] == 0:
            pass 
        elif r[0][0] == 1 and r[0][1] == 0 and r[1][0] == 1 and r[1][1] == 0:
            pass
        elif r[0][0] == 0 and r[0][1] == 1 and r[1][0] == 0 and r[1][1] == 1:
            pass
        elif r[0][0] == 1 and r[0][1] == 0 and r[1][0] == 0 and r[1][1] == 1:
            pass
        elif r[0][0] == 0 and r[0][1] == 1 and r[1][0] == 1 and r[1][1] == 0:
            pass
        else:
            bad += 1

    print(f"Bad results: {bad} out of {len(result)}")

