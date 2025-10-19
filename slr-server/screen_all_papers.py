#!/usr/bin/env python3
"""
Comprehensive screening analysis for all 104 deduplicated papers.
Retrieves abstracts and applies inclusion/exclusion criteria to determine
which papers should advance to full-text screening phase.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.container import Container
from src.handlers.mcp_handler import SLRMCPHandler
from mcp.types import TextContent


class PaperScreener:
    """Analyzes papers against SLR screening criteria."""
    
    # Inclusion criteria keywords
    INCLUSION_CRITERIA = {
        "IC1_EMPIRICAL": ["empirical", "experiment", "evaluation", "dataset", "benchmark", "study", "test", "measure", "assess"],
        "IC2_ARCHITECTURE": ["architecture", "design", "platform", "system", "framework", "pipeline", "module", "component"],
        "IC3_REALTIME": ["real-time", "real time", "realtime", "simultaneous", "low-latency", "latency", "streaming"],
        "IC4_MULTILINGUAL": ["multilingual", "multi-lingual", "language pair", "pairs", "bilingual", "cross-lingual"],
        "IC5_NEURAL": ["neural", "deep learning", "transformer", "lstm", "rnn", "cnn", "attention", "embedding"],
        "IC6_SCALABILITY": ["scalable", "scale", "efficient", "performance", "throughput", "capacity", "distributed"],
        "IC7_EVALUATION": ["evaluate", "metric", "bleu", "comparison", "baseline", "result", "performance"],
        "IC8_PEERREVIEWED": ["conference", "journal", "proceedings", "published", "peer-reviewed", "proceedings"]
    }
    
    # Exclusion criteria keywords
    EXCLUSION_CRITERIA = {
        "EC1_STATISTICAL": ["statistical mt", "phrase-based", "smt", "moses", "statistical machine translation"],
        "EC2_TEXTONLY": ["text translation", "machine translation", "mt model"],  # Without speech component
        "EC3_INSUFFICIENT": ["survey", "review", "overview", "summary", "literature"],  # Without empirical evaluation
        "EC4_QUALITY": ["preliminary", "draft", "work in progress", "incomplete"],
        "EC5_THEORETICAL": ["theoretical", "conceptual", "proposal", "idea"],  # Without evaluation
        "EC6_OUTOFSCOPE": ["sign language", "gesture", "emotion", "voice", "speaker"],  # Non-speech translation
        "EC7_GRAYLITERATURE": ["thesis", "dissertation", "report", "white paper"],
        "EC8_NOACCESS": ["abstract only", "no full text", "summary not available"]
    }
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.container: Optional[Container] = None
        self.handler: Optional[SLRMCPHandler] = None
        
    async def initialize(self):
        """Initialize container and handler."""
        print("📦 Initializing screening system...")
        self.container = Container(
            database_path="database/slr_database.db",
            project_root=Path(__file__).parent
        )
        await self.container.initialize()
        self.handler = self.container.get_mcp_handler()
        print("✅ System initialized")
    
    async def get_paper_info(self, paper_id: int) -> Dict[str, Any]:
        """Get paper information via get_paper handler."""
        try:
            if not self.handler:
                return {"error": True, "message": "Handler not initialized"}
            
            result = await self.handler.handle_get_paper({"paper_id": paper_id})
            
            if result.isError:
                return {"error": True, "message": "Paper not found"}
            
            # Extract text from result
            if result.content and isinstance(result.content[0], TextContent):
                return {
                    "error": False,
                    "text": result.content[0].text
                }
            return {"error": True, "message": "Invalid response format"}
        
        except Exception as e:
            return {"error": True, "message": str(e)}
    
    def parse_paper_sections(self, full_text: str) -> Dict[str, str]:
        """Extract paper sections from full text response."""
        sections = {
            "title": "",
            "authors": "",
            "year": "",
            "abstract": "",
            "keywords": "",
            "full_text": ""
        }
        
        lines = full_text.split("\n")
        current_section = None
        current_content = []
        
        for line in lines:
            if "**Title:**" in line:
                sections["title"] = line.split("**Title:**")[1].strip() if "**Title:**" in line else ""
            elif "**Authors:**" in line:
                sections["authors"] = line.split("**Authors:**")[1].strip() if "**Authors:**" in line else ""
            elif "**Year:**" in line:
                sections["year"] = line.split("**Year:**")[1].strip() if "**Year:**" in line else ""
            elif line.startswith("--- ABSTRACT"):
                current_section = "abstract"
                current_content = []
            elif line.startswith("--- KEYWORDS"):
                if current_section == "abstract" and current_content:
                    sections["abstract"] = "\n".join(current_content).strip()
                current_section = "keywords"
                current_content = []
            elif line.startswith("--- FULL TEXT"):
                if current_section == "keywords" and current_content:
                    sections["keywords"] = "\n".join(current_content).strip()
                current_section = "full_text"
                current_content = []
            elif line.startswith("--- METADATA"):
                if current_section == "full_text" and current_content:
                    sections["full_text"] = "\n".join(current_content).strip()
                break
            elif current_section and line.strip():
                current_content.append(line)
        
        return sections
    
    def check_inclusion_criteria(self, text: str) -> Dict[str, bool]:
        """Check which inclusion criteria are met."""
        text_lower = text.lower()
        results = {}
        
        for criterion, keywords in self.INCLUSION_CRITERIA.items():
            met = any(keyword in text_lower for keyword in keywords)
            results[criterion] = met
        
        return results
    
    def check_exclusion_criteria(self, text: str) -> Tuple[Dict[str, bool], str]:
        """Check which exclusion criteria are met."""
        text_lower = text.lower()
        results = {}
        matched_reason = ""
        
        for criterion, keywords in self.EXCLUSION_CRITERIA.items():
            met = any(keyword in text_lower for keyword in keywords)
            results[criterion] = met
            if met and not matched_reason:
                matched_reason = criterion
        
        return results, matched_reason
    
    def make_decision(self, title: str, abstract: str, inclusion: Dict, exclusion: Dict, exclusion_reason: str) -> Tuple[str, float, str]:
        """Make screening decision based on criteria."""
        # Count criteria met
        inclusion_count = sum(1 for v in inclusion.values() if v)
        exclusion_count = sum(1 for v in exclusion.values() if v)
        
        combined_text = (title + " " + abstract).lower()
        
        # Strong exclusion rules
        if exclusion_reason or exclusion_count > 0:
            # Check if it's actually about speech translation
            speech_terms = ["speech", "s2st", "speech-to-speech", "asr", "speech translation", "transcription"]
            has_speech = any(term in combined_text for term in speech_terms)
            
            if not has_speech:
                return "EXCLUDE", 0.95, f"Not about speech translation: {exclusion_reason}"
        
        # Must have some inclusion criteria
        if inclusion_count == 0:
            return "EXCLUDE", 0.90, "Does not meet inclusion criteria"
        
        # Strong inclusion: meets multiple criteria and no exclusions
        if inclusion_count >= 4 and exclusion_count == 0:
            return "INCLUDE", 0.95, f"Meets {inclusion_count} inclusion criteria"
        
        # Moderate inclusion: meets several criteria
        if inclusion_count >= 3 and exclusion_count == 0:
            return "INCLUDE", 0.85, f"Meets {inclusion_count} inclusion criteria"
        
        # Borderline: meets criteria but some concerns
        if inclusion_count >= 2 and exclusion_count <= 1:
            return "INCLUDE", 0.70, f"Meets {inclusion_count} criteria but {exclusion_count} exclusion concern"
        
        # Uncertain: unclear from abstract
        if inclusion_count >= 1:
            return "UNCERTAIN", 0.55, "Limited information in abstract, needs full-text review"
        
        return "EXCLUDE", 0.80, "Insufficient information for inclusion"
    
    async def screen_all_papers(self):
        """Screen all papers in the database."""
        if not self.container:
            print("❌ Container not initialized")
            return
        
        paper_repository = self.container.get_paper_repository()
        
        # Get all papers
        print("\n📋 Retrieving all 104 unique papers...")
        papers = paper_repository.list_papers(limit=104, offset=0)
        
        if not papers:
            print("❌ No papers found!")
            return
        
        print(f"✅ Found {len(papers)} papers to screen")
        print("\n" + "=" * 100)
        print("🔍 SCREENING PAPERS FOR INCLUSION/EXCLUSION")
        print("=" * 100)
        
        # Screen each paper
        for i, paper in enumerate(papers, 1):
            if i % 10 == 0:
                print(f"\n⏳ Processing paper {i}/{len(papers)}...")
            
            if paper.id is None:
                continue
            
            # Get paper info
            paper_info = await self.get_paper_info(paper.id)
            
            if paper_info.get("error"):
                decision_result = {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "decision": "EXCLUDE",
                    "confidence": 0.5,
                    "reason": "Could not retrieve paper information",
                    "inclusion_criteria": {},
                    "exclusion_criteria": {},
                    "exclusion_reason": "RETRIEVAL_ERROR"
                }
            else:
                # Parse sections
                sections = self.parse_paper_sections(paper_info["text"])
                
                # Check criteria
                inclusion_results = self.check_inclusion_criteria(sections["abstract"])
                exclusion_results, exclusion_reason = self.check_exclusion_criteria(sections["abstract"])
                
                # Make decision
                decision, confidence, reason = self.make_decision(
                    sections.get("title", paper.title),
                    sections.get("abstract", ""),
                    inclusion_results,
                    exclusion_results,
                    exclusion_reason
                )
                
                decision_result = {
                    "paper_id": paper.id,
                    "title": sections.get("title", paper.title),
                    "year": sections.get("year", paper.publication_year),
                    "decision": decision,
                    "confidence": confidence,
                    "reason": reason,
                    "abstract": sections.get("abstract", "")[:300] + "..." if sections.get("abstract") else "[No abstract]",
                    "inclusion_criteria": inclusion_results,
                    "exclusion_criteria": exclusion_results,
                    "exclusion_reason": exclusion_reason
                }
            
            self.results.append(decision_result)
        
        print("\n" + "=" * 100)
        print("✅ SCREENING COMPLETE")
        print("=" * 100)
    
    def generate_report(self) -> str:
        """Generate comprehensive screening report."""
        # Calculate statistics
        include_count = sum(1 for r in self.results if r["decision"] == "INCLUDE")
        exclude_count = sum(1 for r in self.results if r["decision"] == "EXCLUDE")
        uncertain_count = sum(1 for r in self.results if r["decision"] == "UNCERTAIN")
        total = len(self.results)
        
        # Exclusion reason distribution
        exclusion_reasons = {}
        for r in self.results:
            if r["decision"] == "EXCLUDE" and r.get("exclusion_reason"):
                reason = r["exclusion_reason"]
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
        
        # Build report
        report = []
        report.append("# Title-Abstract Screening Analysis Report")
        report.append(f"Date: {Path(__file__).parent.name}")
        report.append("")
        
        # Summary section
        report.append("## Screening Summary")
        report.append("")
        report.append(f"**Total Papers Screened:** {total}")
        report.append(f"**INCLUDE (Advance to Full-Text):** {include_count} ({100*include_count/total:.1f}%)")
        report.append(f"**EXCLUDE (Not Relevant):** {exclude_count} ({100*exclude_count/total:.1f}%)")
        report.append(f"**UNCERTAIN (Needs Discussion):** {uncertain_count} ({100*uncertain_count/total:.1f}%)")
        report.append("")
        
        # Exclusion reasons
        if exclusion_reasons:
            report.append("### Exclusion Reason Distribution")
            report.append("")
            for reason, count in sorted(exclusion_reasons.items(), key=lambda x: x[1], reverse=True):
                pct = 100 * count / exclude_count if exclude_count > 0 else 0
                report.append(f"- {reason}: {count} papers ({pct:.1f}%)")
            report.append("")
        
        # Included papers
        report.append("## Papers for Full-Text Screening (INCLUDE)")
        report.append("")
        report.append("| ID | Title | Year | Confidence | Reason |")
        report.append("|---|---|---|---|---|")
        
        for r in sorted(self.results, key=lambda x: x["decision"] == "INCLUDE", reverse=True):
            if r["decision"] == "INCLUDE":
                title = r["title"][:60] + "..." if len(r["title"]) > 60 else r["title"]
                year = r.get("year", "N/A")
                conf = f"{r['confidence']:.2f}"
                reason = r["reason"][:40] + "..." if len(r["reason"]) > 40 else r["reason"]
                report.append(f"| {r['paper_id']} | {title} | {year} | {conf} | {reason} |")
        report.append("")
        
        # Uncertain papers
        if uncertain_count > 0:
            report.append("## Papers Requiring Discussion (UNCERTAIN)")
            report.append("")
            report.append("| ID | Title | Year | Reason |")
            report.append("|---|---|---|---|")
            
            for r in self.results:
                if r["decision"] == "UNCERTAIN":
                    title = r["title"][:60] + "..." if len(r["title"]) > 60 else r["title"]
                    year = r.get("year", "N/A")
                    reason = r["reason"][:50] + "..." if len(r["reason"]) > 50 else r["reason"]
                    report.append(f"| {r['paper_id']} | {title} | {year} | {reason} |")
            report.append("")
        
        # Excluded papers
        report.append("## Papers Excluded from SLR")
        report.append("")
        report.append(f"Total Excluded: {exclude_count} papers")
        report.append("")
        report.append("| ID | Title | Year | Exclusion Reason |")
        report.append("|---|---|---|---|")
        
        for r in self.results:
            if r["decision"] == "EXCLUDE":
                title = r["title"][:50] + "..." if len(r["title"]) > 50 else r["title"]
                year = r.get("year", "N/A")
                reason = r.get("exclusion_reason", "General exclusion")
                report.append(f"| {r['paper_id']} | {title} | {year} | {reason} |")
        report.append("")
        
        # Recommendations
        report.append("## Next Steps")
        report.append("")
        report.append(f"1. **Advance {include_count} papers to full-text screening phase**")
        report.append(f"2. **Discuss {uncertain_count} papers with screening team**")
        report.append(f"3. **Confirm {exclude_count} exclusion decisions**")
        report.append("")
        
        # Detailed results
        report.append("## Detailed Screening Results")
        report.append("")
        for r in self.results:
            report.append(f"### Paper {r['paper_id']}: {r['title']}")
            report.append(f"- **Decision:** {r['decision']}")
            report.append(f"- **Confidence:** {r['confidence']:.2f}")
            report.append(f"- **Reason:** {r['reason']}")
            report.append(f"- **Abstract:** {r.get('abstract', '[Not available]')}")
            report.append("")
        
        return "\n".join(report)
    
    async def save_report(self, output_path: Path):
        """Save report to file."""
        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate and save report
        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"✅ Report saved to: {output_path}")


async def main():
    """Run the screening analysis."""
    screener = PaperScreener()
    
    try:
        await screener.initialize()
        await screener.screen_all_papers()
        
        # Save report
        output_path = Path(__file__).parent / "projects" / "real-time-translation-platform" / "screening" / "title-abstract" / "screening_decisions.md"
        await screener.save_report(output_path)
        
        # Print summary
        include_count = sum(1 for r in screener.results if r["decision"] == "INCLUDE")
        exclude_count = sum(1 for r in screener.results if r["decision"] == "EXCLUDE")
        uncertain_count = sum(1 for r in screener.results if r["decision"] == "UNCERTAIN")
        total = len(screener.results)
        
        print("\n📊 FINAL RESULTS:")
        print(f"   INCLUDE:   {include_count:3d} papers ({100*include_count/total:5.1f}%)")
        print(f"   EXCLUDE:   {exclude_count:3d} papers ({100*exclude_count/total:5.1f}%)")
        print(f"   UNCERTAIN: {uncertain_count:3d} papers ({100*uncertain_count/total:5.1f}%)")
        print(f"   ─────────────────────")
        print(f"   TOTAL:     {total:3d} papers")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Error during screening: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
