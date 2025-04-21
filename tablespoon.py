#!/usr/bin/env python3

import os
import sys
import argparse
from teaspoon import subsample_reads  # Import the subsample_reads function

def downsample_paired_reads(desired_coverage, name_type, input_dir, output_dir):
  """
  Downsamples paired-end Illumina reads in a input_dir using teaspoon.py.

  Args:
    desired_coverage (int): The desired coverage for downsampling.
    name_type (str): Downsampled file name format choose: prepend, insert, extend
    input_dir (str): Path to the directory containing the paired-end reads.
    output_dir (str): Path to the directory where downsampled reads will be saved.
  """
  if not os.path.isdir(input_dir):
    print(f"Error: {input_dir} is not a valid directory.")
    sys.exit(1)
  if not os.path.isdir(output_dir):
    os.makedirs(output_dir)
  # Check name_type is one of: prepend, insert, extend
  if name_type not in ["prepend", "insert", "extend"]:
    print("Error: name_type must be one of: prepend, insert, extend")
    sys.exit(1)
  if not isinstance(desired_coverage, int) or desired_coverage <= 0:
    print("Error: Desired coverage must be a positive integer.")
    sys.exit(1)

  # Find pairs of reads in input input_dir that match illumina MiSeq/NextSeq naming schemes and NCBI fasterq-dump outputs
  read_pairs = []
  for filename in os.listdir(input_dir):
    if filename.endswith(".fastq") or filename.endswith(".fastq.gz"):
      # Check if the file is paired-end
      if "_1." in filename or "_R1_" in filename:
        read1_path = os.path.join(input_dir, filename)
        read2_path = read1_path.replace("_1.", "_2.").replace("_R1_", "_R2_")
        if os.path.isfile(read2_path):
          read_pairs.append((read1_path, read2_path))

  if not read_pairs:
    print("No paired-end reads found in the input directory.")
    sys.exit(1)

  # Process each pair of reads
  for read1_path, read2_path in read_pairs:
    try:
      # Call the teaspoon.py subsample_reads function
      subsample_reads(
        desired_coverage, name_type, read1_path, read2_path, output_dir
      )
    except Exception as e:
      print(f"Error processing {read1_path} and {read2_path}: {e}")
      sys.exit(1)
  print(
      f"Successfully downsampled reads to {desired_coverage}x coverage and saved to {output_dir}"
  )


if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(
    description="Subsample reads in a directory to a specified (rough) coverage using teaspoon."
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
    "-i",
    "--input_dir",
    required=True,
    help="Path to the directory containing the input fastq files."
  )
  parser.add_argument(
    "-o",
    "--output_dir",
    required=False,
    default=".",
    help="Output path for downsampled fastq files."
  )
  parser.add_argument(
    "-c",
    "--coverage",
    required=True,
    type=int,
    help="Desired approximate coverage for subsampling."
  )
  args = parser.parse_args()

  downsample_paired_reads(args.coverage, args.name_type, args.input_dir, args.output_dir)