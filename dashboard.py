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
    'explicit_lookup':        1.0,
    'core_director':          1.0,
    'core_director_exact':    1.0,
    'reference_canon':        1.0,
    'user_tag_recovery':      0.8,
    'user_tag':               0.8,
    'country_satellite':      0.7,
    'country_decade_satellite': 0.7,
    'tmdb_satellite':         0.7,
    'satellite':              0.7,
    'popcorn':                0.6,
}

# Fallback satellite caps (used if lib/ import fails)
FALLBACK_SATELLITE_CAPS = {
    'Giallo': 30,
    'Pinku Eiga': 35,
    'Brazilian Exploitation': 45,
    'Hong Kong Action': 65,
    'American Exploitation': 80,
    'European Sexploitation': 25,
    'Blaxploitation': 20,
    'Music Films': 20,
    'Cult Oddities': 50,
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
REFERENCE_CANON = {}
COUNTRY_TO_WAVE = {}
SATELLITE_ROUTING_RULES = {}

try:
    from lib.constants import (
        REFERENCE_CANON as _RC,
        COUNTRY_TO_WAVE as _CW,
        SATELLITE_ROUTING_RULES as _SRR,
        SATELLITE_TENTPOLES as _ST
    )
    REFERENCE_CANON = _RC
    COUNTRY_TO_WAVE = _CW
    SATELLITE_ROUTING_RULES = _SRR
    SATELLITE_TENTPOLES = _ST
    LIB_AVAILABLE = True
except ImportError:
    SATELLITE_TENTPOLES = {}
    pass

# Import validation helpers
try:
    from lib.dashboard_validation import DashboardValidator, build_destination
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    DashboardValidator = None
    def build_destination(tier, decade, subdirectory):
        """Fallback destination builder."""
        return f"{tier}/{decade or 'Unknown'}/"


@st.cache_resource
def load_core_directors():
    """Load CoreDirectorDatabase (cached as resource since it's a class)."""
    try:
        from lib.core_directors import CoreDirectorDatabase
        whitelist = PROJECT_ROOT / 'docs' / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        if not whitelist.exists():
            whitelist = PROJECT_ROOT / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        if whitelist.exists():
            return CoreDirectorDatabase(whitelist)
    except Exception:
        pass
    return None


@st.cache_data
def load_satellite_caps():
    """Load satellite category caps from SatelliteClassifier or use fallback."""
    try:
        from lib.satellite import SatelliteClassifier
        sc = SatelliteClassifier()
        return dict(sc.caps)
    except Exception:
        return dict(FALLBACK_SATELLITE_CAPS)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def find_manifests(output_dir: Path):
    """Scan output/ for CSV manifests, return list sorted by mtime (newest first)."""
    if not output_dir.exists():
        return []
    csvs = sorted(output_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
    # Exclude tiny helper files (< 1 KB)
    return [c for c in csvs if c.stat().st_size > 1024]


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

    # --- Tier donut + Decade stacked bar ---
    left, right = st.columns(2)

    with left:
        st.subheader("Tier Distribution")
        ordered = [t for t in TIER_ORDER if t in tier_counts.index]
        fig = go.Figure(data=[go.Pie(
            labels=ordered,
            values=[int(tier_counts[t]) for t in ordered],
            hole=0.5,
            marker_colors=[TIER_COLORS.get(t, '#E8E8E8') for t in ordered],
            textinfo='label+percent',
            hovertemplate='%{label}: %{value} films (%{percent})<extra></extra>',
            sort=False,
        )])
        fig.update_layout(
            annotations=[dict(text=str(total), x=0.5, y=0.5, font_size=28,
                              showarrow=False)],
            height=420, margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation='h', y=-0.05),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
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
            # Sort decades chronologically
            decade_order = sorted(cross['decade'].unique())
            tier_order_filtered = [t for t in TIER_ORDER if t in cross['tier'].unique()]
            fig = px.bar(
                cross, x='decade', y='count', color='tier',
                color_discrete_map=TIER_COLORS,
                category_orders={'decade': decade_order, 'tier': tier_order_filtered},
                barmode='stack',
            )
            fig.update_layout(height=420, margin=dict(t=20, b=40),
                              xaxis_title='', yaxis_title='Films',
                              legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No decade data available for classified films.")

    st.divider()

    # --- Core directors panel + Satellite fill rates ---
    left2, right2 = st.columns(2)

    with left2:
        st.subheader("Core Directors")
        core_db = load_core_directors()
        core_df = df[df['tier'] == 'Core']

        if core_db and core_db.directors_by_decade:
            for decade in sorted(core_db.directors_by_decade.keys()):
                directors = sorted(core_db.directors_by_decade[decade])
                with st.expander(f"{decade} ({len(directors)} directors)"):
                    for director in directors:
                        count = len(core_df[
                            core_df['director'].str.lower().str.strip()
                            == director.lower().strip()
                        ])
                        dot = "\U0001F7E2" if count > 0 else "\u26AA"
                        st.write(f"{dot} **{director}** — {count} film{'s' if count != 1 else ''}")
        else:
            # Fallback: show directors from manifest
            if len(core_df):
                for director, group in core_df.groupby('director'):
                    if director:
                        st.write(f"**{director}** — {len(group)} films")
            else:
                st.info("No Core films found in this manifest.")

    with right2:
        st.subheader("Satellite Category Fill Rates")
        caps = load_satellite_caps()
        sat_df = df[df['tier'] == 'Satellite']
        cat_counts = sat_df['subdirectory'].value_counts().to_dict()

        rows = []
        for cat, cap in sorted(caps.items(), key=lambda x: -x[1]):
            current = cat_counts.get(cat, 0)
            fill_pct = current / cap if cap else 0
            rows.append({'category': cat, 'current': current, 'cap': cap,
                         'fill_pct': fill_pct})

        if rows:
            cat_df = pd.DataFrame(rows)
            fig = go.Figure()
            # Background cap bars
            fig.add_trace(go.Bar(
                y=cat_df['category'], x=cat_df['cap'],
                orientation='h',
                marker_color='rgba(200,200,200,0.3)',
                name='Cap',
                hovertemplate='Cap: %{x}<extra></extra>',
            ))
            # Foreground current bars
            fig.add_trace(go.Bar(
                y=cat_df['category'], x=cat_df['current'],
                orientation='h',
                marker_color=[_fill_color(r['fill_pct']) for _, r in cat_df.iterrows()],
                name='Current',
                text=[f"{r['current']}/{r['cap']}" for _, r in cat_df.iterrows()],
                textposition='inside',
                hovertemplate='%{y}: %{x} films<extra></extra>',
            ))
            fig.update_layout(
                barmode='overlay', height=max(300, len(rows) * 45),
                margin=dict(t=10, b=30, l=10, r=10),
                showlegend=False,
                yaxis=dict(autorange='reversed'),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No satellite category data available.")

    st.divider()

    # --- Reference Canon Tracker ---
    st.subheader("Reference Canon Tracker")
    if REFERENCE_CANON:
        # Deduplicate alternative normalisations (e.g. 'et the extraterrestrial' vs 'e t ...')
        seen_years = {}
        for (title, year), _ in REFERENCE_CANON.items():
            key = year  # group by year to dedup
            display = title.replace('_', ' ').title()
            # Keep shorter display title as canonical when year matches
            if (display, year) not in seen_years:
                seen_years[(display, year)] = (title, year)

        # Build set of films in collection (normalised title + year)
        try:
            from lib.normalization import normalize_for_lookup
            collection_keys = set()
            for _, row in df.iterrows():
                if row['title'] and pd.notna(row['year']) and row['year'] > 0:
                    norm = normalize_for_lookup(str(row['title']),
                                                strip_format_signals=True)
                    collection_keys.add((norm, int(row['year'])))
        except ImportError:
            # Fallback: simple lowercase matching
            collection_keys = set()
            for _, row in df.iterrows():
                if row['title'] and pd.notna(row['year']) and row['year'] > 0:
                    collection_keys.add((row['title'].lower().strip(), int(row['year'])))

        # Match canon against collection
        canon_items = []
        for (display, year), (norm_title, canon_year) in sorted(
                seen_years.items(), key=lambda x: x[0][1]):
            present = (norm_title, canon_year) in collection_keys
            canon_items.append((display, year, present))

        # Remove near-duplicate display titles (e.g. E T The Extraterrestrial vs Et The...)
        deduped = {}
        for display, year, present in canon_items:
            if year not in deduped:
                deduped[year] = (display, year, present)
            else:
                # Keep whichever is present, or the first one
                existing = deduped[year]
                if present and not existing[2]:
                    deduped[year] = (display, year, present)

        canon_list = list(deduped.values())
        in_count = sum(1 for _, _, p in canon_list if p)
        gap_count = len(canon_list) - in_count

        st.write(f"**{in_count}** of **{len(canon_list)}** canon films in collection "
                 f"| **{gap_count}** gaps")

        n_cols = 5
        grid_cols = st.columns(n_cols)
        for i, (display, year, present) in enumerate(canon_list):
            color = '#d4edda' if present else '#f8d7da'
            icon = "\u2705" if present else "\u274C"
            grid_cols[i % n_cols].markdown(
                f'<div style="background:{color};padding:6px 8px;margin:3px 0;'
                f'border-radius:6px;font-size:13px;">'
                f'{icon} {display} ({year})</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Reference canon data not available (lib/constants.py not importable).")


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
        display_cols = ['title', 'year', 'director', 'reason', 'language', 'country']
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[display_cols].reset_index(drop=True),
            use_container_width=True,
            height=400,
        )
    else:
        st.success("No unsorted films — everything is classified!")

    st.divider()

    # --- Language / Country distribution ---
    st.subheader("Language & Country Distribution")
    left3, right3 = st.columns(2)

    with left3:
        lang_counts = (df['language'].str.strip()
                       .replace('', pd.NA).dropna()
                       .value_counts().head(15).reset_index())
        lang_counts.columns = ['language', 'count']
        if len(lang_counts):
            fig = px.bar(lang_counts, y='language', x='count', orientation='h',
                         color_discrete_sequence=['#DD8452'])
            fig.update_layout(height=max(250, len(lang_counts) * 30),
                              margin=dict(t=10, b=20, l=10, r=10),
                              yaxis_title='', xaxis_title='Films',
                              yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No language data in this manifest.")

    with right3:
        country_counts = (df['country'].str.strip()
                          .replace('', pd.NA).dropna()
                          .value_counts().head(15).reset_index())
        country_counts.columns = ['country', 'count']
        if len(country_counts):
            fig = px.bar(country_counts, y='country', x='count', orientation='h',
                         color_discrete_sequence=['#4C72B0'])
            fig.update_layout(height=max(250, len(country_counts) * 30),
                              margin=dict(t=10, b=20, l=10, r=10),
                              yaxis_title='', xaxis_title='Films',
                              yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No country data in this manifest.")


# ---------------------------------------------------------------------------
# Section 3 – Film Browser
# ---------------------------------------------------------------------------

def render_edit_mode(filtered_df: pd.DataFrame, full_df: pd.DataFrame):
    """Render edit mode with inline editing and validation."""
    st.subheader("Edit Film Classifications")
    st.info("⚠️ Changes will be saved to the manifest CSV. Use Export mode to add permanent entries to SORTING_DATABASE.md")

    # Editable columns
    editable_cols = ['title', 'year', 'director', 'tier', 'decade', 'subdirectory', 'filename']

    # Decade options (1920s to 2020s)
    decade_opts = [f"{y}s" for y in range(1920, 2030, 10)]

    # Satellite category options from SATELLITE_ROUTING_RULES
    satellite_cats = sorted(SATELLITE_ROUTING_RULES.keys()) if SATELLITE_ROUTING_RULES else []

    # Configure column editors
    edited_df = st.data_editor(
        filtered_df[editable_cols].copy(),
        column_config={
            'filename': st.column_config.TextColumn('Filename', disabled=True, width='medium'),
            'title': st.column_config.TextColumn('Title', width='medium'),
            'year': st.column_config.NumberColumn('Year', min_value=1920, max_value=2029, width='small'),
            'director': st.column_config.TextColumn('Director', width='medium'),
            'tier': st.column_config.SelectboxColumn(
                'Tier',
                options=TIER_ORDER,
                required=True,
                width='small'
            ),
            'decade': st.column_config.SelectboxColumn(
                'Decade',
                options=decade_opts,
                required=False,
                width='small'
            ),
            'subdirectory': st.column_config.TextColumn(
                'Subdirectory',
                help='Director name (Core) or Category name (Satellite)',
                width='medium'
            ),
        },
        hide_index=True,
        num_rows="fixed",
        use_container_width=True,
        key='film_editor'
    )

    # Validate edits
    validation_results = validate_edits(edited_df)

    # Display validation results
    if validation_results['has_errors'] or validation_results['has_warnings']:
        st.divider()
        if validation_results['has_errors']:
            st.error(f"❌ {len(validation_results['errors'])} validation errors found")
            for err in validation_results['errors'][:10]:  # Show first 10
                st.error(f"Row {err['row']}: {err['message']}")
            if len(validation_results['errors']) > 10:
                st.caption(f"... and {len(validation_results['errors']) - 10} more errors")

        if validation_results['has_warnings']:
            st.warning(f"⚠️ {len(validation_results['warnings'])} warnings")
            for warn in validation_results['warnings'][:5]:  # Show first 5
                st.warning(f"Row {warn['row']}: {warn['message']}")
            if len(validation_results['warnings']) > 5:
                st.caption(f"... and {len(validation_results['warnings']) - 5} more warnings")

    # Save button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        can_save = not validation_results['has_errors']
        if st.button("💾 Save Changes", type="primary", disabled=not can_save):
            csv_path = save_edited_csv(edited_df, full_df)
            st.success(f"✅ Changes saved to {csv_path.name}!")
            st.info("Reloading dashboard...")
            st.cache_data.clear()
            st.rerun()

    with col2:
        if validation_results['has_errors']:
            st.caption("Fix validation errors before saving")
        else:
            st.caption("Ready to save")


def render_export_mode(filtered_df: pd.DataFrame):
    """Render export mode for generating SORTING_DATABASE.md entries."""
    st.subheader("Export to SORTING_DATABASE.md")
    st.info("📝 Generate markdown entries to manually add to docs/SORTING_DATABASE.md")

    # Group films by tier for selection
    tier_groups = filtered_df.groupby('tier')

    selected_films = []
    st.write("**Select films to export:**")

    for tier in ['Core', 'Reference', 'Satellite', 'Popcorn']:
        if tier in tier_groups.groups:
            tier_df = tier_groups.get_group(tier)
            with st.expander(f"{tier} ({len(tier_df)} films)", expanded=False):
                # Select all checkbox
                select_all = st.checkbox(f"Select all {tier}", key=f"select_all_{tier}")

                for idx, row in tier_df.iterrows():
                    year_display = int(row['year']) if pd.notna(row['year']) else '?'
                    label = f"{row['title']} ({year_display})"

                    is_selected = select_all or st.checkbox(
                        label,
                        key=f"export_{idx}",
                        value=select_all
                    )

                    if is_selected:
                        selected_films.append(row)

    st.divider()

    if selected_films:
        st.write(f"**{len(selected_films)} films selected**")

        if st.button("📋 Generate SORTING_DATABASE.md Entries", type="primary"):
            markdown_text = generate_sorting_database_entries(selected_films)

            st.success("✅ Generated! Copy the text below:")
            st.code(markdown_text, language='markdown')

            st.divider()
            st.caption("**To apply:**")
            st.caption("1. Copy the text above")
            st.caption("2. Open docs/SORTING_DATABASE.md in your text editor")
            st.caption("3. Find the appropriate decade section")
            st.caption("4. Paste the entries in the correct tier subsection")
            st.caption("5. Re-run: `python classify.py <source_dir>`")
            st.caption("6. Films will now use reason=explicit_lookup (confidence=1.0)")
    else:
        st.warning("Select at least one film to export")


def validate_edits(edited_df: pd.DataFrame) -> dict:
    """
    Validate edited dataframe against business rules.

    Returns dict with:
    - has_errors: bool
    - has_warnings: bool
    - errors: list of {row, field, message}
    - warnings: list of {row, field, message}
    """
    errors = []
    warnings = []

    for idx, row in edited_df.iterrows():
        # Hard gate: Year required for non-Unsorted
        if row['tier'] not in ['Unsorted', 'Staging'] and pd.isna(row['year']):
            errors.append({
                'row': idx,
                'field': 'year',
                'message': f"{row['filename']}: Year required for {row['tier']} tier"
            })

        # Core validation
        if row['tier'] == 'Core':
            if not row.get('subdirectory') or str(row['subdirectory']).strip() == '':
                errors.append({
                    'row': idx,
                    'field': 'subdirectory',
                    'message': f"{row['filename']}: Core requires director subdirectory"
                })
            if not row.get('decade') or str(row['decade']).strip() == '':
                errors.append({
                    'row': idx,
                    'field': 'decade',
                    'message': f"{row['filename']}: Core requires decade"
                })

        # Satellite validation
        if row['tier'] == 'Satellite':
            if not row.get('subdirectory') or str(row['subdirectory']).strip() == '':
                errors.append({
                    'row': idx,
                    'field': 'subdirectory',
                    'message': f"{row['filename']}: Satellite requires category subdirectory"
                })
            elif SATELLITE_ROUTING_RULES and row['subdirectory'] not in SATELLITE_ROUTING_RULES:
                errors.append({
                    'row': idx,
                    'field': 'subdirectory',
                    'message': f"{row['filename']}: Invalid satellite category '{row['subdirectory']}'"
                })
            # Check decade bounds
            if SATELLITE_ROUTING_RULES and row.get('subdirectory') in SATELLITE_ROUTING_RULES:
                valid_decades = SATELLITE_ROUTING_RULES[row['subdirectory']].get('decades')
                if valid_decades and row.get('decade') and row['decade'] not in valid_decades:
                    errors.append({
                        'row': idx,
                        'field': 'decade',
                        'message': f"{row['filename']}: {row['subdirectory']} only valid in {valid_decades}"
                    })

        # Reference validation (warnings)
        if row['tier'] == 'Reference':
            if row.get('subdirectory') and str(row['subdirectory']).strip() != '':
                warnings.append({
                    'row': idx,
                    'field': 'subdirectory',
                    'message': f"{row['filename']}: Reference tier doesn't use subdirectory"
                })
            if not row.get('decade') or str(row['decade']).strip() == '':
                errors.append({
                    'row': idx,
                    'field': 'decade',
                    'message': f"{row['filename']}: Reference requires decade"
                })

        # Popcorn validation (warnings)
        if row['tier'] == 'Popcorn':
            if row.get('subdirectory') and str(row['subdirectory']).strip() != '':
                warnings.append({
                    'row': idx,
                    'field': 'subdirectory',
                    'message': f"{row['filename']}: Popcorn tier doesn't use subdirectory"
                })
            if not row.get('decade') or str(row['decade']).strip() == '':
                errors.append({
                    'row': idx,
                    'field': 'decade',
                    'message': f"{row['filename']}: Popcorn requires decade"
                })

    return {
        'has_errors': len(errors) > 0,
        'has_warnings': len(warnings) > 0,
        'errors': errors,
        'warnings': warnings
    }


def save_edited_csv(edited_df: pd.DataFrame, full_df: pd.DataFrame) -> Path:
    """Save edited dataframe back to CSV, rebuilding destinations."""
    # Get the current manifest path from sidebar
    output_dir = PROJECT_ROOT / 'output'
    csv_path = output_dir / 'sorting_manifest.csv'

    # Create a copy of full dataframe
    updated_df = full_df.copy()

    # Update edited rows
    for idx, edited_row in edited_df.iterrows():
        # Find matching row in full_df by filename
        mask = updated_df['filename'] == edited_row['filename']

        if mask.any():
            # Update fields
            updated_df.loc[mask, 'title'] = edited_row['title']
            updated_df.loc[mask, 'year'] = edited_row['year'] if pd.notna(edited_row['year']) else ''
            updated_df.loc[mask, 'director'] = edited_row['director'] if pd.notna(edited_row['director']) else ''
            updated_df.loc[mask, 'tier'] = edited_row['tier']
            updated_df.loc[mask, 'decade'] = edited_row['decade'] if pd.notna(edited_row['decade']) else ''
            updated_df.loc[mask, 'subdirectory'] = edited_row['subdirectory'] if pd.notna(edited_row['subdirectory']) else ''

            # Rebuild destination
            destination = build_destination(
                edited_row['tier'],
                edited_row['decade'] if pd.notna(edited_row['decade']) else '',
                edited_row['subdirectory'] if pd.notna(edited_row['subdirectory']) else ''
            )
            updated_df.loc[mask, 'destination'] = destination

            # Update confidence and reason
            updated_df.loc[mask, 'confidence'] = 0.9
            updated_df.loc[mask, 'reason'] = 'manual_dashboard_edit'

    # Write CSV with proper quoting
    updated_df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)

    return csv_path


def generate_sorting_database_entries(films: list) -> str:
    """
    Generate markdown-formatted SORTING_DATABASE.md entries.
    Groups by decade and tier for readability.
    """
    # Group by decade, then tier
    grouped = defaultdict(lambda: defaultdict(list))

    for film in films:
        decade = film['decade'] if pd.notna(film['decade']) else 'Unknown'
        tier = film['tier']
        grouped[decade][tier].append(film)

    lines = []

    for decade in sorted(grouped.keys()):
        if decade == 'Unknown':
            continue

        lines.append(f"\n## {decade.upper()} FILMS")
        lines.append("")

        for tier in ['Core', 'Reference', 'Satellite', 'Popcorn']:
            if tier in grouped[decade]:
                lines.append(f"### {tier}")

                for film in sorted(grouped[decade][tier], key=lambda x: str(x['title'])):
                    title = film['title']
                    year = int(film['year']) if pd.notna(film['year']) else ''
                    dest = film['destination']

                    entry = f"- {title} ({year}) → {dest}"
                    lines.append(entry)

                lines.append("")

    if not lines:
        return "# No valid films to export (missing decade information)"

    return '\n'.join(lines)


def render_film_browser(df: pd.DataFrame):
    st.header("Film Browser")

    # --- Filter controls ---
    filter_row = st.columns(4)

    with filter_row[0]:
        tier_opts = [t for t in TIER_ORDER if t in df['tier'].unique()]
        selected_tiers = st.multiselect("Tier", tier_opts, default=tier_opts,
                                         key='browser_tier')
    with filter_row[1]:
        decade_opts = sorted([d for d in df['decade'].unique() if d.strip()])
        selected_decades = st.multiselect("Decade", decade_opts, key='browser_decade')

    with filter_row[2]:
        director_search = st.text_input("Director search", key='browser_director')

    with filter_row[3]:
        title_search = st.text_input("Title search", key='browser_title')

    filter_row2 = st.columns(3)
    with filter_row2[0]:
        conf_range = st.slider("Confidence range", 0.0, 1.0, (0.0, 1.0),
                                step=0.1, key='browser_conf')
    with filter_row2[1]:
        lang_opts = sorted([l for l in df['language'].unique() if l.strip()])
        selected_langs = st.multiselect("Language", lang_opts, key='browser_lang')
    with filter_row2[2]:
        country_opts = sorted([c for c in df['country'].unique() if c.strip()])
        selected_countries = st.multiselect("Country", country_opts,
                                             key='browser_country')

    # --- Apply filters ---
    filtered = df.copy()

    if selected_tiers:
        filtered = filtered[filtered['tier'].isin(selected_tiers)]
    if selected_decades:
        filtered = filtered[filtered['decade'].isin(selected_decades)]
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
    if selected_langs:
        filtered = filtered[filtered['language'].isin(selected_langs)]
    if selected_countries:
        filtered = filtered[filtered['country'].isin(selected_countries)]

    st.write(f"**{len(filtered):,}** films match your filters")

    # --- Mode selector ---
    st.divider()
    mode = st.radio(
        "Mode",
        ["View", "Edit", "Export"],
        horizontal=True,
        key='browser_mode',
        help="View: read-only display | Edit: modify classifications | Export: generate SORTING_DATABASE.md entries"
    )

    if mode == "View":
        # --- Results table ---
        display_cols = ['title', 'year', 'director', 'tier', 'decade',
                        'subdirectory', 'confidence', 'reason']
        display_cols = [c for c in display_cols if c in filtered.columns]

        st.dataframe(
            filtered[display_cols].sort_values(['tier', 'title']).reset_index(drop=True),
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

    elif mode == "Edit":
        render_edit_mode(filtered, df)

    elif mode == "Export":
        render_export_mode(filtered)


# ---------------------------------------------------------------------------
# Section 4 – Thread Discovery
# ---------------------------------------------------------------------------

def render_thread_discovery(df: pd.DataFrame):
    st.header("Thread Discovery")
    st.caption("Discover thematic connections using TMDb keywords and tentpole films")

    # Check if thread index exists
    thread_index_path = PROJECT_ROOT / 'output' / 'thread_keywords.json'

    if not thread_index_path.exists():
        st.warning("⚠️ Thread keyword index not found")
        st.info("Run: `python scripts/build_thread_index.py --summary` to build the index")

        if st.button("📚 View Tentpole Films"):
            if SATELLITE_TENTPOLES:
                st.subheader("Tentpole Films by Category")
                for category, tentpoles in sorted(SATELLITE_TENTPOLES.items()):
                    with st.expander(f"{category} ({len(tentpoles)} tentpoles)", expanded=False):
                        for title, year, director in tentpoles:
                            st.write(f"• **{title}** ({year}) — {director}")
            else:
                st.error("SATELLITE_TENTPOLES not available (import failed)")
        return

    # Load thread index
    try:
        with open(thread_index_path, 'r', encoding='utf-8') as f:
            thread_index = json.load(f)
    except Exception as e:
        st.error(f"Error loading thread index: {e}")
        return

    st.divider()

    # --- Panel 1: Discover Threads for a Film ---
    st.subheader("🎬 Discover Threads for a Film")

    col1, col2 = st.columns([3, 1])
    with col1:
        film_title = st.text_input("Enter film title:", placeholder="e.g., Deep Red, Faster Pussycat Kill Kill")
    with col2:
        film_year = st.number_input("Year (optional):", min_value=1900, max_value=2030, value=None, step=1)

    col3, col4 = st.columns([2, 2])
    with col3:
        min_overlap = st.slider("Minimum overlap threshold:", 0.0, 0.5, 0.15, 0.05)

    if film_title:
        try:
            # Import thread discovery functions
            from lib.rag.query import discover_threads

            threads = discover_threads(film_title, film_year, min_overlap=min_overlap)

            if threads:
                st.success(f"✅ Found {len(threads)} thread connection(s)")

                # Radar chart
                categories = [t['category'] for t in threads]
                scores = [t['jaccard_score'] for t in threads]

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=categories,
                    fill='toself',
                    name=film_title,
                    line_color='#DD8452',
                    fillcolor='rgba(221, 132, 82, 0.3)'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, max(scores) * 1.1])
                    ),
                    showlegend=False,
                    height=400,
                    margin=dict(t=40, b=40, l=60, r=60)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Details table
                st.subheader("Thread Connections")
                for i, thread in enumerate(threads, 1):
                    with st.expander(f"{i}. {thread['category']} — Jaccard: {thread['jaccard_score']:.3f}", expanded=(i==1)):
                        st.write(f"**Shared keywords ({thread['overlap_count']}):**")
                        shared = thread['shared_keywords'][:15]
                        st.write(", ".join(shared))
                        if len(thread['shared_keywords']) > 15:
                            st.caption(f"... and {len(thread['shared_keywords']) - 15} more")
            else:
                st.info("No threads found above the threshold. Try lowering the minimum overlap.")

        except FileNotFoundError as e:
            st.error(f"Error: {e}")
            st.info("Make sure TMDb API key is configured in config.yaml")
        except Exception as e:
            st.error(f"Error discovering threads: {e}")

    st.divider()

    # --- Panel 2: Category Keyword Profiles ---
    st.subheader("🔍 Category Keyword Profiles")

    col1, col2 = st.columns([2, 2])
    with col1:
        if SATELLITE_TENTPOLES:
            selected_category = st.selectbox("Select category:", sorted(SATELLITE_TENTPOLES.keys()))
        else:
            selected_category = st.selectbox("Select category:", sorted(thread_index.keys()))

    with col2:
        top_k = st.slider("Number of keywords:", 10, 50, 20, 5)

    if selected_category and selected_category in thread_index:
        category_data = thread_index[selected_category]
        keywords = category_data['keywords'][:top_k]

        # Bar chart of keyword frequencies
        kw_df = pd.DataFrame(keywords)
        fig = px.bar(
            kw_df,
            y='keyword',
            x='count',
            orientation='h',
            title=f"Top {len(keywords)} Keywords for {selected_category}",
            color='count',
            color_continuous_scale='Tealgrn'
        )
        fig.update_layout(
            height=max(400, len(keywords) * 25),
            yaxis=dict(autorange='reversed'),
            yaxis_title='',
            xaxis_title='Frequency across tentpoles',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tentpole films
        with st.expander("📚 Tentpole Films"):
            if 'tentpole_films' in category_data:
                for film in category_data['tentpole_films']:
                    st.write(f"• **{film['title']}** ({film['year']}) — {film['director']}")
                    st.caption(f"  {film.get('keyword_count', 0)} keywords")

    st.divider()

    # --- Panel 3: Thread Coverage in Collection ---
    st.subheader("📊 Thread Coverage in Collection")

    # Count films with keywords in manifest
    # This would require keywords to be in the manifest, which they're not yet
    # For now, show index stats

    coverage_data = []
    for category, data in thread_index.items():
        coverage_data.append({
            'category': category,
            'unique_keywords': len(data['keywords']),
            'tentpoles': data['tentpole_count'],
            'query_failures': len(data.get('query_failures', []))
        })

    coverage_df = pd.DataFrame(coverage_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            coverage_df,
            x='category',
            y='unique_keywords',
            title="Unique Keywords per Category",
            color='unique_keywords',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=coverage_df['category'],
            y=coverage_df['tentpoles'],
            name='Tentpoles',
            marker_color='#55A868'
        ))
        fig.add_trace(go.Bar(
            x=coverage_df['category'],
            y=coverage_df['query_failures'],
            name='Query Failures',
            marker_color='#C44E52'
        ))
        fig.update_layout(
            title="Tentpoles vs Query Failures",
            xaxis_tickangle=-45,
            barmode='group',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- Panel 4: Index Statistics ---
    with st.expander("📈 Index Statistics"):
        total_keywords = sum(len(data['keywords']) for data in thread_index.values())
        total_tentpoles = sum(data['tentpole_count'] for data in thread_index.values())
        total_failures = sum(len(data.get('query_failures', [])) for data in thread_index.values())

        cols = st.columns(4)
        cols[0].metric("Categories", len(thread_index))
        cols[1].metric("Total Tentpoles", total_tentpoles)
        cols[2].metric("Unique Keywords", total_keywords)
        cols[3].metric("Query Failures", total_failures)

        if total_failures > 0:
            st.warning("Some tentpole films failed to query from TMDb")
            for category, data in thread_index.items():
                failures = data.get('query_failures', [])
                if failures:
                    st.write(f"**{category}:** {', '.join(failures)}")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render sidebar and return (selected_csv_path, section_name)."""
    with st.sidebar:
        st.title("\U0001F3AC Film Sorting DB")
        st.caption("Collection dashboard")

        st.divider()

        # Manifest selector
        output_dir = PROJECT_ROOT / 'output'
        manifests = find_manifests(output_dir)

        if not manifests:
            st.error("No CSV manifests found in output/")
            st.stop()

        manifest_names = [m.name for m in manifests]
        selected_name = st.selectbox("Manifest", manifest_names,
                                      help="CSV files in output/, sorted by newest")
        selected_path = output_dir / selected_name

        # Manifest info
        mtime = datetime.fromtimestamp(selected_path.stat().st_mtime)
        temp_df = pd.read_csv(selected_path, nrows=0)
        fmt = detect_format(temp_df.columns)
        st.caption(f"Format: **{fmt}** | Modified: {mtime:%b %d %H:%M}")

        st.divider()

        # Section navigation
        section = st.radio(
            "Section",
            ["Collection Overview", "Pipeline Health", "Film Browser", "Thread Discovery"],
            label_visibility='collapsed',
        )

        st.divider()
        if LIB_AVAILABLE:
            st.caption("\u2705 lib/ modules loaded")
        else:
            st.caption("\u26A0\uFE0F lib/ modules unavailable — running in CSV-only mode")

    return str(selected_path), section


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    csv_path, section = render_sidebar()
    df = load_manifest(csv_path)

    if section == "Collection Overview":
        render_collection_overview(df)
    elif section == "Pipeline Health":
        render_pipeline_health(df)
    elif section == "Film Browser":
        render_film_browser(df)
    elif section == "Thread Discovery":
        render_thread_discovery(df)


if __name__ == '__main__':
    main()
