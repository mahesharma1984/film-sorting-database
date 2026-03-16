"""
lib/rag/contracts.py — L3 typed contracts for RAG-as-engine (Issue #55 Phase 2)

Defines the interface between the Work Router (L2 architecture) and the RAG
retrieval engine (implementation). Three named query operations with typed
return values replace bare query_docs() calls scattered across documentation.

Architecture role (governance chain):
  L1 Theory   — exports/knowledge-base/governance-chain-theory.md
  L2 Interface — docs/WORK_ROUTER.md §0.8 (governance preflight)
  L3 Contract  — THIS FILE (typed function signatures)
  L4 Dev rules — docs/WORKFLOW_REGISTRY.md WF-GOV-PREFLIGHT
  L5 Engine    — lib/rag/query.py query_docs() + lib/rag/retriever.py

Usage:
    from lib.rag.contracts import route_problem, governance_preflight, find_workflow

    # Map a symptom to docs
    pointers = route_problem("wrong tier classification")

    # Gather L1-L4 context before changing a component
    ctx = governance_preflight("satellite routing")
    print(ctx.theory)       # L1 docs
    print(ctx.architecture) # L2 docs

    # Look up a named repeatable procedure
    wf = find_workflow("WF-THEORY-CHECK")
    if wf:
        for step in wf.steps:
            print(step)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Return types
# ---------------------------------------------------------------------------

@dataclass
class DocPointer:
    """A pointer to a specific documentation section."""
    section_reference: str     # e.g. 'docs/WORK_ROUTER.md §0.3'
    source_file: str           # relative path from repo root
    line_range: Tuple[int, int]
    score: float
    governance_level: Optional[int] = None  # 1=Theory, 2=Architecture, 3=Components, 4=Dev rules


@dataclass
class GovernanceContext:
    """L1-L4 governance documentation for a component, partitioned by level.

    Produced by governance_preflight(). Provides the ordered context needed
    before modifying classification, routing, or validation logic.
    """
    component: str
    theory: List[DocPointer] = field(default_factory=list)        # L1
    architecture: List[DocPointer] = field(default_factory=list)  # L2
    components: List[DocPointer] = field(default_factory=list)    # L3
    dev_rules: List[DocPointer] = field(default_factory=list)     # L4

    @property
    def all_docs(self) -> List[DocPointer]:
        """All governance docs in L1→L4 order."""
        return self.theory + self.architecture + self.components + self.dev_rules

    @property
    def is_complete(self) -> bool:
        """True if all four governance levels have at least one result."""
        return all([self.theory, self.architecture, self.components, self.dev_rules])


@dataclass
class Workflow:
    """A named repeatable procedure from WORKFLOW_REGISTRY.md."""
    name: str           # e.g. 'WF-THEORY-CHECK'
    when: str           # when to use this workflow
    steps: List[str]    # ordered procedure steps
    source_file: str    # always docs/WORKFLOW_REGISTRY.md


# ---------------------------------------------------------------------------
# Public contract functions
# ---------------------------------------------------------------------------

def route_problem(symptom: str, top_k: int = 5) -> List[DocPointer]:
    """Map a problem symptom to relevant documentation.

    Use when: you have a symptom and need to find where the fix lives.
    Replaces the manual 'run RAG query' instruction in WORK_ROUTER.md §0.1.

    Args:
        symptom: Natural language description of the problem
        top_k:   Number of results to return (default 5)

    Returns:
        List of DocPointers ranked by relevance
    """
    results = _query(symptom, top_k=top_k)
    return [_to_doc_pointer(r) for r in results]


def governance_preflight(component: str, top_k: int = 12) -> GovernanceContext:
    """Gather L1-L4 governance context before modifying a component.

    Use when: about to change classification, routing, validation, or
    reporting logic. Implements WORK_ROUTER.md §0.8 programmatically.

    Queries with governance level filter [1, 2, 3, 4] and partitions
    results by level into the GovernanceContext structure.

    Args:
        component: Component or concept being changed (e.g. 'satellite routing')
        top_k:     Total results to fetch before partitioning (default 12)

    Returns:
        GovernanceContext with theory/architecture/components/dev_rules fields
    """
    results = _query(
        f"governance chain {component}",
        top_k=top_k,
        filter_governance_levels=[1, 2, 3, 4],
    )
    ctx = GovernanceContext(component=component)
    for r in results:
        ptr = _to_doc_pointer(r)
        level = ptr.governance_level
        if level == 1:
            ctx.theory.append(ptr)
        elif level == 2:
            ctx.architecture.append(ptr)
        elif level == 3:
            ctx.components.append(ptr)
        elif level == 4:
            ctx.dev_rules.append(ptr)
    return ctx


def find_workflow(task: str) -> Optional[Workflow]:
    """Find a named workflow from WORKFLOW_REGISTRY.md matching the task.

    Use when: looking for a named repeatable procedure.

    Two-phase lookup:
    1. Exact name match against WORKFLOW_REGISTRY.md (precision — fast)
    2. If no exact match, RAG query filtered to WORKFLOW_REGISTRY.md

    Args:
        task: Workflow name (e.g. 'WF-THEORY-CHECK') or task description

    Returns:
        Workflow with steps, or None if not found
    """
    registry_path = Path('docs/WORKFLOW_REGISTRY.md')
    if not registry_path.exists():
        # Try from project root
        registry_path = Path(__file__).parent.parent.parent / 'docs' / 'WORKFLOW_REGISTRY.md'

    if registry_path.exists():
        wf = _parse_workflow_by_name(task.upper(), registry_path)
        if wf:
            return wf

    # RAG fallback: query filtered to WORKFLOW_REGISTRY results
    try:
        results = _query(task, top_k=5, filter_status=['AUTHORITATIVE'])
        registry_hits = [
            r for r in results
            if 'WORKFLOW_REGISTRY' in r.get('chunk', {}).get('source_file', '')
        ]
        if registry_hits and registry_path.exists():
            ref = registry_hits[0]['section_reference']
            wf_name = _extract_workflow_name(ref)
            if wf_name:
                return _parse_workflow_by_name(wf_name, registry_path)
    except Exception:
        pass  # RAG unavailable — file lookup already attempted above

    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _query(
    query_text: str,
    top_k: int = 5,
    filter_status: Optional[List[str]] = None,
    filter_governance_levels: Optional[List[int]] = None,
):
    """Thin wrapper around query_docs() — isolated for testing."""
    from lib.rag.query import query_docs
    return query_docs(
        query_text,
        top_k=top_k,
        filter_status=filter_status,
        filter_governance_levels=filter_governance_levels,
    )


def _to_doc_pointer(result: dict) -> DocPointer:
    """Convert a raw query_docs() result dict to a DocPointer."""
    chunk = result['chunk']
    line_range = chunk.get('line_range', (0, 0))
    return DocPointer(
        section_reference=result['section_reference'],
        source_file=chunk['source_file'],
        line_range=(line_range[0], line_range[1]),
        score=result['final_score'],
        governance_level=chunk.get('metadata', {}).get('governance_level'),
    )


def _parse_workflow_by_name(name: str, registry_path: Path) -> Optional[Workflow]:
    """Parse a named WF-* workflow from WORKFLOW_REGISTRY.md.

    Matches headings like '### WF-THEORY-CHECK: ...' and extracts
    the When field and numbered steps.
    """
    text = registry_path.read_text()

    # Match '### WF-NAME...' section (up to next '###' or end of file)
    pattern = rf'### ({re.escape(name)}[^\n]*)\n(.*?)(?=\n### |\Z)'
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not m:
        return None

    heading = m.group(1).strip()
    body = m.group(2).strip()

    # Extract **When:** line
    when_match = re.search(r'\*\*When:\*\*\s*(.+)', body)
    when = when_match.group(1).strip() if when_match else ''

    # Extract numbered steps from **Steps:** block or plain numbered list
    steps_block = re.search(r'\*\*Steps:\*\*\n(.*?)(?=\n\*\*|\Z)', body, re.DOTALL)
    if steps_block:
        steps = re.findall(r'^\d+\.\s+`?(.+?)`?$', steps_block.group(1), re.MULTILINE)
    else:
        steps = re.findall(r'^\d+\.\s+(.+)$', body, re.MULTILINE)

    # For atomic workflows (no numbered steps), extract Command as the step
    if not steps:
        cmd_match = re.search(r'```(?:bash)?\n(.*?)```', body, re.DOTALL)
        if cmd_match:
            steps = [cmd_match.group(1).strip()]

    return Workflow(
        name=heading,
        when=when,
        steps=steps,
        source_file=str(registry_path),
    )


def _extract_workflow_name(section_reference: str) -> Optional[str]:
    """Extract WF-* or CW-* workflow name from a section reference string."""
    m = re.search(r'((WF|CW)-[A-Z-]+)', section_reference, re.IGNORECASE)
    return m.group(1).upper() if m else None
