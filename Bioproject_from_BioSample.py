import gzip
from lxml import etree
import argparse
import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract BioProject accessions from NCBI BioSample XML dump"
    )

    parser.add_argument(
        "--biosample_list",
        required=True,
        help="Text file containing BioSample accessions, one per line"
    )

    parser.add_argument(
        "--ncbi_xml",
        required=True,
        help="NCBI biosample_set.xml.gz file"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output TSV file"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output file"
    )

    parser.add_argument(
        "--log",
        default=None,
        help="Progress log file"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    print("Loading BioSample list...")

    with open(args.biosample_list) as f:
        wanted = {line.strip() for line in f if line.strip()}

    total_requested = len(wanted)

    print(f"Loaded {total_requested} BioSample IDs")

    missing_bioprojects = []

    # Resume support
    if args.resume:

        try:
            completed = set()

            with open(args.output) as f:
                next(f)  # skip header

                for line in f:
                    if line.strip():

                        fields = line.rstrip("\n").split("\t")

                        completed.add(fields[0])

                        if len(fields) > 1 and fields[1] == "":
                            missing_bioprojects.append(fields[0])

            wanted -= completed

            print(
                f"Resume mode: {len(completed)} already processed"
            )

            print(
                f"Remaining BioSamples: {len(wanted)}"
            )

            if len(wanted) == 0:
                print("All BioSamples already processed.")
                return

        except FileNotFoundError:

            print(
                "Resume requested but output file not found. Starting fresh."
            )
            args.resume = False


    found = 0
    checked = 0

    print("Parsing BioSample XML...")

    write_mode = "a" if args.resume else "w"

    with open(args.output, write_mode) as out:

        if not args.resume:
            out.write("BioSample\tBioProject\n")


        with gzip.open(args.ncbi_xml, "rb") as f:

            for event, elem in etree.iterparse(
                f,
                tag="BioSample"
            ):

                checked += 1

                if args.log and checked % 100000 == 0:

                    with open(args.log, "a") as log:

                        log.write(
                            f"{datetime.datetime.now()}\t"
                            f"streamed={checked}\t"
                            f"found={found}\t"
                            f"remaining={len(wanted)}\n"
                        )


                accession = elem.attrib.get("accession")


                if accession in wanted:

                    bioprojects = []

                    for link in elem.findall("./Links/Link"):

                        if link.attrib.get("target") == "bioproject":

                            label = link.attrib.get("label")

                            if label:
                                bioprojects.append(label)


                    if bioprojects:

                        out.write(
                            f"{accession}\t{','.join(bioprojects)}\n"
                        )

                    else:

                        out.write(
                            f"{accession}\t\n"
                        )

                        missing_bioprojects.append(accession)


                    found += 1

                    wanted.remove(accession)

                    print(
                        f"[{found}/{total_requested}] "
                        f"{accession} -> "
                        f"{','.join(bioprojects) if bioprojects else 'NO BIOPROJECT'}"
                    )


                    if not wanted:

                        print(
                            "All requested BioSamples found. Stopping early."
                        )
                        break


                if checked % 100000 == 0:

                    print(
                        f"Processed {checked:,} BioSample records..."
                    )


                # free memory
                elem.clear()

                while elem.getprevious() is not None:
                    del elem.getparent()[0]


    print("\nFinished")
    print(f"Scanned {checked:,} BioSample records")
    print(
        f"Found this run: {found}/{total_requested} BioSamples"
    )

    if wanted:

        print(
            f"Still missing {len(wanted)} BioSamples from XML"
        )

        missing_file = args.output.replace(
            ".tsv",
            "_missing_biosamples.txt"
        )

        with open(missing_file, "w") as f:
            f.write("\n".join(sorted(wanted)))

        print(
            f"Written unresolved BioSamples to: {missing_file}"
        )


    if missing_bioprojects:

        missing_file = args.output.replace(
            ".tsv",
            "_missing_bioproject.txt"
        )

        with open(missing_file, "w") as f:
            f.write("\n".join(sorted(set(missing_bioprojects))))

        print(
            f"{len(set(missing_bioprojects))} BioSamples had no BioProject link"
        )

        print(
            f"Written to: {missing_file}"
        )


if __name__ == "__main__":
    main()
