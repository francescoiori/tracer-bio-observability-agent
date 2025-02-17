#!/bin/bash

# RNA-Seq Dummy Pipeline with Automated File Downloads
# Author: ChatGPT

set -e  # Exit on error
set -u  # Treat unset variables as errors
set -o pipefail  # Fail if any pipeline command fails

# Define working directory
WORKDIR="./rna_seq_pipeline"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO] $1"
}

# Ensure Python and Virtual Environment are Available
if ! command -v python3.12 &> /dev/null; then
    log "Python3 not found. Please install it."
    exit 1
fi

# Create and Activate Virtual Environment
if [ ! -d "env" ]; then
    log "Creating Python virtual environment..."
    python3.12 -m venv env
fi
source env/bin/activate

# Install Required Python Packages
log "Installing HTSeq..."
pip install --upgrade pip > /dev/null
pip install htseq > /dev/null

# Download Example FASTQ File
if [ ! -f "sample_reads.fastq.gz" ]; then
    log "Downloading sample FASTQ reads..."
    wget -q -O sample_reads.fastq.gz https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR000/SRR000001/SRR000001.fastq.gz
    gunzip sample_reads.fastq.gz || true
fi
log "FASTQ file ready."

# Download Reference Genome
if [ ! -f "reference.fasta" ]; then
    log "Downloading reference genome..."
    wget -q -O reference.fa.gz https://ftp.ensembl.org/pub/release-113/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz
    gunzip reference.fa.gz
    mv reference.fa reference.fasta
fi
log "Reference genome ready."

# Download GTF File
if [ ! -f "annotations.gtf" ]; then
    log "Downloading GTF annotations..."
    wget -q -O annotations.gtf.gz https://ftp.ensembl.org/pub/release-100/gtf/homo_sapiens/Homo_sapiens.GRCh38.100.chr.gtf.gz
    gunzip annotations.gtf.gz
fi
log "GTF file ready."

# Step 1: Quality Control using FastQC
log "Running FastQC..."
fastqc sample_reads.fastq -o .
log "Quality control completed."

# Step 2: Read Trimming (Simulated using seqtk)
log "Trimming reads..."
seqtk trimfq sample_reads.fastq > trimmed_reads.fastq
log "Read trimming completed."

# Step 3: Index the Reference Genome
log "Indexing reference genome..."
bwa index reference.fasta
log "Reference genome indexed."

# Step 4: Read Alignment using BWA
log "Aligning reads with BWA..."
bwa mem reference.fasta trimmed_reads.fastq > aligned_reads.sam
log "Alignment completed."

# Step 5: Convert SAM to BAM, Sort, and Index using Samtools
log "Processing BAM files..."
samtools view -Sb aligned_reads.sam > aligned_reads.bam
samtools sort aligned_reads.bam -o sorted_reads.bam
samtools index sorted_reads.bam
log "BAM processing completed."

# Step 6: Gene Expression Quantification using HTSeq-Count
log "Running HTSeq-count..."
htseq-count -f bam -r pos -s no sorted_reads.bam annotations.gtf > gene_expression.tsv
log "Gene expression quantification completed."

# Cleanup
rm aligned_reads.sam  # Save space
log "RNA-seq pipeline completed successfully."

# Deactivate Virtual Environment
deactivate
