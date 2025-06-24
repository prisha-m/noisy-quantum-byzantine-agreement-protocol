import matplotlib.pyplot as plt
from math import sqrt
import numpy as np
import os
import sys

def subtitle(name):
    if name == "r0":
        return "Faulty receiver (R0)"
    elif name == "n":
        return "No faulty nodes"
    elif name == "s":
        return "Faulty sender"

def process_row(values):
    return sum(values) / len(values)  # Mean of each row

def process_files(name):
    filenames = sorted([
        f for f in os.listdir(".")
        if f.endswith(".txt") and f.startswith(f"{name}_faulty")
    ])

    print("Processing files:", filenames)

    file_contents = []
    for file in filenames:
        with open(file, "r") as f:
            lines = [float(line.strip()) for line in f if line.strip()]
            file_contents.append(lines)

    # Compute the mean (failure probability) per row
    results = []
    for row_values in zip(*file_contents):
        result = process_row(list(row_values))
        results.append(result)

    return results, file_contents


def main(name="n", runs=100):
    linear_space = np.linspace(1e-6 ** (1/3), 10 ** (1/3), 15)
    scaled = linear_space ** 3
    t2 = scaled.tolist()
    even_x = list(range(len(t2)))

    output_failure_prob, raw_data = process_files(name)

    # Compute stderr per m using sqrt(p(1-p)/n)
    stderr = [sqrt((p * (1 - p)) / runs) for p in output_failure_prob]

    with open(f"../exact data/exact_{name}f.txt", "r") as file:
        exact = [float(line.strip()) for line in file if line.strip()]

    plt.rcParams.update({'font.size': 13})

    def plot_failure_probabilities(data, stderr, exact, title, filename):
        plt.figure(figsize=(8, 3.5))
        plt.ylim(-0.05, 0.25)
        line = plt.axhline(y=exact[27], color='r', linestyle='--', linewidth=1, label='Noiseless exact value for m=280')
        line.set_dashes([6, 6])
        plt.errorbar(even_x, data, yerr=stderr, marker='x', color='purple',
                     linestyle='None', capsize=0, elinewidth=1, label='Monte Carlo')
        plt.xticks(ticks=even_x, labels=[f"{x:.3g}" for x in t2], rotation=45)
        plt.xlabel('T2 decoherence times (s)')
        plt.ylabel('Failure probability')
        plt.title(title)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename)

    plot_failure_probabilities(
        output_failure_prob,
        stderr,
        exact,
        f"Failure probability vs T2 decoherence - {subtitle(name)}",
        f"{name}_faulty.png"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        main(name)