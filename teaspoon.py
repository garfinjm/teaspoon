#!/usr/bin/env python3
import argparse
import os
import re
import subprocess


def subsample_reads(desired_coverage, name_type, r1, r2):
    """
    Subsamples paired-end reads using mash and rasusa.

    Args:
        desired_coverage (int): Desired coverage for subsampling.
        name_type (str): Downsampled file name format choose: prepend, insert, extend
        r1 (str): Path to the first read file.
        r2 (str): Path to the second read file.
    """

    r1_path, r1_filename = os.path.split(r1)
    r2_path, r2_filename = os.path.split(r2)
    padded_coverage = str(desired_coverage).zfill(3)

    if (name_type == "prepend"):
        print("Using prefix naming scheme")
        r1_out = os.path.join(r1_path, f"{padded_coverage}xds-{r1_filename}")
        r2_out = os.path.join(r2_path, f"{padded_coverage}xds-{r2_filename}")
    elif (name_type == "insert"):
        print("Using insert naming scheme")
        r1_split = r1_filename.split("_", 1)
        r1_out = f"{r1_split[0]}-{padded_coverage}xds_{r1_split[1]}"
        r2_split = r2_filename.split("_", 1)
        r2_out = f"{r2_split[0]}-{padded_coverage}xds_{r2_split[1]}"
    elif (name_type == "extend"):
        print("Using extend naming scheme")
        regex_pattern = r"." + padded_coverage + r"xds\1"
        r1_out = re.sub(r'(.fastq.gz|.fastq)', regex_pattern, r1_filename)
        r2_out = re.sub(r'(.fastq.gz|.fastq)', regex_pattern, r2_filename)
    else:
        print("Unrecognized naming scheme, defaulting to prepend")


    # Run mash, capturing stderr
    mash_command = [
        "mash", "sketch",
        "-o", "/dev/null",
        "-k", "21",
        "-m", "10",
        "-r", "-",
    ]
    with open(r1, 'rb') as r1_file, open(r2, 'rb') as r2_file:
        mash_process = subprocess.run(mash_command, input=r1_file.read() + r2_file.read(), capture_output=True)

    # Capture estimated genome size and coverage from mash stderr
    genome_size = None
    coverage = None
    for line in mash_process.stderr.decode().splitlines():
        if line.startswith("Estimated genome size:"):
            genome_size = float(line.split(":")[1].strip())
        elif line.startswith("Estimated coverage:"):
            coverage = float(line.split(":")[1].strip())
            coverage = round(coverage)

    if genome_size is None or coverage is None:
        raise ValueError("Could not parse genome size and coverage from mash output.")

    # Run rasusa
    rasusa_command = [
        "rasusa", "reads",
        "-g", str(genome_size),
        "-c", str(desired_coverage),  # Use desired_coverage here
        "-o", r1_out,
        "-o", r2_out,
        r1,
        r2
    ]
    subprocess.run(rasusa_command, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subsample reads to an approximate coverage using mash and rasusa.")
    parser.add_argument("-c", "--coverage", required=True, type=int, help="Desired coverage for subsampling.")
    parser.add_argument("-n", "--name_type", required=False, default="prepend", type=str, help="Downsampled file name format (Default: prepend). Choose: prepend, insert, extend")
    parser.add_argument("-r1", "--read1", required=True, help="Path to the first read file.")
    parser.add_argument("-r2", "--read2", required=True, help="Path to the second read file.")
    args = parser.parse_args()

    subsample_reads(args.coverage, args.name_type, args.read1, args.read2)