"""
tests/test_rag_contracts.py — Tests for Issue #55 Phase 2 RAG contracts layer.

Covers:
  - DocPointer, GovernanceContext, Workflow dataclasses
  - route_problem(): wraps query_docs, returns List[DocPointer]
  - governance_preflight(): partitions by governance level
  - find_workflow(): parses WORKFLOW_REGISTRY.md by name
  - _parse_workflow_by_name(): integration test against real registry file
  - _to_doc_pointer(): conversion helper

RAG dependencies (sentence-transformers, numpy) are mocked throughout.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.rag.contracts import (
    DocPointer,
    GovernanceContext,
    Workflow,
    _to_doc_pointer,
    _parse_workflow_by_name,
    _extract_workflow_name,
    route_problem,
    governance_preflight,
    find_workflow,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_raw_result(
    section_reference='docs/WORK_ROUTER.md §0.3',
    source_file='docs/WORK_ROUTER.md',
    line_range=(97, 106),
    final_score=0.85,
    governance_level=4,
):
    """Build a minimal query_docs() result dict."""
    return {
        'section_reference': section_reference,
        'final_score': final_score,
        'semantic_score': 0.7,
        'keyword_score': 0.2,
        'authority_score': 0.1,
        'chunk': {
            'source_file': source_file,
            'line_range': list(line_range),
            'metadata': {
                'governance_level': governance_level,
                'status': 'AUTHORITATIVE',
            },
        },
    }


# ---------------------------------------------------------------------------
# DocPointer
# ---------------------------------------------------------------------------

class TestDocPointer:

    def test_to_doc_pointer_basic(self):
        raw = _make_raw_result()
        ptr = _to_doc_pointer(raw)
        assert isinstance(ptr, DocPointer)
        assert ptr.section_reference == 'docs/WORK_ROUTER.md §0.3'
        assert ptr.source_file == 'docs/WORK_ROUTER.md'
        assert ptr.line_range == (97, 106)
        assert ptr.score == pytest.approx(0.85)
        assert ptr.governance_level == 4

    def test_to_doc_pointer_no_governance_level(self):
        raw = _make_raw_result(governance_level=None)
        raw['chunk']['metadata'].pop('governance_level')
        ptr = _to_doc_pointer(raw)
        assert ptr.governance_level is None


# ---------------------------------------------------------------------------
# GovernanceContext
# ---------------------------------------------------------------------------

class TestGovernanceContext:

    def test_all_docs_ordering(self):
        ctx = GovernanceContext(component='test')
        l1 = DocPointer('ref1', 'theory.md', (1, 10), 0.9, governance_level=1)
        l2 = DocPointer('ref2', 'arch.md', (1, 10), 0.8, governance_level=2)
        l3 = DocPointer('ref3', 'comp.md', (1, 10), 0.7, governance_level=3)
        l4 = DocPointer('ref4', 'dev.md', (1, 10), 0.6, governance_level=4)
        ctx.theory.append(l1)
        ctx.architecture.append(l2)
        ctx.components.append(l3)
        ctx.dev_rules.append(l4)
        assert ctx.all_docs == [l1, l2, l3, l4]

    def test_is_complete_true(self):
        ctx = GovernanceContext(component='test')
        ctx.theory.append(DocPointer('r1', 'f', (1, 2), 0.9, 1))
        ctx.architecture.append(DocPointer('r2', 'f', (1, 2), 0.8, 2))
        ctx.components.append(DocPointer('r3', 'f', (1, 2), 0.7, 3))
        ctx.dev_rules.append(DocPointer('r4', 'f', (1, 2), 0.6, 4))
        assert ctx.is_complete is True

    def test_is_complete_false_missing_level(self):
        ctx = GovernanceContext(component='test')
        ctx.theory.append(DocPointer('r1', 'f', (1, 2), 0.9, 1))
        ctx.architecture.append(DocPointer('r2', 'f', (1, 2), 0.8, 2))
        # no L3 or L4
        assert ctx.is_complete is False


# ---------------------------------------------------------------------------
# route_problem()
# ---------------------------------------------------------------------------

class TestRouteProblem:

    def test_returns_list_of_doc_pointers(self):
        raw_results = [_make_raw_result(), _make_raw_result(section_reference='docs/DEBUG_RUNBOOK.md §1')]
        with patch('lib.rag.contracts._query', return_value=raw_results):
            result = route_problem("wrong tier classification")
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, DocPointer) for p in result)

    def test_passes_symptom_and_top_k(self):
        with patch('lib.rag.contracts._query', return_value=[]) as mock_q:
            route_problem("wrong tier classification", top_k=3)
        mock_q.assert_called_once_with("wrong tier classification", top_k=3)

    def test_empty_results(self):
        with patch('lib.rag.contracts._query', return_value=[]):
            result = route_problem("no match query")
        assert result == []


# ---------------------------------------------------------------------------
# governance_preflight()
# ---------------------------------------------------------------------------

class TestGovernancePreflight:

    def test_partitions_by_governance_level(self):
        raw_results = [
            _make_raw_result(section_reference='theory', governance_level=1),
            _make_raw_result(section_reference='arch', governance_level=2),
            _make_raw_result(section_reference='comp', governance_level=3),
            _make_raw_result(section_reference='dev', governance_level=4),
        ]
        with patch('lib.rag.contracts._query', return_value=raw_results):
            ctx = governance_preflight("satellite routing")
        assert len(ctx.theory) == 1
        assert len(ctx.architecture) == 1
        assert len(ctx.components) == 1
        assert len(ctx.dev_rules) == 1
        assert ctx.theory[0].section_reference == 'theory'
        assert ctx.dev_rules[0].section_reference == 'dev'

    def test_component_name_in_context(self):
        with patch('lib.rag.contracts._query', return_value=[]):
            ctx = governance_preflight("popcorn classifier")
        assert ctx.component == "popcorn classifier"

    def test_unknown_governance_level_ignored(self):
        raw = _make_raw_result(governance_level=5)
        with patch('lib.rag.contracts._query', return_value=[raw]):
            ctx = governance_preflight("something")
        # Level 5 is implementation — not placed in any governance bucket
        assert ctx.all_docs == []

    def test_passes_governance_level_filter(self):
        with patch('lib.rag.contracts._query', return_value=[]) as mock_q:
            governance_preflight("signals")
        call_kwargs = mock_q.call_args[1]
        assert call_kwargs.get('filter_governance_levels') == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# _parse_workflow_by_name() — integration test against real registry
# ---------------------------------------------------------------------------

REGISTRY_PATH = Path('docs/WORKFLOW_REGISTRY.md')


@pytest.mark.skipif(not REGISTRY_PATH.exists(), reason="WORKFLOW_REGISTRY.md not found")
class TestParseWorkflowByName:

    def test_finds_existing_atomic_workflow(self):
        wf = _parse_workflow_by_name('WF-TEST-UNIT', REGISTRY_PATH)
        assert wf is not None
        assert 'WF-TEST-UNIT' in wf.name
        assert 'pytest' in ' '.join(wf.steps).lower() or len(wf.steps) >= 1

    def test_finds_theory_check_workflow(self):
        """WF-THEORY-CHECK added by Issue #55."""
        wf = _parse_workflow_by_name('WF-THEORY-CHECK', REGISTRY_PATH)
        assert wf is not None
        assert 'WF-THEORY-CHECK' in wf.name
        assert len(wf.steps) >= 3

    def test_finds_arch_check_workflow(self):
        """WF-ARCH-CHECK added by Issue #55."""
        wf = _parse_workflow_by_name('WF-ARCH-CHECK', REGISTRY_PATH)
        assert wf is not None
        assert 'WF-ARCH-CHECK' in wf.name

    def test_finds_data_trace_workflow(self):
        """WF-DATA-TRACE added by Issue #55."""
        wf = _parse_workflow_by_name('WF-DATA-TRACE', REGISTRY_PATH)
        assert wf is not None
        assert 'WF-DATA-TRACE' in wf.name

    def test_finds_drift_audit_workflow(self):
        """WF-DRIFT-AUDIT added by Issue #55."""
        wf = _parse_workflow_by_name('WF-DRIFT-AUDIT', REGISTRY_PATH)
        assert wf is not None
        assert 'WF-DRIFT-AUDIT' in wf.name

    def test_returns_none_for_missing_name(self):
        wf = _parse_workflow_by_name('WF-DOES-NOT-EXIST', REGISTRY_PATH)
        assert wf is None

    def test_workflow_has_source_file(self):
        wf = _parse_workflow_by_name('WF-GOV-PREFLIGHT', REGISTRY_PATH)
        assert wf is not None
        assert 'WORKFLOW_REGISTRY' in wf.source_file

    def test_composed_workflow_has_steps(self):
        wf = _parse_workflow_by_name('CW-GOVERNED-CHANGE', REGISTRY_PATH)
        assert wf is not None
        assert len(wf.steps) >= 3


