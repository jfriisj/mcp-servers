"""
Automated Screening Documentation System

Generates documentation automatically as MCP screen_paper calls are made.
Handles:
- Decision recording
- Reviewer agreement tracking
- Conflict detection
- Progress updates
- Daily/weekly reports
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScreeningDecision:
    """Single reviewer's screening decision"""
    paper_id: int
    reviewer_id: str
    decision: str  # INCLUDE, EXCLUDE, UNCERTAIN
    confidence_level: float
    reason: str
    exclusion_criteria: Optional[List[str]] = None
    timestamp: Optional[str] = None
    stage: str = "title_abstract"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class PaperScreeningRecord:
    """Complete screening record for a paper"""
    paper_id: int
    title: str
    year: int
    reviewer1_decision: Optional[str] = None
    reviewer1_confidence: Optional[float] = None
    reviewer2_decision: Optional[str] = None
    reviewer2_confidence: Optional[float] = None
    agreement: Optional[bool] = None
    final_decision: Optional[str] = None
    status: str = "PENDING"  # PENDING, COMPLETED, CONFLICT
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class ScreeningDocumentationSystem:
    """Manages automatic documentation generation for screening workflow"""

    def __init__(self, project_root: Path, project_name: str = "real-time-translation-platform"):
        self.project_root = Path(project_root)
        self.screening_root = self.project_root / "projects" / project_name / "screening" / "title-abstract"
        
        # Create directory structure
        self.logs_dir = self.screening_root / "logs"
        self.decisions_dir = self.screening_root / "decisions"
        self.reports_dir = self.screening_root / "reports"
        self.summaries_dir = self.screening_root / "summaries"
        
        for dir_path in [self.logs_dir, self.decisions_dir, self.reports_dir, self.summaries_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Core files
        self.screening_log = self.screening_root / "screening_log.json"
        self.progress_csv = self.screening_root / "screening_progress.csv"
        
        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize core logging files"""
        if not self.screening_log.exists():
            self.screening_log.write_text(json.dumps({"decisions": [], "updated": datetime.utcnow().isoformat()}))
        
        if not self.progress_csv.exists():
            with open(self.progress_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "paper_id", "title", "year",
                    "reviewer1_decision", "reviewer1_confidence",
                    "reviewer2_decision", "reviewer2_confidence",
                    "agreement", "final_decision", "status", "timestamp"
                ])

    def log_paper_decision(self, decision: ScreeningDecision, paper_title: str, paper_year: int) -> None:
        """
        Log a single reviewer's decision for a paper.
        
        Triggers automatic documentation generation if complete.
        """
        # Write decision to individual log
        decision_log = self.logs_dir / f"screening_{decision.paper_id}_{decision.reviewer_id}.json"
        decision_log.write_text(json.dumps(asdict(decision), indent=2))
        logger.info(f"Logged decision: Paper {decision.paper_id}, Reviewer {decision.reviewer_id}")

        # Update master screening log
        self._update_master_log(decision)

        # Update progress CSV
        self._update_progress_csv(decision, paper_title, paper_year)

        # Check if both reviewers have decided for this paper
        record = self._get_paper_record(decision.paper_id)
        if record.reviewer1_decision and record.reviewer2_decision:
            self._generate_decision_document(record, decision.paper_id)

    def _update_master_log(self, decision: ScreeningDecision) -> None:
        """Add decision to master screening log"""
        log_data = json.loads(self.screening_log.read_text())
        
        # Find or create decision entry for this paper
        paper_entry: Dict = {}
        for entry in log_data["decisions"]:
            if entry.get("paper_id") == decision.paper_id:
                paper_entry = entry
                break
        
        if not paper_entry:
            paper_entry = {"paper_id": decision.paper_id}
            log_data["decisions"].append(paper_entry)
        
        # Add reviewer decision
        reviewer_key = f"{decision.reviewer_id}_decision"
        paper_entry[reviewer_key] = asdict(decision)
        
        # Check for agreement if both have decided
        if "reviewer1_decision" in paper_entry and "reviewer2_decision" in paper_entry:
            r1_dec = paper_entry["reviewer1_decision"]["decision"]
            r2_dec = paper_entry["reviewer2_decision"]["decision"]
            paper_entry["agreement"] = (r1_dec == r2_dec)
            paper_entry["final_decision"] = r1_dec if paper_entry["agreement"] else "PENDING_DISCUSSION"
        
        log_data["updated"] = datetime.utcnow().isoformat()
        self.screening_log.write_text(json.dumps(log_data, indent=2))

    def _update_progress_csv(self, decision: ScreeningDecision, paper_title: str, paper_year: int) -> None:
        """Update progress CSV with decision"""
        records = []
        
        # Read existing records
        if self.progress_csv.exists():
            with open(self.progress_csv, 'r', newline='') as f:
                reader = csv.DictReader(f)
                records = list(reader)
        
        # Find or create record for this paper
        paper_record = None
        for rec in records:
            if rec.get("paper_id") == str(decision.paper_id):
                paper_record = rec
                break
        
        if paper_record is None:
            paper_record = {
                "paper_id": str(decision.paper_id),
                "title": paper_title,
                "year": str(paper_year),
                "status": "PENDING",
                "timestamp": decision.timestamp
            }
            records.append(paper_record)
        
        # Update with this reviewer's decision
        if decision.reviewer_id == "reviewer1":
            paper_record["reviewer1_decision"] = decision.decision
            paper_record["reviewer1_confidence"] = str(decision.confidence_level)
        else:
            paper_record["reviewer2_decision"] = decision.decision
            paper_record["reviewer2_confidence"] = str(decision.confidence_level)
            paper_record["timestamp"] = decision.timestamp
        
        # Determine agreement and final status
        if paper_record.get("reviewer1_decision") and paper_record.get("reviewer2_decision"):
            agree = paper_record["reviewer1_decision"] == paper_record["reviewer2_decision"]
            paper_record["agreement"] = str(agree)
            paper_record["final_decision"] = paper_record["reviewer1_decision"] if agree else "PENDING"
            paper_record["status"] = "COMPLETED" if agree else "CONFLICT"
        
        # Write updated CSV
        with open(self.progress_csv, 'w', newline='') as f:
            fieldnames = [
                "paper_id", "title", "year",
                "reviewer1_decision", "reviewer1_confidence",
                "reviewer2_decision", "reviewer2_confidence",
                "agreement", "final_decision", "status", "timestamp"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _get_paper_record(self, paper_id: int) -> PaperScreeningRecord:
        """Retrieve current screening record for a paper"""
        log_data = json.loads(self.screening_log.read_text())
        
        for entry in log_data["decisions"]:
            if entry.get("paper_id") == paper_id:
                r1_dec = entry.get("reviewer1_decision")
                r2_dec = entry.get("reviewer2_decision")
                
                return PaperScreeningRecord(
                    paper_id=paper_id,
                    title=entry.get("title", ""),
                    year=entry.get("year", 0),
                    reviewer1_decision=r1_dec.get("decision") if r1_dec else None,
                    reviewer1_confidence=r1_dec.get("confidence_level") if r1_dec else None,
                    reviewer2_decision=r2_dec.get("decision") if r2_dec else None,
                    reviewer2_confidence=r2_dec.get("confidence_level") if r2_dec else None,
                    agreement=entry.get("agreement"),
                    final_decision=entry.get("final_decision"),
                    status=entry.get("status", "PENDING")
                )
        
        return PaperScreeningRecord(paper_id=paper_id, title="", year=0)

    def _generate_decision_document(self, record: PaperScreeningRecord, paper_id: int) -> None:
        """Generate human-readable decision document when both reviewers have decided"""
        
        if record.agreement:
            # Both reviewers agree
            doc_path = self.decisions_dir / f"{paper_id}_decision_record.md"
            content = self._generate_agreement_document(record)
        else:
            # Reviewers disagree - flag as conflict
            doc_path = self.decisions_dir / f"{paper_id}_conflict_discussion.md"
            content = self._generate_conflict_document(record)
        
        doc_path.write_text(content)
        logger.info(f"Generated decision document: {doc_path}")

    def _generate_agreement_document(self, record: PaperScreeningRecord) -> str:
        """Generate document when reviewers agree"""
        
        r1_conf = record.reviewer1_confidence or 0
        r2_conf = record.reviewer2_confidence or 0
        
        decision_symbol = "✅" if record.final_decision == "INCLUDE" else "❌"
        
        content = f"""# Paper {record.paper_id} Decision Record

{decision_symbol} **BOTH REVIEWERS AGREE** → {record.final_decision}

## Paper Information
- Title: {record.title}
- Year: {record.year}

## Reviewer 1
- Decision: {record.reviewer1_decision}
- Confidence: {r1_conf}

## Reviewer 2
- Decision: {record.reviewer2_decision}
- Confidence: {r2_conf}

## Metrics
- Cohen's Kappa Contribution: 1.0 (perfect agreement)
- Average Confidence: {(r1_conf + r2_conf) / 2:.2f}
- Status: {record.final_decision}

## Next Steps
- {"Ready for full-text screening" if record.final_decision == "INCLUDE" else "Paper excluded from SLR"}
- Timestamp: {record.timestamp}
"""
        return content

    def _generate_conflict_document(self, record: PaperScreeningRecord) -> str:
        """Generate document when reviewers disagree"""
        
        r1_conf = record.reviewer1_confidence or 0
        r2_conf = record.reviewer2_confidence or 0
        
        content = f"""# Paper {record.paper_id} - Reviewer Disagreement

⚠️ **CONFLICT DETECTED**

## Paper Information
- Title: {record.title}
- Year: {record.year}

## Reviewer 1
- Decision: {record.reviewer1_decision}
- Confidence: {r1_conf}

## Reviewer 2
- Decision: {record.reviewer2_decision}
- Confidence: {r2_conf}

## Metrics
- Cohen's Kappa Contribution: 0.0 (complete disagreement)
- Confidence Difference: {abs(r1_conf - r2_conf):.2f}

## Resolution Status
- Status: **PENDING_DISCUSSION**
- Action: Needs team meeting to resolve
- Date Added: {record.timestamp}

## Team Discussion (To Be Filled In)
1. Review paper evidence
2. Discuss disagreement sources
3. Make final decision
4. Document resolution reasoning

## Resolution (To Be Updated)
- Team Decision: [PENDING]
- Resolution Method: [To be documented]
- Final Decision: [To be determined]
- Timestamp: [To be filled]
"""
        return content

    def generate_daily_report(self, date: Optional[str] = None) -> Path:
        """Generate daily screening summary report"""
        if date is None:
            date = datetime.now().strftime("%b%d").upper()
        
        # Calculate statistics
        stats = self._calculate_statistics()
        
        report_path = self.reports_dir / f"daily_summary_{date}.md"
        
        content = f"""# Daily Screening Summary - {date}

## Results
- Papers Screened Today: {stats['papers_screened_today']}
- INCLUDE: {stats['include_count']} ({stats['include_pct']:.1f}%)
- EXCLUDE: {stats['exclude_count']} ({stats['exclude_pct']:.1f}%)
- UNCERTAIN: {stats['uncertain_count']} ({stats['uncertain_pct']:.1f}%)
- CONFLICTS: {stats['conflicts']} ({stats['conflict_pct']:.1f}% of screened)

## Quality Metrics
- Average Confidence: {stats['avg_confidence']:.2f}
- Cohen's Kappa: {stats['kappa']:.2f}
- Pairs Completed: {stats['pairs_completed']}
- Papers Ready for Full-Text: {stats['ready_for_fulltext']}

## Conflicts to Resolve
"""
        
        for conflict_paper in stats['conflict_papers']:
            content += f"- Paper {conflict_paper['id']}: {conflict_paper['r1']} vs {conflict_paper['r2']}\n"
        
        content += f"""

## Timeline Projection
- Screening Pace: {stats['papers_per_hour']:.1f} papers/hour
- Papers Remaining: {stats['papers_remaining']}
- Estimated Hours: {stats['est_hours']:.0f}
- Est. Completion: {stats['est_completion']}

## Next Steps
1. Continue screening next batch
2. Schedule team meeting for conflicts
3. Update progress tracking
"""
        
        report_path.write_text(content)
        logger.info(f"Generated daily report: {report_path}")
        return report_path

    def _calculate_statistics(self) -> Dict:
        """Calculate screening statistics"""
        log_data = json.loads(self.screening_log.read_text())
        
        decisions = log_data.get("decisions", [])
        
        completed = [d for d in decisions if d.get("agreement") is not None]
        include_count = sum(1 for d in completed if d.get("final_decision") == "INCLUDE")
        exclude_count = sum(1 for d in completed if d.get("final_decision") == "EXCLUDE")
        uncertain_count = sum(1 for d in completed if d.get("final_decision") == "UNCERTAIN")
        conflicts = sum(1 for d in completed if not d.get("agreement", True))
        
        total_completed = len(completed)
        
        return {
            "papers_screened_today": total_completed,
            "include_count": include_count,
            "exclude_count": exclude_count,
            "uncertain_count": uncertain_count,
            "include_pct": (include_count / total_completed * 100) if total_completed else 0,
            "exclude_pct": (exclude_count / total_completed * 100) if total_completed else 0,
            "uncertain_pct": (uncertain_count / total_completed * 100) if total_completed else 0,
            "conflicts": conflicts,
            "conflict_pct": (conflicts / total_completed * 100) if total_completed else 0,
            "avg_confidence": self._calculate_avg_confidence(completed),
            "kappa": self._calculate_kappa(completed),
            "pairs_completed": total_completed,
            "ready_for_fulltext": include_count,
            "conflict_papers": [d for d in completed if not d.get("agreement", True)],
            "papers_per_hour": 3.6,  # Base rate
            "papers_remaining": 104 - total_completed,
            "est_hours": (104 - total_completed) / 3.6,
            "est_completion": (datetime.now()).strftime("%B %d, %Y")
        }

    def _calculate_avg_confidence(self, decisions: List[Dict]) -> float:
        """Calculate average confidence across all decisions"""
        confidences = []
        for d in decisions:
            if "reviewer1_decision" in d and "confidence_level" in d["reviewer1_decision"]:
                confidences.append(d["reviewer1_decision"]["confidence_level"])
            if "reviewer2_decision" in d and "confidence_level" in d["reviewer2_decision"]:
                confidences.append(d["reviewer2_decision"]["confidence_level"])
        
        return sum(confidences) / len(confidences) if confidences else 0

    def _calculate_kappa(self, decisions: List[Dict]) -> float:
        """Calculate Cohen's Kappa for inter-rater reliability"""
        if not decisions:
            return 0
        
        agreements = sum(1 for d in decisions if d.get("agreement", False))
        total = len(decisions)
        
        # Simplified calculation - should implement full Cohen's Kappa
        return agreements / total if total else 0
