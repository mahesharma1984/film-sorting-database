#!/usr/bin/env python3
"""
Film Sorting Database Dashboard
Single-file Streamlit application for collection overview and pipeline monitoring.

Run:  streamlit run dashboard.py
"""

import os
import sys
import re
import csv
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_ORDER = ['Core', 'Reference', 'Satellite', 'Popcorn', 'Staging', 'Unsorted']

TIER_COLORS = {
    'Core':      '#C44E52',
    'Reference': '#DD8452',
    'Satellite': '#55A868',
    'Popcorn':   '#4C72B0',
    'Staging':   '#8C8C8C',
    'Unsorted':  '#CCCCCC',
}

# Maps reason code prefixes to confidence scores (for CSVs that lack a confidence column)
REASON_CONFIDENCE = {
    # Current reason codes (Issue #42+)
    'explicit_lookup':           1.0,
    'corpus_lookup':             1.0,
    'reference_canon':           1.0,
    'both_agree':                0.85,
    'director_disambiguates':    0.75,
    'director_signal':           0.65,
    'structural_signal':         0.65,
    'review_flagged':            0.4,
    'user_tag_recovery':         0.8,
    'user_tag':                  0.8,
    'popcorn':                   0.6,
    # Legacy reason codes (pre-Issue #42, for old manifest CSVs)
    'core_director':             1.0,
    'core_director_exact':       1.0,
    'country_satellite':         0.7,
    'country_decade_satellite':  0.7,
    'tmdb_satellite':            0.7,
    'satellite':                 0.7,
}


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Film Sorting Database",
    page_icon="\U0001F3AC",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Library imports (graceful degradation)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LIB_AVAILABLE = False

try:
    from lib.constants import SATELLITE_ROUTING_RULES as _SRR
    SATELLITE_ROUTING_RULES = _SRR
    LIB_AVAILABLE = True
except ImportError:
    SATELLITE_ROUTING_RULES = {}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_PRIMARY_MANIFESTS = {'sorting_manifest.csv', 'library_audit.csv'}
_DIAGNOSTIC_MANIFESTS = {'reaudit_report.csv', 'review_queue.csv'}
_EXCLUDED_MANIFESTS = {
    'evidence_trails.csv', 'corpus_check_report.csv',
    'lookup_coverage.csv', 'manual_enrichment.csv',
    'rename_manifest.csv', 'unsorted_readiness.csv',
}


def find_manifests(output_dir: Path):
    """Return (primary_list, diagnostic_list) sorted by mtime (newest first).

    Primary: classification manifests suitable for System Health view.
    Diagnostic: read-only audit outputs (reaudit, review queue).
    Excluded: evidence trails, corpus drafts, and other non-manifest CSVs.
    """
    if not output_dir.exists():
        return [], []

    def _sorted(names):
        paths = []
        for name in names:
            p = output_dir / name
            if p.exists() and p.stat().st_size > 1024:
                paths.append(p)
        return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)

    primary = _sorted(_PRIMARY_MANIFESTS)
    diagnostic = _sorted(_DIAGNOSTIC_MANIFESTS)
    return primary, diagnostic


def detect_format(columns):
    """Detect CSV schema version from column names."""
    cols = set(c.lower().strip() for c in columns)
    if 'filename' in cols and 'confidence' in cols:
        return 'v1'
    if 'original_filename' in cols and 'language' in cols:
        return 'v02'
    if 'original_filename' in cols:
        return 'v01'
    return 'unknown'


def _derive_decade(year):
    if pd.notna(year) and year > 0:
        return f"{int(year) // 10 * 10}s"
    return ''


def _derive_confidence(reason):
    if not isinstance(reason, str):
        return 0.0
    reason_lower = reason.lower().strip()
    for prefix, conf in REASON_CONFIDENCE.items():
        if reason_lower.startswith(prefix):
            return conf
    return 0.0


