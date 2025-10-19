# Title/Abstract Screening Summary
**Speech Translation Systems - Systematic Literature Review**

Date: October 18, 2025  
Project: speech-translation-systems (ID: 1)  
Review Stage: Title/Abstract Screening - COMPLETE ✅

---

## Executive Summary

**Title/Abstract screening is now complete for all 104 papers in the corpus.**

| Metric | Value |
|--------|-------|
| **Total Papers Screened** | 104 |
| **Papers Included** | 55 (52.9%) |
| **Papers Excluded** | 49 (47.1%) |
| **Advance to Full-Text Screening** | 55 |

---

## Screening Results by Batch

### Batch 1: Papers 451-442 (n=10)
- **Included:** 7 papers (70%)
- **Excluded:** 3 papers (30%)
- **Quality:** High - substantive papers and conference proceedings headers
- **Confidence (avg):** 0.89

**Included Papers:**
- PROCEEDINGS OF THE 19TH INTERNATIONAL CONFERENCE ON SPOKEN LANGUAGE TRANSLATION (IWSLT 2022)
- MLLP-VRAIN UPV systems for the IWSLT 2022 Simultaneous Speech Translation and Speech-to-Speech Translation tasks
- Talklingo: A Smart Solution for Multilingual Communication
- Direct Speech to Speech Translation: A Review
- Towards Simultaneous Machine Interpretation
- KAME: Tandem Architecture for Enhancing Knowledge in Real-Time Speech-to-Speech Conversational AI
- Design and implementation of an AI-based wireless real-time voice translation system with directional audio output

**Excluded Papers:**
- Perspectives sobre la traducció automàtica de la parla (Catalan - non-English)
- O-COCOSDA conference header (metadata artifact)
- Non-research content

---

### Batch 2: Papers 440-418 (n=20)
- **Included:** 4 papers (20%)
- **Excluded:** 16 papers (80%)
- **Quality:** Low - heavy concentration of conference headers and metadata artifacts
- **Confidence (avg):** 0.77

**Data Quality Issue Identified:**
This batch revealed a significant problem: ~80% were generic conference proceeding headers rather than actual research papers. These include:
- IEEE SLT 2024
- INTERSPEECH 2021
- AACL-IJCNLP 2020
- ACL 2022
- And many others from various IEEE conferences (ICFTIC, IMSA, ICCCNT, etc.)

**Included Papers:**
- Simultaneous Speech-to-Speech Translation System with Neural Incremental ASR, MT, and TTS
- Neural Incremental Speech Recognition Toward Real-Time Machine Speech Translation
- Jointly Trained Transformers models for Spoken Language Translation
- Evaluating Gender Bias in Speech Translation

---

### Batch 3: Papers 417-360 (n=25)
- **Included:** 18 papers (72%)
- **Excluded:** 7 papers (30%)
- **Quality:** High - IWSLT-focused, substantive systems papers
- **Confidence (avg):** 0.93

**Included Papers (Highlight):**
- FST: the FAIR Speech Translation System for the IWSLT21 Multilingual Shared Task
- ESPnet-ST IWSLT 2021 Offline Speech Translation System
- The Volctrans Neural Speech Translation System for IWSLT 2021
- Blending LLMs into Cascaded Speech Translation: KIT's Offline Speech Translation System for IWSLT 2024
- KIT's Multilingual Speech Translation System for IWSLT 2023
- User-Oriented EFL Speaking through Application and Exercise: Instant Speech Translation and Shadowing in Authentic Context

---

### Batch 4: Papers 358-1 (n=49)
- **Included:** 26 papers (53%)
- **Excluded:** 23 papers (47%)
- **Quality:** Mixed - blend of high-quality recent papers and metadata artifacts
- **Confidence (avg):** 0.88

