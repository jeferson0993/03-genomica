export interface PipelineRun {
  id: string;
  name: string;
  status: "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
  samplesheet_path: string;
  reference: string;
  params: Record<string, unknown> | null;
  nextflow_run_id: string | null;
  output_dir: string | null;
  report_path: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  datalake_dataset_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReferenceGenome {
  id: string;
  name: string;
  species: string;
  fasta_path: string;
  bwa_index_prefix: string | null;
  dbsnp_path: string | null;
  known_indels_path: string | null;
  gtf_path: string | null;
  minio_prefix: string | null;
  is_default: boolean;
  created_at: string;
}
