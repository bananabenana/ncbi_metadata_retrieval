import os
import argparse
import xml.etree.ElementTree as ET
import csv
from concurrent.futures import ProcessPoolExecutor

def parse_xml(file_path):
    """Extract Filename, BioSample, Attributes, SRA, and Assembly data from a single XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract filename without extension
        filename = os.path.splitext(os.path.basename(file_path))[0]


        # Extract BioSample accession
        biosample = root.find(".//BioSample")
        biosample_id = biosample.attrib.get("accession", "Unknown") if biosample is not None else "Unknown"

        # Extract Attributes
        attributes = {}
        for attr in root.findall(".//Attribute"):
            attr_name = attr.attrib.get("attribute_name", "Unknown")
            attributes[attr_name] = attr.text.strip() if attr.text else "NA"

        # Extract SRA Accession
        sra_ids = [sra.text.strip() for sra in root.findall(".//Id[@db='SRA']")]
        sra_accession = ";".join(sra_ids) if sra_ids else "NA"

        # Extract Assembly Accession
        assembly_ids = [assembly.text.strip() for assembly in root.findall(".//Id[@db='Assembly']")]
        assembly_accession = ";".join(assembly_ids) if assembly_ids else "NA"

        return {
            "Filename": filename,
            "BioSample": biosample_id,
            "SRA": sra_accession,
            "Assembly": assembly_accession,
            **attributes
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def process_xml_files(input_dir, output_file, num_threads=4):
    """Process all XML files in a directory in parallel and save the extracted data to a TSV file."""
    xml_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".xml")]

    all_attributes = set()
    results = []

    # Use ProcessPoolExecutor for parallel XML parsing
    with ProcessPoolExecutor(max_workers=num_threads) as executor:
        for result in executor.map(parse_xml, xml_files):
            if result:
                all_attributes.update(result.keys())
                results.append(result)

    # Ensure consistent column order
    fieldnames = (
        ["Filename", "BioSample", "SRA", "Assembly"] +
        sorted(all_attributes - {"Filename", "BioSample", "SRA", "Assembly"})
    )

    # **Single-threaded file writing to prevent race conditions**
    with open(output_file, "w", newline="") as tsvfile:
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"TSV file saved as {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract BioSample, Attributes, SRA, and Assembly info from GenBank XML files.")
    parser.add_argument("--input_dir", required=True, help="Directory containing XML files")
    parser.add_argument("--output", default="combined.tsv", help="Output TSV file (default: combined.tsv)")
    parser.add_argument("--threads", type=int, default=4, help="Number of parallel threads for XML parsing (default: 4)")

    args = parser.parse_args()
    process_xml_files(args.input_dir, args.output, args.threads)
