// ─── MultiQC Report Module ───
// Input:  All QC files (FastQC, bcftools stats, etc.)
// Output: MultiQC HTML report

process MULTIQC {
    tag "multiqc"

    input:
    path qc_files

    output:
    path("multiqc_report.html"), emit: report
    path("multiqc_data/"),       emit: data_dir

    script:
    """
    multiqc \
        --filename multiqc_report.html \
        --force \
        .
    """
}