def _derive_subdirectory(destination):
    """Parse subdirectory / satellite category from destination path."""
    if not isinstance(destination, str) or not destination.strip():
        return ''
    parts = [p for p in destination.replace('\\', '/').split('/') if p.strip()]
    # Common patterns:  "1970s/Satellite/Brazilian Exploitation/"  or  "Satellite/Giallo/"
    # Return the last meaningful segment that isn't a tier name or decade
    tiers_lower = {t.lower() for t in TIER_ORDER}
    decade_re = re.compile(r'^\d{4}s$')
    for part in reversed(parts):
        p = part.strip()
        if p.lower() not in tiers_lower and not decade_re.match(p) and p:
            return p
    return ''


@st.cache_data
def load_manifest(csv_path: str) -> pd.DataFrame:
    """Load a manifest CSV and normalise to a unified schema."""
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    fmt = detect_format(df.columns)

    # ---- Column renaming ----
    if fmt == 'v1':
        # Already has most columns
        pass
    elif fmt in ('v02', 'v01'):
        if 'original_filename' in df.columns:
            df = df.rename(columns={'original_filename': 'filename'})
        if 'new_filename' in df.columns:
            df = df.drop(columns=['new_filename'], errors='ignore')

    # ---- Ensure every unified column exists ----
    unified = ['filename', 'title', 'year', 'director', 'language', 'country',
               'user_tag', 'tier', 'decade', 'subdirectory', 'destination',
               'confidence', 'reason']
    for col in unified:
        if col not in df.columns:
            df[col] = ''

    # ---- Type coercion ----
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')

    # ---- Derive missing values ----
    # Decade
    mask_no_decade = df['decade'].astype(str).str.strip().isin(['', 'nan'])
    df.loc[mask_no_decade, 'decade'] = df.loc[mask_no_decade, 'year'].apply(_derive_decade)

    # Subdirectory
    mask_no_sub = df['subdirectory'].astype(str).str.strip().isin(['', 'nan'])
    df.loc[mask_no_sub, 'subdirectory'] = df.loc[mask_no_sub, 'destination'].apply(_derive_subdirectory)

    # Confidence — fill NaN with reason-derived values, ensure float dtype
    mask_no_conf = df['confidence'].isna()
    if mask_no_conf.any():
        derived = df.loc[mask_no_conf, 'reason'].apply(_derive_confidence).astype(float)
        df['confidence'] = df['confidence'].astype(float)
        df.loc[mask_no_conf, 'confidence'] = derived

    # Normalise tier casing
    df['tier'] = df['tier'].str.strip().str.title()
    df.loc[df['tier'] == '', 'tier'] = 'Unsorted'

    return df


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _fill_color(pct: float) -> str:
    if pct >= 0.8:
        return '#C44E52'   # red
    if pct >= 0.5:
        return '#DD8452'   # amber
    return '#55A868'       # green


# ---------------------------------------------------------------------------
# Section 1 – Collection Overview
# ---------------------------------------------------------------------------