**Notable Included Papers:**
- Streaming Simultaneous Speech Translation with Augmented Memory Transformer (RQ3)
- SimulMT to SimulST: Adapting Simultaneous Text Translation to End-to-End Simultaneous Speech Translation
- Direct speech-to-speech translation with discrete units (RQ1)
- Long-Form End-to-End Speech Translation via Latent Alignment Segmentation
- USYD-JD Speech Translation System for IWSLT 2021
- BeaverTalk: Oregon State University's IWSLT 2025 Simultaneous Speech Translation System (Latest 2025)
- Multilingual Simultaneous Speech Translation (RQ5)
- Efficient and Adaptive Simultaneous Speech Translation with Fully Unidirectional Architecture (RQ3)
- Dragoman AI: Real-Time Speech Translation for Educational Applications
- Open Source Toolkit for Speech-to-Text Translation
- Breaking the Data Barrier: Towards Robust Speech Translation via Adversarial Stability Training (RQ4)
- Blockwise Streaming Transformer for Spoken Language Understanding and Simultaneous Speech Translation
- SASST: Leveraging Syntax-Aware Chunking and LLMs for Simultaneous Speech Translation
- SimulMEGA: MoE Routers are Advanced Policy Makers for Simultaneous Speech Translation
- UnitY: Two-pass Direct Speech-to-speech Translation with Discrete Units (RQ1)
- SimulTron: On-Device Simultaneous Speech-to-Speech Translation
- Speech-to-Speech Translation with Discrete-Unit-Based Style Transfer
- DASpeech: Directed Acyclic Transformer for Fast and High-quality Speech-to-Speech Translation
- Diffusion Synthesizer for Efficient Multilingual Speech-to-Speech Translation
- Analyzing Speech Unit Selection for Textless Speech-to-Speech Translation
- Survey On Monolingual Speech-to-Speech Translation
- Tibetan–Chinese speech-to-speech translation based on discrete units (RQ5)

---

## Papers Advancing to Full-Text Screening

### By Research Question Coverage

**RQ1: Main approaches/architectures**
- Direct speech-to-speech translation approaches (8 papers)
- Discrete unit-based systems (UnitY, SimulTron, etc.)
- Transformer-based architectures (Streaming, DASpeech, etc.)
- Cascaded vs. end-to-end systems

**RQ2: Performance metrics and evaluation**
- Gender bias evaluation papers
- Benchmark papers (IWSLT systems)
- Robustness and adversarial training approaches

**RQ3: Real-time and latency handling**
- Streaming architectures (Augmented Memory Transformer)
- Simultaneous translation systems
- On-device implementations (SimulTron)
- Efficient unidirectional architectures

**RQ4: Challenges and limitations**
- Data barrier/robustness training
- Disfluency detection
- Quality and coverage concerns

**RQ5: Languages and language pairs**
- Multilingual systems
- Specific language pairs (Tibetan-Chinese, etc.)
- EFL applications
- Multilingual educational tools

---

## Key Themes in Included Papers

### 1. System Descriptions (IWSLT Shared Tasks)
Multiple papers describe state-of-the-art systems from major labs:
- **Meta/FAIR:** FST system for IWSLT21
- **CMU/KIT:** Multiple systems for IWSLT 2023-2024
- **University of Tokyo/NAIST:** ESPnet-ST system
- **University of Stuttgart:** Volctrans system
- **University of Sydney:** USYD-JD system
- **USTC/NELSLIP:** Simultaneous translation system
- **Oregon State:** BeaverTalk system for IWSLT 2025
- Plus many others (KIT, CMU, MLLP-VRAIN UPV, etc.)

### 2. Novel Approaches
- **Discrete units:** UnitY, Direct speech-to-speech with discrete units
- **Style transfer:** Discrete-unit-based style transfer
- **Diffusion models:** Diffusion Synthesizer for speech synthesis
- **LLM integration:** SASST (Syntax-Aware with LLMs)
- **MoE routing:** SimulMEGA with mixture-of-experts routers
- **DAG transformers:** DASpeech with directed acyclic graphs

### 3. Efficiency & Real-Time
- Blockwise streaming transformers
- On-device translation (SimulTron)
- Unidirectional architectures
- Latent alignment segmentation
- Augmented memory transformers

### 4. Applications
- Educational applications (EFL speaking, Dragoman AI)
- Real-time conversation systems (Talklingo, KAME)
- Wireless systems with directional audio
- Institutional implementations

### 5. Multilingual Coverage
- Multiple IWSLT systems supporting 10+ language pairs
- Specific low-resource pairs (Tibetan-Chinese)
- Multilingual end-to-end approaches

### 6. Quality & Robustness
- Gender bias evaluation in speech translation
- Adversarial stability training
- Survey on speech translation systems
- Evaluation frameworks and metrics

---

## Data Quality Findings

### Issues Identified
1. **Metadata Artifacts:** ~25-30% of database entries are conference headers, not actual papers
   - Example: "INTERSPEECH 2022" listed as paper title
   - Distributed across batches but concentrated in Batch 2
   
2. **Non-English Papers:** At least 1 paper in Catalan language (excluded appropriately)

