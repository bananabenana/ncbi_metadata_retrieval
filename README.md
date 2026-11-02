# ncbi_metadata_retrieval
Scripts to extract BioProject, BioSample and SRA metadata.

## Quick usage

Install dependencies:
```bash
mamba create -y -n ncbi_metadata_retrieval
mamba install -y -n ncbi_metadata_retrieval anaconda::lxml
mamba install -y -n ncbi_metadata_retrieval bioconda::entrez-direct
mamba install -y -n ncbi_metadata_retrieval conda-forge::parallel
mamba activate ncbi_metadata_retrieval
```

Use Entrez Direct to download targeted metadata from NCBI using assembly accessions
```bash
cat assemblies.txt | parallel -j 4 --delay 3 '
  output="BioSample_metadata/{}_metadata.xml"

  if [[ ! -s "$output" ]]; then
    esearch -db assembly -query "{}" \
      | elink -target biosample \
      | efetch -format xml \
      > "$output"
  else
    echo "File $output exists and is non-empty, skipping {}"
  fi
'
```

Convert metadata in .xml format to .tsv format
```bash
python efetch_xml_BioSample_to_tsv.py \
    --input_dir BioSample_metadata \
    --output combined_BioSample_metadata.tsv \
    --threads 4
```

Obtain BioProject IDs using a list of BioSample IDs:
```bash
# Download NCBI BioSample data to query locally
wget https://ftp.ncbi.nlm.nih.gov/biosample/biosample_set.xml.gz

# Run script
python BioProject_from_BioSample.py \
    --biosample_list BioProjects_list_NCBI.txt \
    --ncbi_xml biosample_set.xml.gz \
    --output biosample_bioproject.tsv \
    --log biosample_progress.log
```

Obtain BioProject IDs from SRA using a list of BioSample IDs:
```bash
# Download NCBI SRA records
wget ftp://ftp.ncbi.nlm.nih.gov/sra/reports/Metadata/SRA_Accessions.tab

# Run script
python BioProject_from_SRA.py \
    --biosample_list BioProjects_list_NCBI.txt \
    --sra_tab SRA_Accessions.tab \
    --output biosample_bioproject_from_sra.tsv
```

## Input files

### Example assemblies.txt
```
GCA_002055515.1
GCA_016939475.1
GCA_021165835.1
GCA_021165855.1
GCA_032594495.1
GCA_039725545.1
GCA_054130465.1
```

### Example BioProjects_list_NCBI.txt
```
SAMD00000816
SAMD00002818
SAMD00004208
SAMD00006363
SAMD00008944
```


