import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import numpy as np
import os
import json
from streamlit_local_storage import LocalStorage
import requests
from PIL import Image
import io
import re
import base64

# Set page configuration
st.set_page_config(
    page_title="Stormgate Strategy Analyzer",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize local storage
local_storage = LocalStorage()

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 3rem; color: #FF6B00; margin-bottom: 1rem;}
    .section-header {font-size: 2rem; color: #4A90E2; border-bottom: 2px solid #4A90E2; padding-bottom: 0.3rem;}
    .metric-label {font-weight: bold; color: #FF6B00;}
    .info-text {font-style: italic; color: #666;}
    .sub-header {font-size: 1.5rem; color: #FF6B00; margin-top: 1.5rem;}
    .stButton>button {
        background-color: #4A90E2;
        color: white;
        font-weight: bold;
    }
    .filter-section {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .storage-notification {
        background-color: #4A90E2;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
    }
    .unit-icon {
        width: 36px;
        height: 36px;
        margin: 2px;
        border-radius: 4px;
        object-fit: cover;
    }
    .structure-icon {
        width: 36px;
        height: 36px;
        margin: 2px;
        border-radius: 4px;
        object-fit: cover;
    }
    .icon-container {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        align-items: center;
        justify-content: flex-start;
    }
    .icon-row {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        padding: 5px;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    .structure-count {
        font-weight: bold;
        margin-left: 10px;
        min-width: 50px;
        text-align: right;
    }
    .rank-number {
        font-weight: bold;
        margin-right: 10px;
        min-width: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for filter persistence
if 'filters' not in st.session_state:
    # Try to load filters from local storage
    saved_filters = local_storage.getItem("stormgate_filters")
    if saved_filters and saved_filters:
        try:
            st.session_state.filters = json.loads(saved_filters)
            st.session_state.filters_loaded = True
        except:
            st.session_state.filters = {
                'races': [],
                'opponents': [],
                'leagues': [],
                'opponent_leagues': []
            }
            st.session_state.filters_loaded = False
    else:
        st.session_state.filters = {
            'races': [],
            'opponents': [],
            'leagues': [],
            'opponent_leagues': []
        }
        st.session_state.filters_loaded = False

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'df' not in st.session_state:
    st.session_state.df = None

if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None

# Load units and upgrades data
@st.cache_data
def load_units_data():
    try:
        with open('units.json', 'r') as f:
            units_data = json.load(f)
        # Create a mapping from ID to unit data
        return {unit['id']: unit for unit in units_data}
    except FileNotFoundError:
        st.error("units.json file not found. Please make sure it's in the same directory.")
        return {}
    except Exception as e:
        st.error(f"Error loading units.json: {e}")
        return {}

@st.cache_data
def load_upgrades_data():
    try:
        with open('upgrades.json', 'r') as f:
            upgrades_data = json.load(f)
        # Create a mapping from ID to upgrade data
        return {upgrade['id']: upgrade for upgrade in upgrades_data}
    except FileNotFoundError:
        st.error("upgrades.json file not found. Please make sure it's in the same directory.")
        return {}
    except Exception as e:
        st.error(f"Error loading upgrades.json: {e}")
        return {}

# Load units and upgrades data
units_data = load_units_data()
upgrades_data = load_upgrades_data()

# Function to get unit icon by ID
@st.cache_data
def get_unit_icon(unit_id):
    if unit_id in units_data and 'button_icon_path' in units_data[unit_id]:
        icon_path = units_data[unit_id]['button_icon_path']
        if icon_path:
            try:
                response = requests.get(f"https://stormgatejson.untapped.gg/art/{icon_path}")
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    image = image.resize((36, 36))
                    return image
            except Exception as e:
                st.error(f"Error loading icon for {unit_id}: {e}")
                
    if unit_id in upgrades_data and 'button_icon_path' in upgrades_data[unit_id]:
        icon_path = upgrades_data[unit_id]['button_icon_path']
        if icon_path:
            try:
                response = requests.get(f"https://stormgatejson.untapped.gg/art/{icon_path}")
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    image = image.resize((36, 36))
                    return image
            except Exception as e:
                st.error(f"Error loading icon for {unit_id}: {e}")
    return None

# Function to get unit name by ID
def get_unit_name(unit_id):
    if unit_id in units_data and 'name' in units_data[unit_id]:
        return units_data[unit_id]['name']
    return unit_id

# Function to get structure icon by ID
@st.cache_data
def get_structure_icon(structure_id):
    # Structures are also in units.json, so we can use the same function
    return get_unit_icon(structure_id)

# Function to convert structure IDs to readable names
def get_structure_combo_name(structure_combo):
    structure_ids = extract_structure_ids(structure_combo)
    structure_names = []
    for structure_id in structure_ids:
        structure_name = get_structure_name(structure_id)
        structure_names.append(structure_name)
    return " - ".join(structure_names)
    
def get_structure_combo_with_icons(structure_combo, icon_size=24):
    structure_ids = extract_structure_ids(structure_combo)
    icon_html = '<div style="display: flex; align-items: center; gap: 2px;">'
    
    for structure_id in structure_ids:
        structure_name = get_structure_name(structure_id)
        icon = get_structure_icon(structure_id)
        
        if icon:
            # Resize icon to the specified size
            icon = icon.resize((icon_size, icon_size))
            icon_base64 = image_to_base64(icon)
            icon_html += f'<img src="data:image/png;base64,{icon_base64}" style="width: {icon_size}px; height: {icon_size}px;" title="{structure_name}">'
        else:
            icon_html += f'<span title="{structure_name}">{structure_id}</span>'
    
    icon_html += '</div>'
    return icon_html

# Function to get structure name by ID
def get_structure_name(structure_id):
    if structure_id in units_data and 'name' in units_data[structure_id]:
        return units_data[structure_id]['name']
    if structure_id in upgrades_data and 'name' in upgrades_data[structure_id]:
        return upgrades_data[structure_id]['name']
    return structure_id

# Function to get upgrade icon by ID
@st.cache_data
def get_upgrade_icon(upgrade_id):
    if upgrade_id in upgrades_data and 'button_icon_path' in upgrades_data[upgrade_id]:
        icon_path = upgrades_data[upgrade_id]['button_icon_path']
        if icon_path:
            try:
                response = requests.get(f"https://stormgatejson.untapped.gg/art/{icon_path}")
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    image = image.resize((36, 36))
                    return image
            except Exception as e:
                st.error(f"Error loading icon for {upgrade_id}: {e}")
    return None

# Function to get upgrade name by ID
def get_upgrade_name(upgrade_id):
    if upgrade_id in upgrades_data and 'name' in upgrades_data[upgrade_id]:
        return upgrades_data[upgrade_id]['name']
    return upgrade_id

# Function to extract IDs from composition strings
def extract_ids_from_composition(comp_str):
    if pd.isna(comp_str):
        return []
    
    # Pattern to match IDs with optional counts in parentheses
    pattern = r'([A-Za-z0-9_]+)(?:\([^)]*\))?'
    matches = re.findall(pattern, comp_str)
    return matches

# Function to extract structure IDs from opening strings
def extract_structure_ids(opening_str):
    if pd.isna(opening_str):
        return []
    
    # Split by '-' to get individual structures
    structures = opening_str.split('-')
    return [s.strip() for s in structures if s.strip()]

# Function to save filters to local storage
def save_filters_to_storage():
    local_storage.setItem("stormgate_filters", json.dumps(st.session_state.filters))

# Function to convert image to base64 for HTML display
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Title and description
st.markdown('<h1 class="main-header">🎮 Stormgate Strategy Analyzer</h1>', unsafe_allow_html=True)
st.markdown("Analyze opening strategies, unit compositions, and win rates across different match-ups and leagues.")

# Load data function with caching
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    
    # Clean and preprocess data
    df['win'] = df['outcome'].apply(lambda x: 1 if x == 'win' else 0)
    
    # Extract race information from match_up
    df['race'] = df['match_up'].str[0]
    df['opponent_race'] = df['match_up'].str[2]
    
    return df

# Check if default.csv exists and load it automatically
default_csv_path = "default.csv"

if os.path.exists(default_csv_path) and not st.session_state.data_loaded:
    try:
        st.session_state.df = load_data(default_csv_path)
        st.session_state.data_loaded = True
        st.sidebar.success("📊 Loaded default.csv automatically")
        
        # Initialize filters with all options if not already set
        if not st.session_state.filters_loaded:
            st.session_state.filters['races'] = list(st.session_state.df['race'].unique())
            st.session_state.filters['opponents'] = list(st.session_state.df['opponent_race'].unique())
            st.session_state.filters['leagues'] = list(st.session_state.df['league_before'].unique())
            st.session_state.filters['opponent_leagues'] = list(st.session_state.df['opponent_league_before'].unique())
            st.session_state.filters_loaded = True
            
        # Save to local storage
        save_filters_to_storage()
            
    except Exception as e:
        st.sidebar.error(f"Error loading default.csv: {e}")

# File upload - always show even if default data is loaded
uploaded_file = st.sidebar.file_uploader("Or upload a different CSV file", type="csv")

if uploaded_file is not None:
    try:
        st.session_state.df = load_data(uploaded_file)
        st.session_state.data_loaded = True
        st.sidebar.success("📊 Uploaded file loaded successfully")
        
        # Update filters with new data options
        st.session_state.filters['races'] = list(st.session_state.df['race'].unique())
        st.session_state.filters['opponents'] = list(st.session_state.df['opponent_race'].unique())
        st.session_state.filters['leagues'] = list(st.session_state.df['league_before'].unique())
        st.session_state.filters['opponent_leagues'] = list(st.session_state.df['opponent_league_before'].unique())
        
        # Save to local storage
        save_filters_to_storage()
        
    except Exception as e:
        st.sidebar.error(f"Error loading uploaded file: {e}")

# Filter section with persistence
if st.session_state.data_loaded:
    if not st.session_state.filters_loaded:
        st.sidebar.markdown('<div class="storage-notification">Loaded saved filters from storage!</div>', unsafe_allow_html=True)
        st.session_state.filters_loaded = True
    
    st.sidebar.markdown("### Filters")
    
    # Clear filters button
    if st.sidebar.button("🗑️ Clear All Filters"):
        st.session_state.filters['races'] = []
        st.session_state.filters['opponents'] = []
        st.session_state.filters['leagues'] = []
        st.session_state.filters['opponent_leagues'] = []
        save_filters_to_storage()
        st.sidebar.success("Filters cleared!")
    
    # Reset to default button
    if st.sidebar.button("🔄 Reset to Default Filters"):
        st.session_state.filters['races'] = list(st.session_state.df['race'].unique())
        st.session_state.filters['opponents'] = list(st.session_state.df['opponent_race'].unique())
        st.session_state.filters['leagues'] = list(st.session_state.df['league_before'].unique())
        st.session_state.filters['opponent_leagues'] = list(st.session_state.df['opponent_league_before'].unique())
        save_filters_to_storage()
        st.sidebar.success("Filters reset to default!")
    
    st.sidebar.markdown("---")
    
    # Create callback functions for filter changes
    def update_races():
        st.session_state.filters['races'] = st.session_state.races_filter
        save_filters_to_storage()
        
    def update_opponents():
        st.session_state.filters['opponents'] = st.session_state.opponents_filter
        save_filters_to_storage()
        
    def update_leagues():
        st.session_state.filters['leagues'] = st.session_state.leagues_filter
        save_filters_to_storage()
        
    def update_opponent_leagues():
        st.session_state.filters['opponent_leagues'] = st.session_state.opponent_leagues_filter
        save_filters_to_storage()
    
    # Race filter
    selected_races = st.sidebar.multiselect(
        "Select Races",
        options=st.session_state.df['race'].unique(),
        default=st.session_state.filters['races'],
        key="races_filter",
        on_change=update_races
    )
    
    # Opponent race filter
    selected_opponents = st.sidebar.multiselect(
        "Select Opponent Races",
        options=st.session_state.df['opponent_race'].unique(),
        default=st.session_state.filters['opponents'],
        key="opponents_filter",
        on_change=update_opponents
    )
    
    # League filter
    selected_leagues = st.sidebar.multiselect(
        "Select Leagues",
        options=st.session_state.df['league_before'].unique(),
        default=st.session_state.filters['leagues'],
        key="leagues_filter",
        on_change=update_leagues
    )
    
    # Opponent league filter
    selected_opponent_leagues = st.sidebar.multiselect(
        "Select Opponent Leagues",
        options=st.session_state.df['opponent_league_before'].unique(),
        default=st.session_state.filters['opponent_leagues'],
        key="opponent_leagues_filter",
        on_change=update_opponent_leagues
    )
    
    # Filter data based on selections
    st.session_state.filtered_df = st.session_state.df[
        (st.session_state.df['race'].isin(st.session_state.filters['races'])) &
        (st.session_state.df['opponent_race'].isin(st.session_state.filters['opponents'])) &
        (st.session_state.df['league_before'].isin(st.session_state.filters['leagues'])) &
        (st.session_state.df['opponent_league_before'].isin(st.session_state.filters['opponent_leagues']))
    ]
    
    # Display data source info
    if os.path.exists(default_csv_path) and uploaded_file is None:
        st.sidebar.info("Using data from: default.csv")
    else:
        st.sidebar.info("Using data from: uploaded file")
    
    # Display basic metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Matches", len(st.session_state.filtered_df))
    with col2:
        win_rate = st.session_state.filtered_df['win'].mean() * 100 if len(st.session_state.filtered_df) > 0 else 0
        st.metric("Overall Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Unique Match-ups", st.session_state.filtered_df['match_up'].nunique())
    with col4:
        st.metric("Maps", st.session_state.filtered_df['map_name'].nunique())
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Win Rate Analysis", 
        "Opening Strategies", 
        "Unit Compositions", 
        "Map Analysis", 
        "Raw Data"
    ])
    
    with tab1:
        st.markdown('<h2 class="section-header">Win Rate Analysis</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Win rate by match-up
            match_up_win_rate = st.session_state.filtered_df.groupby('match_up')['win'].agg(['mean', 'count']).reset_index()
            match_up_win_rate['win_percentage'] = match_up_win_rate['mean'] * 100
            match_up_win_rate = match_up_win_rate[match_up_win_rate['count'] >= 5]  # Only show match-ups with enough data
            
            if len(match_up_win_rate) > 0:
                fig = px.bar(
                    match_up_win_rate, 
                    x='match_up', 
                    y='win_percentage',
                    title='Win Rate by Match-up',
                    labels={'match_up': 'Match-up', 'win_percentage': 'Win Rate (%)'},
                    text='count',
                    color='win_percentage',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(texttemplate='%{text} games', textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to display match-up win rates")
        
        with col2:
            # Win rate by league
            league_win_rate = st.session_state.filtered_df.groupby('league_before')['win'].agg(['mean', 'count']).reset_index()
            league_win_rate['win_percentage'] = league_win_rate['mean'] * 100
            league_win_rate = league_win_rate[league_win_rate['count'] >= 5]  # Only show leagues with enough data
            
            if len(league_win_rate) > 0:
                fig = px.bar(
                    league_win_rate, 
                    x='league_before', 
                    y='win_percentage',
                    title='Win Rate by League',
                    labels={'league_before': 'League', 'win_percentage': 'Win Rate (%)'},
                    text='count',
                    color='win_percentage',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(texttemplate='%{text} games', textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to display league win rates")
            
        # Win rate by opponent league
        st.markdown('<div class="sub-header">Win Rate by Opponent League</div>', unsafe_allow_html=True)
        opponent_league_win_rate = st.session_state.filtered_df.groupby('opponent_league_before')['win'].agg(['mean', 'count']).reset_index()
        opponent_league_win_rate['win_percentage'] = opponent_league_win_rate['mean'] * 100
        opponent_league_win_rate = opponent_league_win_rate[opponent_league_win_rate['count'] >= 5]  # Only show leagues with enough data
        
        if len(opponent_league_win_rate) > 0:
            fig = px.bar(
                opponent_league_win_rate, 
                x='opponent_league_before', 
                y='win_percentage',
                title='Win Rate by Opponent League',
                labels={'opponent_league_before': 'Opponent League', 'win_percentage': 'Win Rate (%)'},
                text='count',
                color='win_percentage',
                color_continuous_scale='RdYlGn'
            )
            fig.update_traces(texttemplate='%{text} games', textposition='outside')
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display opponent league win rates")
    
    with tab2:
        st.markdown('<h2 class="section-header">Opening Strategies</h2>', unsafe_allow_html=True)
        
        # Most common opening structures
        st.subheader("Most Common Opening Structures")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # First 3 structures
            structure_3_counts = st.session_state.filtered_df['first_3_structures'].value_counts().head(10)
            if len(structure_3_counts) > 0:
                st.markdown("**Top 10 First 3 Structures**")
                for i, (structure_combo, count) in enumerate(structure_3_counts.items()):
                    structure_ids = extract_structure_ids(structure_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for structure_id in structure_ids:
                        icon = get_structure_icon(structure_id.strip())
                        structure_name = get_structure_name(structure_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="structure-icon" title="{structure_name}">'
                        else:
                            icon_html += f'<span title="{structure_name}">{structure_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available for first 3 structures")
        
        with col2:
            # First 4 structures
            structure_4_counts = st.session_state.filtered_df['first_4_structures'].value_counts().head(10)
            if len(structure_4_counts) > 0:
                st.markdown("**Top 10 First 4 Structures**")
                for i, (structure_combo, count) in enumerate(structure_4_counts.items()):
                    structure_ids = extract_structure_ids(structure_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for structure_id in structure_ids:
                        icon = get_structure_icon(structure_id.strip())
                        structure_name = get_structure_name(structure_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="structure-icon" title="{structure_name}">'
                        else:
                            icon_html += f'<span title="{structure_name}">{structure_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available for first 4 structures")
                
        col3, col4 = st.columns(2)
        
        with col3:
            # First 5 structures
            structure_5_counts = st.session_state.filtered_df['first_5_structures'].value_counts().head(10)
            if len(structure_5_counts) > 0:
                st.markdown("**Top 10 First 5 Structures**")
                for i, (structure_combo, count) in enumerate(structure_5_counts.items()):
                    structure_ids = extract_structure_ids(structure_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for structure_id in structure_ids:
                        icon = get_structure_icon(structure_id.strip())
                        structure_name = get_structure_name(structure_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="structure-icon" title="{structure_name}">'
                        else:
                            icon_html += f'<span title="{structure_name}">{structure_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available for first 5 structures")
        
        with col4:
            # First 6 structures
            structure_6_counts = st.session_state.filtered_df['first_6_structures'].value_counts().head(10)
            if len(structure_6_counts) > 0:
                st.markdown("**Top 10 First 6 Structures**")
                for i, (structure_combo, count) in enumerate(structure_6_counts.items()):
                    structure_ids = extract_structure_ids(structure_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for structure_id in structure_ids:
                        icon = get_structure_icon(structure_id.strip())
                        structure_name = get_structure_name(structure_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="structure-icon" title="{structure_name}">'
                        else:
                            icon_html += f'<span title="{structure_name}">{structure_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available for first 6 structures")
        
        # Win rate by opening - for all structure counts
        st.subheader("Win Rate by Opening Strategy")
        
        # Create a selectbox to choose which structure count to analyze
        structure_option = st.selectbox(
            "Select Structure Count for Analysis",
            options=["3 Structures", "4 Structures", "5 Structures", "6 Structures"],
            index=0
        )
        
        # Map selection to column name
        structure_col = f"first_{structure_option[0]}_structures"
        
        opening_win_rates = st.session_state.filtered_df.groupby(structure_col)['win'].agg(['mean', 'count']).reset_index()
        opening_win_rates = opening_win_rates[opening_win_rates['count'] >= 5]  # Only openings with enough data
        opening_win_rates['win_percentage'] = opening_win_rates['mean'] * 100
        opening_win_rates['combo_name'] = opening_win_rates[structure_col].apply(get_structure_combo_name)
        opening_win_rates['combo_with_icons'] = opening_win_rates[structure_col].apply(
                lambda x: get_structure_combo_with_icons(x, icon_size=24)
            )
        
        if len(opening_win_rates) > 0:
            # Create custom hover data
            hover_data = {
                'combo_name': True,
                'count': True,
                'win_percentage': ':.1f%'
            }
        
            fig = px.scatter(
                opening_win_rates,
                x='count',
                y='win_percentage',
                size='count',
                hover_name='combo_name',
                title=f'Win Rate vs. Popularity of Opening Strategies ({structure_option})',
                labels={'count': 'Number of Games', 'win_percentage': 'Win Rate (%)'}#,
                #custom_data=['combo_with_icons']  # Add HTML with icons as custom data
            )
            
            # Update hover template to include icons
            fig.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b><br>" +
                    "Games: %{x}<br>" +
                    "Win Rate: %{y:.1f}%<br>" +
                    "<extra></extra>"
                )
            )
            
            # Add some styling
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                ),
                xaxis_title="Number of Games (Popularity)",
                yaxis_title="Win Rate (%)",
                showlegend=False
            )
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% Win Rate")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Not enough data to display win rates for {structure_option.lower()}")
    
    with tab3:
        st.markdown('<h2 class="section-header">Unit Compositions</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most common unit combinations
            st.subheader("Most Common Unit Combinations")
            
            # Get top unit combinations for 2 units
            unit_2_list = st.session_state.filtered_df['units_2'].dropna().tolist()
            if unit_2_list:
                unit_2_counter = Counter(unit_2_list)
                top_unit_2 = dict(unit_2_counter.most_common(10))
                
                # Create a custom visualization with icons
                st.markdown("**Top 10 Two-Unit Combinations**")
                for i, (unit_combo, count) in enumerate(top_unit_2.items()):
                    unit_ids = extract_ids_from_composition(unit_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for unit_id in unit_ids:
                        icon = get_unit_icon(unit_id.strip())
                        unit_name = get_unit_name(unit_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="unit-icon" title="{unit_name}">'
                        else:
                            icon_html += f'<span title="{unit_name}">{unit_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("No data available for two-unit combinations")
        
        with col2:
            # Get top unit combinations for 3 units
            unit_3_list = st.session_state.filtered_df['units_3'].dropna().tolist()
            if unit_3_list:
                unit_3_counter = Counter(unit_3_list)
                top_unit_3 = dict(unit_3_counter.most_common(10))
                
                # Create a custom visualization with icons
                st.markdown("**Top 10 Three-Unit Combinations**")
                for i, (unit_combo, count) in enumerate(top_unit_3.items()):
                    unit_ids = extract_ids_from_composition(unit_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for unit_id in unit_ids:
                        icon = get_unit_icon(unit_id.strip())
                        unit_name = get_unit_name(unit_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="unit-icon" title="{unit_name}">'
                        else:
                            icon_html += f'<span title="{unit_name}">{unit_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("No data available for three-unit combinations")
                
        col3, col4 = st.columns(2)
        
        with col3:
            # Get top unit combinations for 4 units
            unit_4_list = st.session_state.filtered_df['units_4'].dropna().tolist()
            if unit_4_list:
                unit_4_counter = Counter(unit_4_list)
                top_unit_4 = dict(unit_4_counter.most_common(10))
                
                # Create a custom visualization with icons
                st.markdown("**Top 10 Four-Unit Combinations**")
                for i, (unit_combo, count) in enumerate(top_unit_4.items()):
                    unit_ids = extract_ids_from_composition(unit_combo)
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    for unit_id in unit_ids:
                        icon = get_unit_icon(unit_id.strip())
                        unit_name = get_unit_name(unit_id.strip())
                        if icon:
                            icon_base64 = image_to_base64(icon)
                            icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="unit-icon" title="{unit_name}">'
                        else:
                            icon_html += f'<span title="{unit_name}">{unit_id.strip()}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("No data available for four-unit combinations")
                
        with col4:
            # Get top unit compositions (all units)
            all_unit_ids = []
            for comp_str in st.session_state.filtered_df['units_comp'].dropna():
                unit_ids = extract_ids_from_composition(comp_str)
                all_unit_ids.extend(unit_ids)
            
            if all_unit_ids:
                unit_counter = Counter(all_unit_ids)
                top_units = dict(unit_counter.most_common(15))
                
                # Create a custom visualization with icons
                st.markdown("**Top 15 Most Frequently Built Units**")
                for i, (unit_id, count) in enumerate(top_units.items()):
                    st.markdown(f'<div class="icon-row"><span class="rank-number">#{i+1}</span>', unsafe_allow_html=True)
                    
                    # Create icon container
                    icon_html = '<div class="icon-container">'
                    icon = get_unit_icon(unit_id)
                    unit_name = get_unit_name(unit_id)
                    if icon:
                        icon_base64 = image_to_base64(icon)
                        icon_html += f'<img src="data:image/png;base64,{icon_base64}" class="unit-icon" title="{unit_name}">'
                    else:
                        icon_html += f'<span title="{unit_name}">{unit_id}</span>'
                    icon_html += f'<span class="structure-count">{count}</span></div>'
                    
                    st.markdown(icon_html, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data available for unit compositions")
        
        # Unit composition win rates with custom graph (similar to opening strategies)
        st.subheader("Unit Composition Win Rates")
        
        # Create a selectbox to choose which unit count to analyze
        unit_option = st.selectbox(
            "Select Unit Count for Analysis",
            options=["2 Units", "3 Units", "4 Units"],
            index=1
        )
        
        # Map selection to column name
        unit_col = f"units_{unit_option[0]}"
        
        unit_comp_win_rates = st.session_state.filtered_df.groupby(unit_col)['win'].agg(['mean', 'count']).reset_index()
        unit_comp_win_rates = unit_comp_win_rates[unit_comp_win_rates['count'] >= 3]  # Only compositions with enough data
        unit_comp_win_rates['win_percentage'] = unit_comp_win_rates['mean'] * 100
        unit_comp_win_rates['combo_name'] = unit_comp_win_rates[unit_col].apply(get_structure_combo_name)
        unit_comp_win_rates['combo_with_icons'] = unit_comp_win_rates[unit_col].apply(
            lambda x: get_structure_combo_with_icons(x, icon_size=24)
        )
        
        if len(unit_comp_win_rates) > 0:
            # Create custom scatter plot similar to opening strategies
            fig = px.scatter(
                unit_comp_win_rates,
                x='count',
                y='win_percentage',
                size='count',
                hover_name='combo_name',
                title=f'Win Rate vs. Popularity of {unit_option} Compositions',
                labels={'count': 'Number of Games', 'win_percentage': 'Win Rate (%)'}
            )
            
            # Update hover template
            fig.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b><br>" +
                    "Games: %{x}<br>" +
                    "Win Rate: %{y:.1f}%<br>" +
                    "<extra></extra>"
                )
            )
            
            # Add styling
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial"
                ),
                xaxis_title="Number of Games (Popularity)",
                yaxis_title="Win Rate (%)",
                showlegend=False
            )
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% Win Rate")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Not enough data to display win rates for {unit_option.lower()}")
    
    with tab4:
        st.markdown('<h2 class="section-header">Map Analysis</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Map popularity
            map_counts = st.session_state.filtered_df['map_name'].value_counts()
            if len(map_counts) > 0:
                fig = px.pie(
                    values=map_counts.values,
                    names=map_counts.index,
                    title='Map Popularity Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for map popularity")
        
        with col2:
            # Win rate by map
            map_win_rates = st.session_state.filtered_df.groupby('map_name')['win'].agg(['mean', 'count']).reset_index()
            map_win_rates['win_percentage'] = map_win_rates['mean'] * 100
            map_win_rates = map_win_rates[map_win_rates['count'] >= 5]  # Only maps with enough data
            
            if len(map_win_rates) > 0:
                fig = px.bar(
                    map_win_rates,
                    x='map_name',
                    y='win_percentage',
                    title='Win Rate by Map',
                    labels={'map_name': 'Map', 'win_percentage': 'Win Rate (%)'},
                    text='count',
                    color='win_percentage',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(texttemplate='%{text} games', textposition='outside')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to display map win rates")
    
    with tab5:
        st.markdown('<h2 class="section-header">Raw Data</h2>', unsafe_allow_html=True)
        st.dataframe(st.session_state.filtered_df)

else:
    st.info("👈 Please upload a CSV file to begin analysis or place a 'default.csv' file in the same directory.")
    st.markdown("""
    ### How to use this dashboard:
    1. Run the scraping script to collect Stormgate data
    2. Save the CSV as 'default.csv' in the same directory or upload it using the sidebar
    3. Use the filters to select specific races, opponents, and leagues
    4. Your filter selections will be automatically saved in browser storage
    5. Explore the different tabs to analyze various aspects of the data
    
    ### What you can analyze:
    - **Win Rate Analysis**: See win rates by match-up and league
    - **Opening Strategies**: Discover the most common and effective opening builds
    - **Unit Compositions**: Analyze which unit combinations are popular and successful
    - **Map Analysis**: Understand map preferences and performance on different maps
    
    ### Filter Persistence:
    - Your filter selections are automatically saved in browser local storage
    - They will be restored when you revisit the page, even after closing the browser
    - Use the "Clear All Filters" button to reset all selections
    - Use the "Reset to Default Filters" button to select all options
    """)

# Footer
st.markdown("---")
st.markdown("### About")
st.markdown("This dashboard analyzes Stormgate match data to help players understand strategies, win rates, and meta trends. Stormgate is a free-to-play real-time strategy game developed by Frost Giant Studios.")