3. **Non-Research Content:** At least 1 entry was travel writing ("Into the heart of coffee country")

### Recommendations for Future Uploads
- Implement stricter BibTeX parsing to filter conference headers
- Add language detection filter before import
- Validate that entries contain title, author, and abstract fields
- Remove entries with invalid abstracts or content types

---

## Next Steps: Full-Text Screening

### Preparation Phase
1. **Generate full texts:** Retrieve PDFs or abstracts for all 55 included papers
2. **Quality assessment framework:** Define criteria for full-text review
3. **Define screening protocol:** Detailed full-text evaluation rubric
4. **Reviewer training:** Brief reviewers on domain-specific criteria

### Full-Text Screening Phase
1. **Stage:** Full-Text Review
2. **Reviewers:** researcher_01 (and potentially second reviewer for conflict resolution)
3. **Criteria:** Detailed inclusion/exclusion criteria for full-text level
4. **Output:** ~40-45 papers expected to advance to quality assessment

### Estimated Timeline
- Full-text screening: 2-3 weeks
- Quality assessment: 2-3 weeks
- Data extraction: 3-4 weeks
- Synthesis and analysis: 2-3 weeks
- Final report: 1-2 weeks

---

## Statistics Summary

### Inclusion Rates by Batch
```
Batch 1: ████████░ 70%
Batch 2: ██░░░░░░░ 20%
Batch 3: ███████░░ 72%
Batch 4: █████░░░░ 53%
─────────────────
Overall: █████░░░░ 52.9%
```

### Confidence Levels
- **High confidence (0.90-0.98):** 38 papers (69%)
- **Medium confidence (0.75-0.89):** 17 papers (31%)
- **Low confidence (< 0.75):** 0 papers (0%)

### Publication Year Distribution
- **2025:** 11 papers (20%) - Recent work, latest approaches
- **2024:** 6 papers (11%) - Current systems, IWSLT 2024
- **2023:** 5 papers (9%) - IWSLT 2023, established systems
- **2022:** 6 papers (11%) - IWSLT 2022, ICASSP
- **2021:** 14 papers (25%) - IWSLT 2021, ESPnet-ST, FST
- **2020:** 9 papers (16%) - Earlier work, foundational
- **2019:** 2 papers (4%) - Prior work
- **2018:** 1 paper (2%) - Older work
- **2015:** 1 paper (2%) - Earliest work

### Exclusion Reasons
- **Conference headers (metadata artifacts):** 31 papers (63% of exclusions)
- **Text-only translation:** 4 papers (8%)
- **Other domains:** 8 papers (16%)
- **Non-research/misc:** 6 papers (13%)

---

## Documentation Generated

1. ✅ **Title/Abstract Screening Report** (PRISMA-compliant)
   - File: `title-abstract-screening-report.md.markdown`
   - Includes: Study characteristics, citation analysis, evidence synthesis
   - Size: 25.4 KB

2. ✅ **Screening Summary** (This document)
   - Batch-by-batch analysis
   - Key themes and findings
   - Next steps and recommendations

3. ✅ **Research Questions** (Already documented)
   - File: `research-questions.md`

---

## Recommendations for Full-Text Phase

### Priority 1: IWSLT System Papers (High Relevance)
Focus on papers describing systems from major research institutions. These directly address RQ1 (approaches/architectures) and represent state-of-the-art work.

### Priority 2: Novel Approaches (High Innovation)
Papers presenting new architectures (Diffusion Synthesizer, SimulMEGA, DASpeech) offer insights into evolving approaches.

### Priority 3: Evaluation & Quality (RQ2, RQ4)
Papers on gender bias, robustness, and adversarial training address evaluation frameworks and challenge identification.

### Priority 4: Practical Applications (RQ3, RQ5)
Papers on real-time systems, multilingual support, and specific applications address efficiency and language coverage.

### Priority 5: Surveys & Reviews (Synthesis)
The monolingual speech-to-speech translation survey provides valuable overview and comparison of approaches.

---

## Conclusion

**Status: Title/Abstract Screening Successfully Completed**

✅ 55 papers advance to full-text screening  
✅ All research questions represented in included papers  
✅ Good diversity of paper types (systems, evaluations, approaches, applications)  
✅ Strong temporal coverage (2015-2025, concentrated in 2020-2025)  
✅ Data quality issues identified for future process improvement  

**Ready to proceed to full-text screening phase.**

