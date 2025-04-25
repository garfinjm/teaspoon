#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess


def subsample_reads(desired_coverage, name_type, r1, r2, output_dir):
    """
    Subsamples paired-end reads using mash and rasusa.

    Args:
      desired_coverage (int): Desired coverage for subsampling.
      name_type (str): Downsampled file name format choose: prepend, insert, extend
      r1 (str): Path to the first read file.
      r2 (str): Path to the second read file.
      output_dir (str): Directory to save the downsampled files.
    """

    if not os.path.isfile(r1) or not os.path.isfile(r2):
        raise FileNotFoundError("One or both read files do not exist.")
    if not isinstance(desired_coverage, int) or desired_coverage <= 0:
        raise ValueError("Desired coverage must be a positive integer.")
    if name_type not in ["prepend", "insert", "extend"]:
        raise ValueError("name_type must be one of: prepend, insert, extend")

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    r1_filename = os.path.basename(r1)
    r2_filename = os.path.basename(r2)
    padded_coverage = str(desired_coverage).zfill(3)

    if name_type == "prepend":
        print("Using prepend naming scheme")
        r1_out = os.path.join(output_dir, f"{padded_coverage}xds-{r1_filename}")
        r2_out = os.path.join(output_dir, f"{padded_coverage}xds-{r2_filename}")
    elif name_type == "insert":
        print("Using insert naming scheme")
        r1_out = os.path.join(
            output_dir,
            f"{r1_filename.split('_', 1)[0]}-{padded_coverage}xds_{r1_filename.split('_', 1)[1]}",
        )
        r2_out = os.path.join(
            output_dir,
            f"{r2_filename.split('_', 1)[0]}-{padded_coverage}xds_{r2_filename.split('_', 1)[1]}",
        )
    elif name_type == "extend":
        print("Using extend naming scheme")
        r1_out = os.path.join(
            output_dir,
            re.sub(r"(.fastq.gz|.fastq)", f".{padded_coverage}xds\\1", r1_filename),
        )
        r2_out = os.path.join(
            output_dir,
            re.sub(r"(.fastq.gz|.fastq)", f".{padded_coverage}xds\\1", r2_filename),
        )
    else:
        print("Unrecognized naming scheme, defaulting to prepend")
        r1_out = os.path.join(output_dir, f"{padded_coverage}xds-{r1_filename}")
        r2_out = os.path.join(output_dir, f"{padded_coverage}xds-{r2_filename}")

    print(f"Processing {r1_filename} and {r2_filename}")

    # Copy the fastq files directly if either in the pair are empty(ish)
    if os.stat(r1).st_size <= 100 or os.stat(r2).st_size <= 100:
        print(
            f"Warning: {r1} or {r2} is effectively empty. Copying the files without downsampling."
        )
        shutil.copy(r1, r1_out)
        shutil.copy(r2, r2_out)
        return

    # Run mash, capturing stderr
    mash_command = [
        "mash",
        "sketch",
        "-o",
        "/dev/null",
        "-k",
        "21",
        "-m",
        "10",
        "-r",
        "-",
    ]
    with open(r1, "rb") as r1_file, open(r2, "rb") as r2_file:
        mash_process = subprocess.run(
            mash_command, input=r1_file.read() + r2_file.read(), capture_output=True
        )

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
        "rasusa",
        "reads",
        "-s",
        "11327544032246541232",
        "-g",
        str(genome_size),
        "-c",
        str(desired_coverage),
        "-o",
        r1_out,
        "-o",
        r2_out,
        r1,
        r2,
    ]
    subprocess.run(rasusa_command, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subsample reads to an approximate coverage using mash and rasusa."
    )
    parser.add_argument(
        "-c",
        "--coverage",
        required=True,
        type=int,
        help="Desired coverage for subsampling.",
    )
    parser.add_argument(
        "-n",
        "--name_type",
        required=False,
        default="prepend",
        type=str,
        help="Downsampled file name format (Default: prepend). Choose: prepend, insert, extend",
    )
    parser.add_argument(
        "-r1", "--read1", required=True, help="Path to the first read file."
    )
    parser.add_argument(
        "-r2", "--read2", required=True, help="Path to the second read file."
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        required=False,
        default=".",
        help="Directory to save the downsampled files.",
    )
    args = parser.parse_args()

    subsample_reads(
        args.coverage, args.name_type, args.read1, args.read2, args.output_dir
    )
