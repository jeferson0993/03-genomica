// ─── bcftools stats module ───
// Input:  Filtered VCF
// Output: VCF stats file

process BCFTOOLS_STATS {
    tag "cohort"

    input:
    path filtered_vcf

    output:
    path("cohort.vcf.stats"), emit: stats

    script:
    """
    bcftools stats ${filtered_vcf} > cohort.vcf.stats
    """
}
