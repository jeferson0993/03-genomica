// ─── BWA-MEM Alignment Module ───
// Input:  FASTQ pair + BWA index prefix
// Output: Sorted BAM/CRAM + index
// Parameter `cram` (boolean) controls output format: CRAM if true, BAM if false

process BWA_ALIGN {
    tag "${sample}"

    input:
    tuple val(sample), path(fastq_1), path(fastq_2)
    path bwa_index_prefix
    path ref_fasta

    output:
    tuple val(sample), path("${sample}.sorted.{bam,cram}", arity: "1"), emit: alignment
    path("${sample}.sorted.{bam,cram}.crai", arity: "1"),               emit: index

    script:
    def out_ext = params.cram ? 'cram' : 'bam'
    def out_idx_ext = params.cram ? 'cram.crai' : 'bam.bai'
    """
    bwa mem \
        -t ${task.cpus} \
        -K 100000000 \
        -Y \
        ${bwa_index_prefix} \
        ${fastq_1} \
        ${fastq_2} \
    | samtools sort \
        -@ ${task.cpus} \
        -O ${out_ext.startsWith('c') ? 'cram' : 'bam'} \
        -T ${sample}.tmp \
        -o ${sample}.sorted.${out_ext} \
        -

    ${params.cram ? "samtools index ${sample}.sorted.cram" : "samtools index ${sample}.sorted.bam"}
    """
}
