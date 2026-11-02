from collections import defaultdict


import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract BioProject accessions from the NCBI SRA_Accessions.tab file."
    )

    parser.add_argument(
        "--biosample_list",
        required=True,
        help="Text file containing BioSample accessions (one per line)."
    )

    parser.add_argument(
        "--sra_tab",
        required=True,
        help="Path to SRA_Accessions.tab."
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output TSV file."
    )

    return parser.parse_args()


from collections import defaultdict


def main():

    args = parse_args()

    print("Loading BioSample list...")

    with open(args.biosample_list) as f:
        wanted = {line.strip() for line in f if line.strip()}

    print(f"Loaded {len(wanted):,} BioSample IDs")

    matches = defaultdict(set)
    checked = 0

    print("Scanning SRA accession table...")

    with open(args.sra_tab) as fin:

        header = fin.readline().rstrip("\n").split("\t")

        biosample_col = header.index("BioSample")
        bioproject_col = header.index("BioProject")

        print(
            f"Using columns: BioSample={biosample_col + 1}, "
            f"BioProject={bioproject_col + 1}"
        )

        for line in fin:

            checked += 1

            fields = line.rstrip("\n").split("\t")

            biosample = fields[biosample_col]

            if biosample in wanted:

                bioproject = fields[bioproject_col]

                if bioproject and bioproject != "-":
                    matches[biosample].add(bioproject)

            if checked % 500000 == 0:

                print(
                    f"Processed {checked:,} SRA records "
                    f"({len(matches):,}/{len(wanted):,} BioSamples resolved)"
                )

    print("Writing output...")

    missing = []

    with open(args.output, "w") as out:

        out.write("BioSample\tBioProject\n")

        for biosample in sorted(wanted):

            projects = sorted(matches[biosample])

            if projects:
                out.write(
                    f"{biosample}\t{','.join(projects)}\n"
                )
            else:
                out.write(f"{biosample}\t\n")
                missing.append(biosample)

    print("\nFinished")
    print(f"Scanned {checked:,} SRA records")
    print(f"Resolved {len(matches):,} of {len(wanted):,} BioSamples")

    if missing:

        missing_file = args.output.replace(
            ".tsv",
            "_missing_bioproject.txt"
        )

        with open(missing_file, "w") as f:
            f.write("\n".join(missing))

        print(f"{len(missing):,} BioSamples still have no BioProject")
        print(f"Written to: {missing_file}")


if __name__ == "__main__":
    main()
