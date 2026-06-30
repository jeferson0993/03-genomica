// ─── Variant Calling Subworkflow ───
// Runs: HaplotypeCaller → CombineGVCFs → GenotypeGVCFs

include { GATK_HAPLOTYPECALLER } from '../modules/gatk_haplotypecaller'
include { GATK_COMBINE } from '../modules/gatk_combine'
include { GATK_GENOTYPE } from '../modules/gatk_genotype'

workflow VARIANT_CALL {
    take:
    bqsr_bams       // channel: [sample, bam, bai]
    ref_fasta       // path: reference FASTA
    ref_dict        // path: reference dict
    ref_dbsnp       // path: dbSNP VCF

    main:
    GATK_HAPLOTYPECALLER(bqsr_bams, ref_fasta, ref_dict, ref_dbsnp)

    // Collect all GVCFs for joint genotyping
    gvcfs_ch = GATK_HAPLOTYPECALLER.out.gvcf.collect()
    tbis_ch = GATK_HAPLOTYPECALLER.out.tbi.collect()

    GATK_COMBINE(gvcfs_ch, tbis_ch, ref_fasta, ref_dict)
    GATK_GENOTYPE(
        GATK_COMBINE.out.gvcf,
        GATK_COMBINE.out.tbi,
        ref_fasta, ref_dict, ref_dbsnp
    )

    emit:
    raw_vcf = GATK_GENOTYPE.out.vcf
    raw_vcf_tbi = GATK_GENOTYPE.out.tbi
}
