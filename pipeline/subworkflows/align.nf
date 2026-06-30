// ─── Align Subworkflow ───
// Runs: FastQC → BWA-MEM → MarkDuplicates → BQSR

include { FASTQC } from '../modules/fastqc'
include { BWA_ALIGN } from '../modules/bwa_align'
include { GATK_MARKDUPLICATES } from '../modules/gatk_dedup'
include { GATK_BQSR } from '../modules/gatk_bqsr'

workflow ALIGN {
    take:
    reads           // channel: [sample, fastq_1, fastq_2]
    bwa_index       // path: BWA index prefix
    ref_fasta       // path: reference FASTA
    ref_dict        // path: reference dict
    ref_dbsnp       // path: dbSNP VCF
    ref_known_indels // path: known indels VCF

    main:
    FASTQC(reads)
    BWA_ALIGN(reads, bwa_index, ref_fasta)
    GATK_MARKDUPLICATES(BWA_ALIGN.out.alignment)
    GATK_BQSR(
        GATK_MARKDUPLICATES.out.bam,
        ref_fasta, ref_dict, ref_dbsnp, ref_known_indels
    )

    emit:
    bqsr_bam = GATK_BQSR.out.bam     // recalibrated BAM per sample
    fastqc_html = FASTQC.out.html     // QC reports
    dedup_metrics = GATK_MARKDUPLICATES.out.metrics
}