# ---------------------------------------------------------------------------
# find_workflow() — unit test with mocked file path
# ---------------------------------------------------------------------------

class TestFindWorkflow:

    def test_finds_by_exact_name(self):
        """find_workflow('WF-TEST-UNIT') resolves via file parse."""
        wf = find_workflow('WF-TEST-UNIT')
        if REGISTRY_PATH.exists():
            assert wf is not None
            assert 'WF-TEST-UNIT' in wf.name

    def test_returns_none_for_unknown(self):
        with patch('lib.rag.contracts._query', return_value=[]):
            wf = find_workflow('WF-NONEXISTENT-WORKFLOW')
        assert wf is None


# ---------------------------------------------------------------------------
# _extract_workflow_name()
# ---------------------------------------------------------------------------

class TestExtractWorkflowName:

    def test_extracts_wf_name(self):
        assert _extract_workflow_name('docs/WORKFLOW_REGISTRY.md WF-TEST-UNIT') == 'WF-TEST-UNIT'

    def test_extracts_cw_name(self):
        assert _extract_workflow_name('CW-GOVERNED-CHANGE: some section') == 'CW-GOVERNED-CHANGE'

    def test_returns_none_for_no_match(self):
        assert _extract_workflow_name('docs/WORK_ROUTER.md §0.3') is None
