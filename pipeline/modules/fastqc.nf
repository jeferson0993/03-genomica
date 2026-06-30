// ─── FASTQC Module ───
// Input:  FASTQ files
// Output: HTML/zip QC reports

process FASTQC {
    tag "${sample}"

    input:
    tuple val(sample), path(fastq_1), path(fastq_2)

    output:
    path("${sample}_fastqc.html"), emit: html
    path("${sample}_fastqc.zip"),  emit: zip

    script:
    """
    fastqc --threads ${task.cpus} ${fastq_1} ${fastq_2}
    """
}
