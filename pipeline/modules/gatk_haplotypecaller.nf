// ─── GATK HaplotypeCaller Module ───
// Input:  Recalibrated BAM
// Output: GVCF per sample

process GATK_HAPLOTYPECALLER {
    tag "${sample}"

    input:
    tuple val(sample), path(bam), path(bai)
    path fasta
    path dict
    path dbsnp

    output:
    tuple val(sample), path("${sample}.g.vcf.gz"),      emit: gvcf
    path("${sample}.g.vcf.gz.tbi"),                      emit: tbi

    script:
    """
    gatk HaplotypeCaller \
        --input ${bam} \
        --output ${sample}.g.vcf.gz \
        --reference ${fasta} \
        --dbsnp ${dbsnp} \
        --emit-ref-confidence GVCF \
        --native-pair-hmm-threads ${task.cpus}
    """
}