def render_collection_overview(df: pd.DataFrame):
    st.header("Collection Overview")

    # --- Hero metrics ---
    total = len(df)
    classified = df[~df['tier'].isin(['Unsorted', 'Staging'])]
    classified_pct = len(classified) / total * 100 if total else 0

    tier_counts = df['tier'].value_counts()
    cols = st.columns(6)
    cols[0].metric("Total Films", f"{total:,}")
    cols[1].metric("Classified", f"{classified_pct:.1f}%")
    for i, tier in enumerate(['Core', 'Reference', 'Satellite', 'Popcorn']):
        cols[i + 2].metric(tier, int(tier_counts.get(tier, 0)))

    st.divider()

    # --- Films by Decade ---
    st.subheader("Films by Decade")
    include_unsorted = st.checkbox("Include Unsorted / Staging", value=False,
                                   key='decade_unsorted')
    plot_df = df.copy()
    if not include_unsorted:
        plot_df = plot_df[~plot_df['tier'].isin(['Unsorted', 'Staging'])]
    plot_df = plot_df[plot_df['decade'].str.strip() != '']

    if len(plot_df):
        cross = (plot_df.groupby(['decade', 'tier']).size()
                 .reset_index(name='count'))
        decade_order = sorted(cross['decade'].unique())
        tier_order_filtered = [t for t in TIER_ORDER if t in cross['tier'].unique()]
        fig = px.bar(
            cross, x='decade', y='count', color='tier',
            color_discrete_map=TIER_COLORS,
            category_orders={'decade': decade_order, 'tier': tier_order_filtered},
            barmode='stack',
        )
        fig.update_layout(height=320, margin=dict(t=20, b=40),
                          xaxis_title='', yaxis_title='Films',
                          legend_title_text='')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No decade data available for classified films.")

    st.divider()

    # --- Signal Quality Panel ---
    st.subheader("Classification Signal Quality")
    st.caption("How heuristic decisions were made — explicit lookups and corpus matches excluded")

    _DIRECTOR_REASONS = {'director_signal', 'director_disambiguates'}
    _ALL_SIGNAL_REASONS = {'both_agree', 'director_signal', 'director_disambiguates',
                           'structural_signal', 'review_flagged'}
    heuristic_df = df[df['reason'].str.strip().isin(_ALL_SIGNAL_REASONS)]

    if len(heuristic_df):
        director_led = len(heuristic_df[heuristic_df['reason'].isin(_DIRECTOR_REASONS)])
        both_agree_n = len(heuristic_df[heuristic_df['reason'] == 'both_agree'])
        structural_n = len(heuristic_df[heuristic_df['reason'] == 'structural_signal'])
        ambiguous_n  = len(heuristic_df[heuristic_df['reason'] == 'review_flagged'])

        sig_cols = st.columns(4)
        sig_cols[0].metric(
            "Both signals agree", both_agree_n,
            help="director + structure independently matched same category — highest heuristic confidence (0.85)"
        )
        sig_cols[1].metric(
            "Director-led", director_led,
            help="director_signal: director matched, no structural; director_disambiguates: director broke tie"
        )
        sig_cols[2].metric(
            "Structural only", structural_n,
            help="structural_signal — country/genre/keywords matched, no director evidence"
        )
        sig_cols[3].metric(
            "Ambiguous (review_flagged)", ambiguous_n,
            help="Multiple structural categories matched, no director to resolve — routed to highest-priority but needs curator attention"
        )

        left_sig, right_sig = st.columns([1, 1])

        with left_sig:
            sig_data = pd.DataFrame([
                {'signal': 'Both agree',      'count': both_agree_n, 'conf': 0.85},
                {'signal': 'Director-led',    'count': director_led, 'conf': 0.70},
                {'signal': 'Structural only', 'count': structural_n, 'conf': 0.65},
                {'signal': 'Ambiguous',       'count': ambiguous_n,  'conf': 0.40},
            ])
            fig = px.bar(
                sig_data, x='count', y='signal', orientation='h',
                color='conf',
                color_continuous_scale=[[0.0, '#CCCCCC'], [0.4, '#DD8452'], [1.0, '#55A868']],
                range_color=[0.3, 1.0],
                custom_data=['conf'],
            )
            fig.update_traces(
                hovertemplate='%{y}: %{x} films (avg conf ~%{customdata[0]:.2f})<extra></extra>'
            )
            fig.update_layout(
                height=220, margin=dict(t=10, b=20, l=10, r=10),
                yaxis_title='', xaxis_title='Films',
                coloraxis_showscale=False,
                yaxis=dict(autorange='reversed'),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right_sig:
            if ambiguous_n > 0:
                flagged_df = heuristic_df[heuristic_df['reason'] == 'review_flagged']
                st.caption(
                    f"**{ambiguous_n} review-flagged films** — multiple structural categories matched, "
                    "no director signal to resolve. Add a SORTING_DATABASE entry to pin each."
                )
                _fcols = [c for c in ['title', 'year', 'director', 'subdirectory', 'country', 'confidence']
                          if c in flagged_df.columns]
                st.dataframe(
                    flagged_df[_fcols].sort_values('year').reset_index(drop=True),
                    use_container_width=True, height=200,
                    column_config={
                        'confidence': st.column_config.ProgressColumn(
                            'Conf', min_value=0.0, max_value=1.0, format='%.2f'),
                        'year': st.column_config.NumberColumn('Year', format='%d'),
                    },
                )
            else:
                st.success("No ambiguous classifications — every heuristic film has a clear signal.")
    else:
        st.info("No heuristic classifications in this manifest (all films are via lookup, corpus, or unsorted).")

    st.divider()
    render_signal_accuracy()


# ---------------------------------------------------------------------------
# Signal Accuracy panel — consumes output/accuracy_baseline.json
# ---------------------------------------------------------------------------

_ACCURACY_REASON_ORDER = [
    'user_tag_recovery', 'both_agree', 'director_signal',
    'structural_signal', 'review_flagged', 'director_disambiguates', 'popcorn',
]


def render_signal_accuracy():
    """Show per-reason-code accuracy from the latest accuracy baseline."""
    st.subheader("Signal Accuracy (Reaudit Baseline)")

    baseline_path = PROJECT_ROOT / 'output' / 'accuracy_baseline.json'
    if not baseline_path.exists():
        st.info(
            "No accuracy baseline found. Run: "
            "`python scripts/reaudit.py && python scripts/analyze_accuracy.py`",
            icon="ℹ️",
        )
        return

    with open(baseline_path) as f:
        baseline = json.load(f)

    by_stage = baseline.get('by_stage', {})
    date_str = baseline.get('date', '—')
    commit = baseline.get('commit', '—')
    contract = baseline.get('routing_contract', '—')
    combined = baseline.get('combined_accuracy', {})

    # Header line
    combined_score = combined.get('score', 0)
    combined_conf = combined.get('confirmed', 0)
    combined_total = combined.get('total', 0)
    st.caption(
        f"Baseline: **{date_str}** | commit `{commit}` | contract: `{contract}` | "
        f"combined: **{combined_conf}/{combined_total}** ({combined_score:.1%})"
    )

    # Per-reason-code table (signal codes only, not unsorted_*)
    rows = []
    for code in _ACCURACY_REASON_ORDER:
        if code not in by_stage:
            continue
        entry = by_stage[code]
        confirmed = entry.get('confirmed', 0)
        total = entry.get('total', 0)
        score = entry.get('score', 0.0)
        rows.append({'Reason Code': code, 'Confirmed': confirmed,
                     'Total': total, 'Accuracy': score})

    if not rows:
        st.info("No per-signal data in baseline.")
        return

    acc_df = pd.DataFrame(rows)

    def _colour(score):
        if score >= 0.75:
            return 'background-color: #d4edda'  # green
        if score >= 0.60:
            return 'background-color: #fff3cd'  # amber
        return 'background-color: #f8d7da'       # red

    styled = (
        acc_df.style
        .format({'Accuracy': '{:.1%}'})
        .applymap(_colour, subset=['Accuracy'])
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Section 2 – Pipeline Health
# ---------------------------------------------------------------------------

def render_pipeline_health(df: pd.DataFrame):
    st.header("Pipeline Health")

    # --- Summary metrics ---
    avg_conf = df['confidence'].mean() if len(df) else 0
    explicit = len(df[df['reason'].str.lower().str.startswith('explicit_lookup')])
    unsorted_count = len(df[df['tier'].isin(['Unsorted', 'Staging'])])

    cols = st.columns(4)
    cols[0].metric("Avg Confidence", f"{avg_conf:.2f}")
    cols[1].metric("Explicit Lookups", explicit)
    cols[2].metric("Unsorted", f"{unsorted_count:,}")
    cols[3].metric("Classified", f"{len(df) - unsorted_count:,}")

    st.divider()

    # --- Confidence histogram + Reason breakdown ---
    left, right = st.columns(2)

    with left:
        st.subheader("Confidence Distribution")
        fig = px.histogram(
            df, x='confidence', nbins=20,
            color_discrete_sequence=['#DD8452'],
            labels={'confidence': 'Confidence Score', 'count': 'Films'},
        )
        fig.update_layout(height=400, margin=dict(t=20, b=40),
                          yaxis_title='Films', bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Classification Reasons")
        reason_counts = (df['reason'].str.strip()
                         .value_counts()
                         .head(20)
                         .reset_index())
        reason_counts.columns = ['reason', 'count']
        reason_counts['type'] = reason_counts['reason'].apply(
            lambda r: 'Unsorted' if 'unsorted' in str(r).lower() else 'Classified'
        )
        fig = px.bar(
            reason_counts, y='reason', x='count', orientation='h',
            color='type',
            color_discrete_map={'Unsorted': '#CCCCCC', 'Classified': '#55A868'},
        )
        fig.update_layout(
            height=max(350, len(reason_counts) * 28),
            margin=dict(t=20, b=30, l=10, r=10),
            showlegend=True, legend_title_text='',
            yaxis_title='', xaxis_title='Films',
            yaxis=dict(autorange='reversed'),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Unsorted triage table ---
    st.subheader("Unsorted Film Triage")
    unsorted_df = df[df['tier'].isin(['Unsorted', 'Staging'])].copy()

    if len(unsorted_df):
        # Data readiness funnel
        if 'data_readiness' in unsorted_df.columns:
            dr_counts = unsorted_df['data_readiness'].value_counts().to_dict()
            dr_cols = st.columns(4)
            dr_cols[0].metric("R0 — no year",
                              dr_counts.get('R0', 0),
                              help="No year extracted — non-film candidates (supplements, interviews)")
            dr_cols[1].metric("R1 — year only",
                              dr_counts.get('R1', 0),
                              help="Year found but no API data returned — binding constraint population")
            dr_cols[2].metric("R2 — partial data",
                              dr_counts.get('R2', 0),
                              help="Director OR country present, not both — enrichment candidates")
            dr_cols[3].metric("R3 — full data, no match",
                              dr_counts.get('R3', 0),
                              help="Full data available but no routing rule matched — routing gap candidates")
            st.caption("R0 → non-film | R1 → enrich via API | R2 → add manual_enrichment.csv | R3 → add SORTING_DATABASE entry or new routing rule")
            st.divider()

        # Filters
        filter_cols = st.columns(3)
        with filter_cols[0]:
            reason_options = sorted(unsorted_df['reason'].unique())
            selected_reasons = st.multiselect("Filter by reason", reason_options,
                                               key='triage_reason')
        with filter_cols[1]:
            has_director = st.checkbox("Has director only", value=False,
                                       key='triage_director')
        with filter_cols[2]:
            has_year = st.checkbox("Has year only", value=False, key='triage_year')

        filtered = unsorted_df
        if selected_reasons:
            filtered = filtered[filtered['reason'].isin(selected_reasons)]
        if has_director:
            filtered = filtered[filtered['director'].str.strip() != '']
        if has_year:
            filtered = filtered[filtered['year'].notna() & (filtered['year'] > 0)]

        st.write(f"Showing **{len(filtered):,}** of {len(unsorted_df):,} unsorted films")
        display_cols = ['title', 'year', 'director', 'reason', 'data_readiness', 'country']
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[display_cols].reset_index(drop=True),
            use_container_width=True,
            height=400,
        )
    else:
        st.success("No unsorted films — everything is classified!")

    st.divider()
    render_reaudit_discrepancies()
    st.divider()
    render_failure_cohorts()


# ---------------------------------------------------------------------------
# Reaudit Discrepancies panel — consumes output/reaudit_report.csv
# ---------------------------------------------------------------------------

def render_reaudit_discrepancies():
    """Show discrepancy summary from the latest reaudit run."""
    st.subheader("Reaudit Discrepancies")

    reaudit_path = PROJECT_ROOT / 'output' / 'reaudit_report.csv'
    if not reaudit_path.exists():
        st.info(
            "No reaudit data. Run: `python audit.py && python scripts/reaudit.py`",
            icon="ℹ️",
        )
        return

    rdf = pd.read_csv(reaudit_path, dtype=str, keep_default_na=False)

    total = len(rdf)
    confirmed = len(rdf[rdf['match'] == 'confirmed'])
    rate = confirmed / total if total else 0

    disc_types = rdf[rdf['match'] != 'confirmed']['discrepancy_type'].value_counts().to_dict()

    hero = st.columns(5)
    hero[0].metric("Confirmed", f"{confirmed:,}", help=f"{rate:.1%} of organized library matches classifier")
    hero[1].metric("Wrong tier", disc_types.get('wrong_tier', 0))
    hero[2].metric("Wrong category", disc_types.get('wrong_category', 0))
    hero[3].metric("Unroutable", disc_types.get('unroutable', 0))
    hero[4].metric("No data", disc_types.get('no_data', 0))

    disc_df = rdf[rdf['match'] != 'confirmed']
    if len(disc_df):
        with st.expander(f"View {len(disc_df)} discrepancies"):
            show_cols = [c for c in ['filename', 'current_tier', 'current_category',
                                     'classified_tier', 'classified_category',
                                     'discrepancy_type', 'classified_reason'] if c in disc_df.columns]
            st.dataframe(disc_df[show_cols].reset_index(drop=True),
                         use_container_width=True, height=350)
    else:
        st.success("No discrepancies — organized library matches classifier output.")


# ---------------------------------------------------------------------------
# Failure Cohorts panel — consumes output/failure_cohorts.json
# ---------------------------------------------------------------------------

_COHORT_COLOURS = {
    'cap_exceeded':   '#C44E52',
    'director_gap':   '#DD8452',
    'data_gap':       '#4C72B0',
    'gate_design_gap':'#8C8C8C',
    'taxonomy_gap':   '#55A868',
}
_CONF_ORDER = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}


def render_failure_cohorts():
    """Show top actionable failure cohorts from analyze_cohorts.py output."""
    st.subheader("Failure Cohorts")

    cohorts_path = PROJECT_ROOT / 'output' / 'failure_cohorts.json'
    if not cohorts_path.exists():
        st.info(
            "No cohort data. Run: `python scripts/analyze_cohorts.py`",
            icon="ℹ️",
        )
        return

    with open(cohorts_path) as f:
        cohorts = json.load(f)

    if not cohorts:
        st.info("No failure cohorts detected.")
        return

    # Sort: HIGH first, then MEDIUM, then LOW; within each tier by count desc
    cohorts_sorted = sorted(cohorts,
                            key=lambda c: (_CONF_ORDER.get(c.get('confidence', 'LOW'), 2),
                                           -c.get('count', 0)))
    top = cohorts_sorted[:5]

    st.caption(f"{len(cohorts)} cohorts total | showing top {len(top)}")

    for cohort in top:
        ctype = cohort.get('cohort_type', '?')
        name = cohort.get('name', '?')
        count = cohort.get('count', 0)
        conf = cohort.get('confidence', '?')
        constraint = cohort.get('binding_constraint', '')
        hypothesis = cohort.get('hypothesis', '')
        films = cohort.get('films', [])

        colour = _COHORT_COLOURS.get(ctype, '#8C8C8C')
        label = f"[{ctype}] {name} — {count} film{'s' if count != 1 else ''} ({conf})"

        with st.expander(label):
            st.markdown(f"**Binding constraint:** {constraint}")
            st.markdown(f"**Suggested action:** {hypothesis}")
            if films:
                film_rows = [{'title': f.get('title', ''), 'year': f.get('year', ''),
                              'director': f.get('director', ''),
                              'nearest_miss': f.get('nearest_miss', '')} for f in films]
                st.dataframe(pd.DataFrame(film_rows), use_container_width=True,
                             hide_index=True)


# ---------------------------------------------------------------------------
# Section 3 – Film Browser
# ---------------------------------------------------------------------------

def render_film_browser(df: pd.DataFrame):
    st.header("Film Browser")

    # --- Filter controls ---
    filter_row = st.columns(4)

    with filter_row[0]:
        tier_opts = [t for t in TIER_ORDER if t in df['tier'].unique()]
        selected_tiers = st.multiselect("Tier", tier_opts, default=tier_opts,
                                         key='browser_tier')
    with filter_row[1]:
        reason_opts = sorted([r for r in df['reason'].unique() if str(r).strip()])
        selected_reasons = st.multiselect("Reason", reason_opts, key='browser_reason')

    with filter_row[2]:
        director_search = st.text_input("Director search", key='browser_director')

    with filter_row[3]:
        title_search = st.text_input("Title search", key='browser_title')

    conf_range = st.slider("Confidence range", 0.0, 1.0, (0.0, 1.0),
                            step=0.1, key='browser_conf')

    # --- Apply filters ---
    filtered = df.copy()

    if selected_tiers:
        filtered = filtered[filtered['tier'].isin(selected_tiers)]
    if selected_reasons:
        filtered = filtered[filtered['reason'].isin(selected_reasons)]
    if director_search:
        filtered = filtered[
            filtered['director'].str.lower().str.contains(
                director_search.lower(), na=False)
        ]
    if title_search:
        filtered = filtered[
            filtered['title'].str.lower().str.contains(
                title_search.lower(), na=False)
        ]
    filtered = filtered[
        (filtered['confidence'] >= conf_range[0])
        & (filtered['confidence'] <= conf_range[1])
    ]

    st.write(f"**{len(filtered):,}** films match your filters")
    st.divider()

    # --- Results table ---
    # Use filename as display label when title is unpopulated (e.g. library_audit.csv)
    view_df = filtered.copy()
    if view_df['title'].astype(str).str.strip().eq('').all():
        view_df['title'] = view_df['filename']
    display_cols = ['title', 'year', 'director', 'tier', 'decade',
                    'subdirectory', 'confidence', 'reason']
    display_cols = [c for c in display_cols if c in view_df.columns]

    st.dataframe(
        view_df[display_cols].sort_values(['tier', 'title']).reset_index(drop=True),
        use_container_width=True,
        height=500,
        column_config={
            'confidence': st.column_config.ProgressColumn(
                "Confidence", min_value=0.0, max_value=1.0, format="%.1f"),
            'year': st.column_config.NumberColumn("Year", format="%d"),
        },
    )

    # --- Detail expanders ---
    st.divider()
    st.subheader("Film Details")

    if len(filtered) > 200:
        st.info("Showing detail cards for the first 200 results. "
                "Narrow your filters to see more.")
        show_df = filtered.head(200)
    else:
        show_df = filtered

    for _, row in show_df.iterrows():
        label = f"{row['title']} ({int(row['year']) if pd.notna(row['year']) and row['year'] > 0 else '?'})"
        with st.expander(label):
            detail_cols = st.columns(3)
            detail_cols[0].write(f"**Director:** {row['director'] or '—'}")
            detail_cols[0].write(f"**Tier:** {row['tier']}")
            detail_cols[0].write(f"**Decade:** {row['decade'] or '—'}")
            detail_cols[1].write(f"**Subdirectory:** {row['subdirectory'] or '—'}")
            detail_cols[1].write(f"**Confidence:** {row['confidence']:.1f}")
            detail_cols[1].write(f"**Language:** {row['language'] or '—'}")
            detail_cols[2].write(f"**Country:** {row['country'] or '—'}")
            detail_cols[2].write(f"**User Tag:** {row['user_tag'] or '—'}")
            detail_cols[2].write(f"**Reason:** {row['reason'] or '—'}")
            st.caption(f"**File:** `{row['filename']}`")
            st.caption(f"**Destination:** `{row['destination']}`")


def render_sidebar():
    """Render sidebar and return (selected_csv_path, section_name, is_diagnostic)."""
    with st.sidebar:
        st.title("\U0001F3AC Film Sorting DB")
        st.caption("Two-signal health monitor")

        st.divider()

        # Typed manifest selector
        output_dir = PROJECT_ROOT / 'output'
        primary, diagnostic = find_manifests(output_dir)

        if not primary and not diagnostic:
            st.error("No CSV manifests found in output/")
            st.stop()

        st.caption("**Classification manifests**")
        primary_names = [p.name for p in primary]
        diag_names = [d.name for d in diagnostic]
        all_options = primary_names + (["── Diagnostic (read-only) ──"] if diag_names else []) + diag_names

        selected_name = st.selectbox(
            "Manifest", all_options,
            help="Primary: sorting_manifest.csv, library_audit.csv\nDiagnostic: reaudit_report.csv, review_queue.csv",
        )

        is_diagnostic = selected_name in diag_names
        if selected_name == "── Diagnostic (read-only) ──":
            st.warning("Select a manifest above or below the separator.")
            st.stop()

        selected_path = output_dir / selected_name

        # Manifest info
        mtime = datetime.fromtimestamp(selected_path.stat().st_mtime)
        fmt = "diagnostic" if is_diagnostic else detect_format(pd.read_csv(selected_path, nrows=0).columns)
        st.caption(f"Format: **{fmt}** | Modified: {mtime:%b %d %H:%M}")
        if is_diagnostic:
            st.info("Diagnostic file — read-only view", icon="ℹ️")

        st.divider()

        # Section navigation — 2 options only
        section = st.radio(
            "Section",
            ["System Health", "Film Browser"],
            label_visibility='collapsed',
        )

        st.divider()
        if LIB_AVAILABLE:
            st.caption("\u2705 lib/ modules loaded")
        else:
            st.caption("\u26A0\uFE0F lib/ modules unavailable — CSV-only mode")

    return str(selected_path), section, is_diagnostic


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def detect_routing_contract(csv_path: str, df: pd.DataFrame) -> str:
    """Detect routing contract from filename convention or manifest data.

    Returns 'scholarship_only' if:
      - filename contains 'scholarship' (naming convention), OR
      - manifest contains no explicit_lookup, Core, or Reference rows (data inspection).
    Otherwise returns 'legacy'.
    """
    name = Path(csv_path).name.lower()
    if 'scholarship' in name:
        return 'scholarship_only'
    # Data inspection: scholarship manifest has no Core/Reference tiers or explicit_lookup reason
    has_core_ref = df['tier'].isin(['Core', 'Reference']).any()
    has_explicit = (df['reason'] == 'explicit_lookup').any() if 'reason' in df.columns else False
    if not has_core_ref and not has_explicit and len(df) > 0:
        return 'scholarship_only'
    return 'legacy'


def render_contract_banner(contract: str):
    """Show a contract context banner when viewing a scholarship-only manifest."""
    if contract == 'scholarship_only':
        st.info(
            "**Contract: scholarship_only** — "
            "This manifest uses the scholarship-only routing contract: "
            "no `explicit_lookup`, no `Core` tier, no `Reference` tier. "
            "Tier distribution reflects autonomous two-signal routing only. "
            "Generate with: `python classify.py <src> --routing-contract scholarship_only`",
            icon="ℹ️",
        )


def main():
    csv_path, section, is_diagnostic = render_sidebar()
    df = load_manifest(csv_path)

    # Show contract banner if this is a scholarship-only manifest
    contract = detect_routing_contract(csv_path, df)
    render_contract_banner(contract)

    if section == "System Health":
        render_collection_overview(df)
        st.divider()
        render_pipeline_health(df)
    elif section == "Film Browser":
        render_film_browser(df)


if __name__ == '__main__':
    main()
