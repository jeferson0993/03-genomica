// ─── GATK CombineGVCFs Module ───
// Input:  GVCF files from all samples (cohort)
// Output: Combined GVCF

process GATK_COMBINE {
    tag "cohort"

    input:
    path gvcfs
    path gvcf_tbis
    path fasta
    path dict

    output:
    path("cohort.g.vcf.gz"),  emit: gvcf
    path("cohort.g.vcf.gz.tbi"), emit: tbi

    script:
    def input_args = gvcfs.collect { "--variant ${it}" }.join(' ')
    """
    gatk CombineGVCFs \
        --reference ${fasta} \
        ${input_args} \
        --output cohort.g.vcf.gz
    """
}
