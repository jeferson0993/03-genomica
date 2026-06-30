# Guia de Genômica Computacional

Baseado nos documentos: aulas de Python para genômica (Dan Andrews/ANU),
artigo Seq (Shajii et al., Nat. Biotechnol. 2021), tese PyGMQL (Luca Nanni,
Politecnico di Milano, 2017), tutorial Biopython v1.82, PyGenomics v0.1.1.

---

## Sumário

1. [Fundamentos de Genômica](#1-fundamentos-de-genômica)
2. [Dogma Central da Biologia Molecular](#2-dogma-central-da-biologia-molecular)
3. [Variação Genética](#3-variação-genética)
4. [Formatos de Dados Genômicos](#4-formatos-de-dados-genômicos)
5. [Medicina de Precisão](#5-medicina-de-precisão)
6. [Programação Python para Genômica](#6-programação-python-para-genômica)
7. [Ferramentas Clássicas de Genômica](#7-ferramentas-clássicas-de-genômica)
8. [Seq: Linguagem Python de Alto Desempenho para Genômica](#8-seq-linguagem-python-de-alto-desempenho-para-genômica)
9. [Biopython](#9-biopython)
10. [PyGMQL e a Linguagem Genométrica](#10-pygmql-e-a-linguagem-genométrica)
11. [Domínios Topologicamente Associados (TADs)](#11-domínios-topologicamente-associados-tads)
12. [Pipeline Completo de Análise Genômica](#12-pipeline-completo-de-análise-genômica)
13. [Referências](#13-referências)

---

## 1. Fundamentos de Genômica

A genômica é o estudo de todos os elementos que compõem o material genético
de um organismo. Diferentemente da genética clássica (que estuda genes
individuais), a genômica analisa o genoma como um todo: 3+ bilhões de bases
no caso humano.

### Por que a genômica importa?

- Essencial para **medicina de precisão**
- Melhor diagnóstico de doenças genéticas
- Diagnóstico melhor == terapias direcionadas
- Exemplos: tratamento de câncer, doenças genéticas raras

### O genoma como sistema de informação celular

```
Célula → Núcleo → Cromossomos → DNA & Nucleotídeos → Genes → Mutações & Variação → Doença
```

O genoma humano contém ~20.000 genes codificadores de proteínas, mas a
maior parte do DNA é não-codificante e desempenha funções regulatórias.

---

## 2. Dogma Central da Biologia Molecular

O Dogma Central descreve o fluxo da informação genética:

```
DNA → Transcrição → RNA → Tradução → Proteína
```

- **Replicação**: DNA → DNA (cópia do genoma)
- **Transcrição**: DNA → RNA (síntese de RNA mensageiro)
- **Tradução**: RNA → Proteína (síntese proteica nos ribossomos)
- **Expressão gênica**: processo pelo qual a informação de um gene é usada
  para sintetizar seu produto funcional (proteína ou RNA)

A expressão gênica é modificada por processos internos (enhancers,
promotores, silenciadores) e externos (câncer, drogas, ambiente).

---

## 3. Variação Genética

### SNPs e CNVs

- **SNP** (Single Nucleotide Polymorphism): variação de uma única base
- **CNV** (Copy Number Variation): variação no número de cópias de genes
- A variação genética humana é muito maior do que se pensava: em vez de
  99,9% idênticos, somos ~99% idênticos (10x mais diversos)

### Tipos de mutação

- **Substituição**: troca de um nucleotídeo
- **Inserção/Deleção** (indel): adição ou remoção de nucleotídeos
- **Rearranjo cromossômico**: translocações, inversões, duplicações

---

## 4. Formatos de Dados Genômicos

### Formato FASTA

```
>seq_id descrição opcional
ATCGATCGATCGATCGATCGTAGCTAGCTAGCTAGCTAGCT
ATCGATCGATCGATCGATCGATCGATCG
```

### Formato FASTQ

Armazena sequências + qualidade das bases:

```
@HWI-EAS209:5:58:5894:21141#ATCACG/1
TTAATTGGTAAATAAATCTCCTAATAGCTTAGATNTTACCTT...
+ HWI-EAS209:5:58:5894:21141#ATCACG/1
efcfffffcfeefffcffffffddf`feed]`]_Ba_^__[YBB...
```

- `@` — cabeçalho com identificador da sequência
- Sequência de nucleotídeos (A, T, C, G, N)
- `+` — separador (opcionalmente repete cabeçalho)
- Pontuação de qualidade (Phred score codificado em ASCII)

### Formato SAM/BAM

SAM (Sequence Alignment/Map) é texto; BAM é binário. Representa
sequências alinhadas contra um genoma de referência.

Cada linha contém: QNAME, FLAG, RNAME, POS, MAPQ, CIGAR, RNEXT, PNEXT,
TLEN, SEQ, QUAL.

### Formato VCF/BCF

VCF (Variant Call Format) armazena chamadas de variantes entre um genoma
pessoal e o de referência:

```
#CHROM  POS  ID        REF  ALT  QUAL  FILTER  INFO           FORMAT       Sample1
2       4370 rs6057    G    A    29     .      NS=2;DP=13     GT:GQ:DP:HQ  0|0:48:1:52,51
20      1106 rs6055    A    G,T  67     PASS   NS=2;DP=10;AF= GT:GQ:DP:HQ  1|2:21:6:23,27
```

- **CHROM/POS**: posição no genoma de referência
- **ID**: identificador dbSNP (se conhecido)
- **REF**: base de referência
- **ALT**: base(s) alternativa(s)
- **QUAL**: qualidade Phred
- **FILTER**: filtro aplicado (PASS, q10, etc.)
- **INFO**: informação adicional (profundidade, frequência alélica)
- **FORMAT**: formato dos dados genotípicos por amostra

---

## 5. Medicina de Precisão

A genômica é a base da medicina de precisão, mas atualmente só se resolve
30-40% dos casos. O problema é a ENORME quantidade de variação em cada
genoma humano.

### Abordagem computacional

1. Sequenciamento massivo (100k+ genomas)
2. Pipelines computacionais para analisar dados
3. Alinhadores e callers de variantes
4. Predição de efeitos funcionais da variação
5. Integração e anotação de dados
6. Priorização de mutações causadoras de doenças

---

## 6. Programação Python para Genômica

### Por que geneticistas precisam programar?

O geneticista moderno não consegue trabalhar sem processar informação. O
Projeto Genoma Humano não teria sido possível sem código para decifrar os
dados de sequenciamento.

### Por que orientação a objetos (OOP) é relevante?

- Estrutura, organização e reuso de código
- Bibliotecas como Biopython, PyGMQL, scikit-learn são implementadas como
  classes
- Código grande/complexo é melhor implementado com classes

### Classes vs Módulos

| Característica | Módulo | Classe |
|---|---|---|
| Importação de função | `import modulo` | `from classe import obj` |
| Múltiplas instâncias | Singleton apenas | Múltiplas instâncias |
| Passagem de dados | Muitos argumentos | Atributos do objeto |
| Contexto | Funções soltas | Métodos operam nos dados |

### Anatomia de uma classe

```python
class PacienteMutations:
    """Gerencia mutações de um paciente."""

    def __init__(self, patient_id, mutations_file):
        self.patient_id = patient_id
        self.mutations = self._load_mutations(mutations_file)

    def _load_mutations(self, filename):
        # Carrega CSV: gene_name,chromosome,coord,ref_nucl,var_nucl,...
        pass

    def filter_by_gene(self, gene_name):
        """Filtra mutações por gene."""
        return [m for m in self.mutations if m['gene'] == gene_name]

    def is_homozygous(self, mutation):
        return mutation['homozygous']
```

### Exemplo: Processamento de dados de mutações

Dados em CSV:
```csv
gene_name,chromosome,coord,ref_nucl,var_nucl,homozygous,essential_category,damage_score
BRCA1,17,41234567,A,T,True,essential,0.95
TP53,17,7579472,G,C,False,essential,0.88
```

---

## 7. Ferramentas Clássicas de Genômica

Ferramentas open-source mais comuns:

| Ferramenta | Função |
|---|---|
| **GATK** (Genome Analysis Toolkit) | Chamada de variantes, pós-processamento BAM |
| **SAMTools** | Manipulação de alinhamentos SAM/BAM |
| **BWA** (Burrows-Wheeler Aligner) | Alinhamento de reads ao genoma de referência |
| **VCFtools** | Filtragem e análise de VCF |
| **SpliceAI** | Predição de efeito de splicing |
| **VEP** (Variant Effect Predictor) | Anotação funcional de variantes |
| **BioMart** | Mineração de dados genômicos |
| **EnsEMBL** | Banco de dados genômico |
| **Bowtie** | Alinhamento rápido de reads curtos |
| **BLAST** | Busca de similaridade de sequências |
| **FastQC** | Controle de qualidade de FASTQ |
| **MultiQC** | Agregação de relatórios QC |
| **STAR** / **HISAT2** | Alinhamento de RNA-seq |

---

## 8. Seq: Linguagem Python de Alto Desempenho para Genômica

**Seq** (Shajii, Numanagić et al., MIT, 2021) é uma linguagem compilada
baseada em Python, especificamente projetada para genômica computacional.

### Conceito

```
Python (fácil, lento) ← → C/C++ (rápido, complexo)
                        ↑
                      SEQ
           (fácil + rápido, domínio-específico)
```

### Características

- **Sintaxe Python**: clara, concisa, amplamente adotada
- **Compilador com otimizações genômicas**: use construções de alto nível
  como sequências, k-mers, alinhamento — o compilador otimiza
  automaticamente
- **Interoperabilidade**: primeira-classe com C e Python
- **Performance**: até 10x mais rápido que implementações C/C++ originais
  em certas tarefas

### Exemplo: Mapeador de reads baseado em k-mer

```seq
# Seq code - um mapeador de reads simples
from seq import *

ref = sequence("reference.fa")
reads = sequence("reads.fq")

# O compilador Seq otimiza automaticamente o loop abaixo
for read in reads:
    for i in range(len(read) - kmer_len + 1):
        kmer = read[i:i+kmer_len]
        if kmer in ref_index:
            matches = ref_index[kmer]
            for pos in matches:
                # alinhamento local
                ...
```

### Ferramentas reimplementadas em Seq

| Ferramenta | Speedup | Linhas de código |
|---|---|---|
| BWA-MEM (SMEM) | 2-3x | 10x menos |
| minimap2 (long-read) | ~2x | 8x menos |
| mrsFAST (all-mapping) | 2-3x | 12x menos |
| GATK (pós-processamento) | ~5x | 15x menos |
| UMI-tools (single-cell) | ~10x | 10x menos |
| CORA (homology table) | ~3x | 8x menos |

---

## 9. Biopython

**Biopython** (v1.82, dez 2023) é a principal biblioteca Python para
biologia molecular computacional. Desenvolvida desde 2000 por voluntários
globais.

### Instalação

```bash
pip install biopython
```

### Principais módulos

#### 9.1. Seq — Objetos de sequência

```python
from Bio.Seq import Seq

seq = Seq("ATCGATCGATCG")
print(seq.complement())       # TCGATCGATCGA
print(seq.reverse_complement()) # CGATCGATCGAT
print(seq.transcribe())        # ATCGAUCGAUCG
print(seq.translate())         # Tradução para proteína
```

#### 9.2. SeqRecord — Sequências com anotação

```python
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

record = SeqRecord(
    Seq("ATCGATCGATCG"),
    id="gene_001",
    name="exemplo",
    description="Gene exemplo para demonstração",
)
print(record.id, record.seq)
```

#### 9.3. SeqIO — Leitura/escrita de arquivos

```python
from Bio import SeqIO

# Lendo FASTA
for record in SeqIO.parse("sequencias.fasta", "fasta"):
    print(record.id, len(record.seq))

# Lendo FASTQ com qualidade
for record in SeqIO.parse("reads.fastq", "fastq"):
    print(record.id, record.letter_annotations["phred_quality"])

# Lendo GenBank
genbank = SeqIO.read("gene.gb", "genbank")
print(genbank.features)

# Convertendo formatos
SeqIO.convert("entrada.fasta", "fasta", "saida.genbank", "genbank")

# Indexando arquivos grandes
index = SeqIO.index("grande.fasta", "fasta")
print(index["seq_id"].seq)
```

#### 9.4. Alinhamentos

```python
from Bio import Align

aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.match_score = 2
aligner.mismatch_score = -1
alignments = aligner.align("ATCGAT", "ATCGCT")
for aln in alignments:
    print(aln)
    print(aln.score)
```

#### 9.5. BLAST

```python
from Bio.Blast import NCBIWWW, NCBIXML

# BLAST pela internet
result = NCBIWWW.qblast("blastn", "nt", "ATCGATCGATCG")
records = NCBIXML.parse(result)
for record in records:
    for alignment in record.alignments:
        print(alignment.title)
```

#### 9.6. NCBI Entrez

```python
from Bio import Entrez

Entrez.email = "seu@email.com"  # obrigatório

# Buscar no PubMed
handle = Entrez.esearch(db="pubmed", term="genomics")
record = Entrez.read(handle)
print(record["IdList"])

# Buscar no Nucleotide
handle = Entrez.efetch(db="nucleotide", id="NM_001301717", rettype="fasta")
print(handle.read())
```

#### 9.7. Estruturas 3D (Bio.PDB)

```python
from Bio.PDB import PDBParser

parser = PDBParser()
structure = parser.get_structure("proteina", "1ubq.pdb")
for model in structure:
    for chain in model:
        for residue in chain:
            for atom in residue:
                print(atom.get_id(), atom.get_vector())
```

#### 9.8. Filogenética (Bio.Phylo)

```python
from Bio import Phylo

tree = Phylo.read("arvore.nwk", "newick")
Phylo.draw(tree)
```

#### 9.9. Motivos (Bio.motifs)

```python
from Bio import motifs
from Bio.Seq import Seq

instances = [Seq("TATAAA"), Seq("TATATA"), Seq("TATATT")]
motif = motifs.create(instances)
print(motif.consensus)
print(motif.counts)
```

#### 9.10. GenomeDiagram — Visualização

```python
from Bio.Graphics import GenomeDiagram
from Bio.SeqFeature import SeqFeature, FeatureLocation

gd = GenomeDiagram.Diagram("genoma")
track = gd.new_track(1, name="genes")
feature_set = track.new_set()
feature = SeqFeature(FeatureLocation(0, 100), type="gene")
feature_set.add_feature(feature)
gd.draw(format="linear")
gd.write("genoma.png", "PNG")
```

---

## 10. PyGMQL e a Linguagem Genométrica

**GMQL** (Genometric Query Language) é uma linguagem declarativa para
consulta e processamento de dados genômicos em larga escala, construída
sobre tecnologias big data (Apache Spark). Desenvolvida no Politecnico di
Milano.

**PyGMQL** é um pacote Python que encapsula o poder do GMQL em um
ambiente interativo.

### Conceitos GMQL

- **Dataset GMQL**: conjunto de amostras, cada uma com:
  - **Regions**: dados de regiões genômicas (chr, start, stop, strand)
  - **Metadata**: atributos descritivos (tissue, cell, antibody, etc.)
- **Operações**: SELECT, PROJECT, JOIN, MAP, COVER, UNION, DIFFERENCE, ORDER

### Arquitetura PyGMQL

```
Python Client (PyGMQL)
       ↕ Py4J bridge
Scala Back-end (GMQL engine)
       ↕ Spark
     Hadoop HDFS / S3
```

### Como usar PyGMQL

```python
import gmql as gl

# Modo remoto
gl.login(username="user", password="pass")
gl.set_mode("remote")

# Carregar dataset remoto
mut = gl.load(name="HG19_TCGA_dnaseq")
mut = mut[mut['dataType'] == 'dnaseq']

# Selecionar regiões
exon = gl.load(name="HG19_BED_ANNOTATION")
exon = exon[exon['annotation_type'] == 'exons']

# Mapear mutações para exons
exon1 = exon.map(experiment=mut)
exon2 = exon1.reg_select(exon1.count_Exon_Mut >= 1)
exon3 = exon2.extend({'exon_count': gl.COUNT()})
exon_res = exon3.order(meta=['exon_count'], meta_ascending=[0])

# Materializar (executar) a query
resultado = exon_res.materialize()

# Resultado em um GDataframe (estrutura dupla pandas)
# resultado.regs = tabela de regiões
# resultado.meta = tabela de metadados
```

### GDataframe

Estrutura de dados de saída do PyGMQL, composta por dois DataFrames
Pandas:

- **Regions**: uma linha por região genômica, colunas `chr`, `start`, `stop`, etc.
- **Metadata**: uma linha por amostra, colunas com atributos descritivos
- As duas tabelas são ligadas pelo `sample id`

### Modo Local vs Remoto

| Modo | Execução | Uso |
|---|---|---|
| **Local** | Máquina local | Dados pequenos/médios, prototipagem |
| **Remoto** | Servidor Spark GMQL | Grandes volumes, produção |

### Operações GMQL

```python
# Seleção de metadados
dataset = dataset[dataset['tissue'] == 'brain']

# Projeção de atributos
dataset = dataset.select(meta_attributes=['tissue', 'cell'])

# Extensão com novos campos
dataset = dataset.extend({'gene_count': gl.COUNT()})

# JOIN genométrico (distância, contiguidade)
join_dataset = left.join(
    experiment=right,
    genometric_condition=[gl.DLE(100000), gl.MD(1)]
)

# MAP
mapped = left.map(experiment=right, new_reg_fields={'count': gl.COUNT()})

# COVER (regiões cobertas por N amostras)
covered = dataset.cover(minAcc=2, maxAcc=10)

# Materialização
dataset.materialize(output_path="./resultado/")
```

### Pipeline GMQL completa

```python
import gmql as gl
import pandas as pd

# Carregar dados de genes (arquivo TSV local)
genes = pd.read_csv("genes.tsv", sep="\t")
genes_ds = gl.from_pandas(genes).to_GMQLDataset()

# Carregar TADs
tads = gl.load_from_path("./tads/", parser=gl.parsers.BedParser(
    chrPos=0, startPos=1, stopPos=2, delimiter="\t"
))

# Selecionar linhagem celular
imr90 = tads[tads['cell'] == 'IMR90']

# Mapear genes para TADs
mapped = genes_ds.map(
    experiment=imr90,
    genometric_predicate=[gl.DLE(0)],
    new_reg_fields={'genes': gl.BAG("gene_name")}
)

# Materializar
result = mapped.materialize()
print(result.regs.head())
```

---

## 11. Domínios Topologicamente Associados (TADs)

TADs são regiões genômicas dentro das quais as interações físicas ocorrem
com frequência muito maior do que entre regiões diferentes. São uma
"sumarização" da conformação 3D do genoma.

### Descoberta via Hi-C

1. Cross-link da cromatina (conecta partes de DNA espacialmente próximas)
2. Corte do DNA em bins (resolução típica: 40 kb)
3. Ligação das pontas soltas do DNA cross-linkado
4. Sequenciamento paired-end para identificar pares

Resultado: matriz I onde I_ij = número de interações entre bin i e bin j.

### Propriedades dos TADs

- Tamanho: de milhares a milhões de bases
- **Boundaries** (fronteiras entre TADs): associadas a sítios de início de
  transcrição (TSS) e sítios de ligação CTCF
- TADs são conservados entre espécies (~60% de sobreposição humano-mouse)
- Genes dentro do mesmo TAD têm correlação de expressão mais alta que
  genes em TADs diferentes

### Correlação de expressão dentro vs entre TADs

```python
import gmql as gl
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# 1. Carregar TADs e coordenadas de genes
tads = gl.load_from_path("./tads_dixon/", parser=tads_parser)
genes = gl.load_from_path("./coords/", parser=coords_parser)

# 2. Selecionar linhagem
imr90 = tads[tads['cell'] == 'IMR90']

# 3. Mapear genes para TADs
mapped = genes.map(experiment=imr90).materialize()

# 4. Para cada TAD, calcular correlação média entre pares de genes
regs = mapped.regs
tad_groups = regs.groupby('sample_id')

same_corrs = []
for tad_id, group in tad_groups:
    genes_in_tad = group['gene'].tolist()
    if len(genes_in_tad) < 2:
        continue
    # Extrair expressão dos genes
    expr = expression_data[genes_in_tad]
    # Calcular correlação média
    corr_matrix = expr.T.corr()
    mean_corr = (corr_matrix.sum().sum() - len(corr_matrix)) / \
                (len(corr_matrix) * (len(corr_matrix) - 1))
    same_corrs.append(mean_corr)

print(f"Correlação média intra-TAD: {np.mean(same_corrs):.3f}")
```

### TADs em tecidos normais vs tumorais

Em todos os cânceres estudados, a correlação de expressão gênica AUMENTA
sistematicamente em relação ao tecido normal:

| Tumor | Tecido | Δ Correlação (tumor − normal) |
|---|---|---|
| THCA | Tireoide | +0,013 |
| PRAD | Próstata | +0,052 |
| BLCA | Bexiga | +0,055 |
| KIRP | Rim | +0,061 |
| LIHC | Fígado | +0,063 |
| BRCA | Mama | +0,064 |
| COAD | Cólon | +0,094 |
| KICH | Rim | +0,124 |

### Conservação de TADs entre espécies

- 178.324 pares de genes possíveis em TADs humanos
- 105.105 pares confirmados também em TADs de camundongo
- **~60% de sobreposição** — TADs são estruturas genômicas conservadas
- A correlação same/cross se mantém ao usar TADs de camundongo com
  expressão humana

### Clustering de TADs

#### Por expressão gênica

1. Matriz de expressão E (genes × pacientes), normalizada RPKM + log10
2. Mapear genes para TADs → média por TAD → matriz X (TADs × pacientes)
3. Z-score por linha (TAD)
4. Clustering hierárquico (Ward, distância euclidiana)
5. Resultado: ~25 clusters, majoritariamente inter-cromossômicos

#### Por conexões ChIA-PET

1. Grafo de vértices ChIA-PET × TADs
2. Matrix de adjacência Y (TAD × TAD) com pesos = número de ligações
3. Algoritmo Louvain para detecção de comunidades
4. Clusters com baixo p-value indicam forte correlação de expressão na
   rede ChIA-PET

---

## 12. Pipeline Completo de Análise Genômica

### Fluxo típico WGS (Whole Genome Sequencing)

```
FASTQ (reads brutos)
    │
    ▼
FastQC + MultiQC (controle de qualidade)
    │
    ▼
BWA-MEM (alinhamento ao genoma de referência)
    │
    ▼
SAMTools sort/index (BAM ordenado)
    │
    ▼
GATK MarkDuplicates (remoção de duplicatas)
    │
    ▼
GATK BQSR (calibração de qualidade de base)
    │
    ▼
GATK HaplotypeCaller (chamada de variantes em GVCF)
    │
    ▼
GATK CombineGVCFs + GenotypeGVCFs (genotipagem conjunta)
    │
    ▼
GATK VQSR / VariantFiltration (filtragem)
    │
    ▼
VCF filtrado + bcftools stats + MultiQC
```

### Boas práticas

1. **QC obrigatório**: FastQC + MultiQC antes de qualquer análise
2. **Imutabilidade**: dados brutos nunca são alterados
3. **Reprodutibilidade**: sementes aleatórias fixas, parâmetros documentados
4. **Containers**: usar imagens oficiais (Broad GATK, biocontainers)
5. **Versionamento**: registrar versão de cada ferramenta e referência
6. **Metadados**: todo arquivo deve ter metadados JSON (source, date, version)

### Ferramentas e containers

| Ferramenta | Imagem Docker |
|---|---|
| BWA-MEM | `biocontainers/bwa` |
| GATK4 | `broadinstitute/gatk` |
| FastQC | `staphb/fastqc` |
| MultiQC | `multiqc/multiqc` |
| Picard/SAMTools | `biocontainers/samtools` |

### API REST para orquestração de pipelines (FastAPI)

```python
# POST /runs — disparar pipeline
@app.post("/runs")
async def create_run(samplesheet: str, reference: str, name: str):
    run = PipelineRun(
        name=name,
        status="pending",
        samplesheet_path=samplesheet,
        reference=reference,
    )
    db.add(run)
    await db.commit()
    # Disparar worker via subprocess
    subprocess.Popen([
        "docker", "compose", "exec", "worker",
        "nextflow", "run", "pipeline/main.nf",
        "-params-file", f"params_{run.id}.json"
    ])
    return run

# GET /runs/{id} — consultar status
@app.get("/runs/{run_id}")
async def get_run(run_id: UUID):
    run = await db.get(PipelineRun, run_id)
    return run
```

---

## 13. Referências

1. **Dan Andrews** — *Reusable Python Code for Genomics* (ANU). Slides de aula.
2. **Shajii, Numanagić et al.** — *Seq: A Python-based programming language
   for high-performance computational genomics*. Nat. Biotechnol. 39,
   1062–1064 (2021). doi:10.1038/s41587-021-00985-6
3. **Luca Nanni** — *A Python Data Analysis Library for Genomics and its
   Application to Biology*. Tese de Mestrado, Politecnico di Milano (2017).
4. **Cock et al.** — *Biopython: freely available Python tools for
   computational molecular biology and bioinformatics*. Bioinformatics 25,
   1422–1423 (2009). doi:10.1093/bioinformatics/btp163
5. **Tiago Antao** — *PyGenomics* (v0.1.1). Documentação.
6. **Dixon et al.** — *Topological domains in mammalian genomes identified
   by analysis of chromatin interactions*. Nature 485, 376–380 (2012).
7. **Rao et al.** — *A 3D map of the human genome at kilobase resolution
   reveals principles of chromatin looping*. Cell 159, 1665–1680 (2014).
8. **McKenna et al.** — *The Genome Analysis Toolkit: a MapReduce framework
   for analyzing next-generation DNA sequencing data*. Genome Res. 20,
   1297–1303 (2010).
9. **Li H.** — *Aligning sequence reads, clone sequences and assembly
   contigs with BWA-MEM*. arXiv:1303.3997 (2013).
10. **Masseroli et al.** — *Genometric Query Language: a novel approach to
    large-scale genomic data management*. Bioinformatics 31, 1881–1888 (2015).
11. **Blondel et al.** — *Fast unfolding of communities in large networks*.
    J. Stat. Mech. P10008 (2008).
12. **Lieberman-Aiden et al.** — *Comprehensive mapping of long-range
    interactions reveals folding principles of the human genome*. Science
    326, 289–293 (2009).
