import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import numpy as np
import os
import json
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# Set page configuration
st.set_page_config(
    page_title="Stormgate Strategy Analyzer",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .cookie-notification {
        background-color: #4A90E2;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize cookie manager
#@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# Initialize session state for filter persistence
if 'filters' not in st.session_state:
    # Try to load filters from cookies
    cookies = cookie_manager.get_all()
    if 'stormgate_filters' in cookies:
        try:
            st.session_state.filters = json.loads(cookies['stormgate_filters'])
            st.success("Loaded saved filters from cookies!")
        except:
            st.session_state.filters = {
                'races': [],
                'opponents': [],
                'leagues': [],
                'opponent_leagues': []
            }
    else:
        st.session_state.filters = {
            'races': [],
            'opponents': [],
            'leagues': [],
            'opponent_leagues': []
        }

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'df' not in st.session_state:
    st.session_state.df = None

if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None

# Function to save filters to cookies
def save_filters_to_cookie():
    cookie_manager.set(
        'stormgate_filters', 
        json.dumps(st.session_state.filters),
        expires_at=datetime.now() + timedelta(days=30)
    )

# Title and description
st.markdown('<h1 class="main-header">🎮 Stormgate Strategy Analyzer</h1>', unsafe_allow_html=True)
st.markdown("Analyze opening strategies, unit compositions, and win rates across different match-ups and leagues.")

# Load data function with caching
#@st.cache_data
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
        if not st.session_state.filters['races']:
            st.session_state.filters['races'] = list(st.session_state.df['race'].unique())
        if not st.session_state.filters['opponents']:
            st.session_state.filters['opponents'] = list(st.session_state.df['opponent_race'].unique())
        if not st.session_state.filters['leagues']:
            st.session_state.filters['leagues'] = list(st.session_state.df['league_before'].unique())
        if not st.session_state.filters['opponent_leagues']:
            st.session_state.filters['opponent_leagues'] = list(st.session_state.df['opponent_league_before'].unique())
            
        # Save to cookies
        # save_filters_to_cookie()
            
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
        
        # Save to cookies
        # save_filters_to_cookie()
        
    except Exception as e:
        st.sidebar.error(f"Error loading uploaded file: {e}")

# Filter section with persistence
if st.session_state.data_loaded:
    st.sidebar.markdown("### Filters")
    
    # Clear filters button
    if st.sidebar.button("🗑️ Clear All Filters"):
        st.session_state.filters['races'] = []
        st.session_state.filters['opponents'] = []
        st.session_state.filters['leagues'] = []
        st.session_state.filters['opponent_leagues'] = []
        save_filters_to_cookie()
        st.sidebar.success("Filters cleared!")
    
    st.sidebar.markdown("---")
    
    # Race filter
    selected_races = st.sidebar.multiselect(
        "Select Races",
        options=st.session_state.df['race'].unique(),
        default=st.session_state.filters['races'],
        on_change=save_filters_to_cookie,
        key="races_filter"
    )
    
    # Update session state
    st.session_state.filters['races'] = selected_races
    
    # Opponent race filter
    selected_opponents = st.sidebar.multiselect(
        "Select Opponent Races",
        options=st.session_state.df['opponent_race'].unique(),
        default=st.session_state.filters['opponents'],
        on_change=save_filters_to_cookie,
        key="opponents_filter"
    )
    
    # Update session state
    st.session_state.filters['opponents'] = selected_opponents
    
    # League filter
    selected_leagues = st.sidebar.multiselect(
        "Select Leagues",
        options=st.session_state.df['league_before'].unique(),
        default=st.session_state.filters['leagues'],
        on_change=save_filters_to_cookie,
        key="leagues_filter"
    )
    
    # Update session state
    st.session_state.filters['leagues'] = selected_leagues
    
    # Opponent league filter
    selected_opponent_leagues = st.sidebar.multiselect(
        "Select Opponent Leagues",
        options=st.session_state.df['opponent_league_before'].unique(),
        default=st.session_state.filters['opponent_leagues'],
        on_change=save_filters_to_cookie,
        key="opponent_leagues_filter"
    )
    
    # Update session state
    st.session_state.filters['opponent_leagues'] = selected_opponent_leagues
    
    # Filter data based on selections
    st.session_state.filtered_df = st.session_state.df[
        (st.session_state.df['race'].isin(selected_races)) &
        (st.session_state.df['opponent_race'].isin(selected_opponents)) &
        (st.session_state.df['league_before'].isin(selected_leagues)) &
        (st.session_state.df['opponent_league_before'].isin(selected_opponent_leagues))
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
                fig = px.bar(
                    x=structure_3_counts.values,
                    y=structure_3_counts.index,
                    orientation='h',
                    title='Top 10 First 3 Structures',
                    labels={'x': 'Frequency', 'y': 'Structures'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for first 3 structures")
        
        with col2:
            # First 4 structures
            structure_4_counts = st.session_state.filtered_df['first_4_structures'].value_counts().head(10)
            if len(structure_4_counts) > 0:
                fig = px.bar(
                    x=structure_4_counts.values,
                    y=structure_4_counts.index,
                    orientation='h',
                    title='Top 10 First 4 Structures',
                    labels={'x': 'Frequency', 'y': 'Structures'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for first 4 structures")
                
        col3, col4 = st.columns(2)
        
        with col3:
            # First 5 structures
            structure_5_counts = st.session_state.filtered_df['first_5_structures'].value_counts().head(10)
            if len(structure_5_counts) > 0:
                fig = px.bar(
                    x=structure_5_counts.values,
                    y=structure_5_counts.index,
                    orientation='h',
                    title='Top 10 First 5 Structures',
                    labels={'x': 'Frequency', 'y': 'Structures'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for first 5 structures")
        
        with col4:
            # First 6 structures
            structure_6_counts = st.session_state.filtered_df['first_6_structures'].value_counts().head(10)
            if len(structure_6_counts) > 0:
                fig = px.bar(
                    x=structure_6_counts.values,
                    y=structure_6_counts.index,
                    orientation='h',
                    title='Top 10 First 6 Structures',
                    labels={'x': 'Frequency', 'y': 'Structures'}
                )
                st.plotly_chart(fig, use_container_width=True)
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
        
        if len(opening_win_rates) > 0:
            fig = px.scatter(
                opening_win_rates,
                x='count',
                y='win_percentage',
                size='count',
                hover_name=structure_col,
                title=f'Win Rate vs. Popularity of Opening Strategies ({structure_option})',
                labels={'count': 'Number of Games', 'win_percentage': 'Win Rate (%)'}
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
                
                fig = px.bar(
                    x=list(top_unit_2.values()),
                    y=list(top_unit_2.keys()),
                    orientation='h',
                    title='Top 10 Two-Unit Combinations',
                    labels={'x': 'Frequency', 'y': 'Units'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for two-unit combinations")
        
        with col2:
            # Get top unit combinations for 3 units
            unit_3_list = st.session_state.filtered_df['units_3'].dropna().tolist()
            if unit_3_list:
                unit_3_counter = Counter(unit_3_list)
                top_unit_3 = dict(unit_3_counter.most_common(10))
                
                fig = px.bar(
                    x=list(top_unit_3.values()),
                    y=list(top_unit_3.keys()),
                    orientation='h',
                    title='Top 10 Three-Unit Combinations',
                    labels={'x': 'Frequency', 'y': 'Units'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for three-unit combinations")
                
        col3, col4 = st.columns(2)
        
        with col3:
            # Get top unit combinations for 4 units
            unit_4_list = st.session_state.filtered_df['units_4'].dropna().tolist()
            if unit_4_list:
                unit_4_counter = Counter(unit_4_list)
                top_unit_4 = dict(unit_4_counter.most_common(10))
                
                fig = px.bar(
                    x=list(top_unit_4.values()),
                    y=list(top_unit_4.keys()),
                    orientation='h',
                    title='Top 10 Four-Unit Combinations',
                    labels={'x': 'Frequency', 'y': 'Units'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for four-unit combinations")
                
        with col4:
            # Get top unit compositions (all units)
            all_units = []
            for comp_str in st.session_state.filtered_df['units_comp'].dropna():
                # Split by '-' and extract unit names (ignoring counts in parentheses)
                units = [unit.split('(')[0].strip() for unit in comp_str.split('-')]
                all_units.extend(units)
            
            if all_units:
                unit_counter = Counter(all_units)
                top_units = dict(unit_counter.most_common(15))
                
                fig = px.bar(
                    x=list(top_units.values()),
                    y=list(top_units.keys()),
                    orientation='h',
                    title='Top 15 Most Frequently Built Units',
                    labels={'x': 'Frequency', 'y': 'Units'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for unit compositions")
        
        # Unit composition win rates
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
        
        if len(unit_comp_win_rates) > 0:
            fig = px.scatter(
                unit_comp_win_rates,
                x='count',
                y='win_percentage',
                size='count',
                hover_name=unit_col,
                title=f'Win Rate vs. Popularity of {unit_option} Compositions',
                labels={'count': 'Number of Games', 'win_percentage': 'Win Rate (%)'}
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
    4. Your filter selections will be automatically saved via cookies
    5. Explore the different tabs to analyze various aspects of the data
    
    ### What you can analyze:
    - **Win Rate Analysis**: See win rates by match-up and league
    - **Opening Strategies**: Discover the most common and effective opening builds
    - **Unit Compositions**: Analyze which unit combinations are popular and successful
    - **Map Analysis**: Understand map preferences and performance on different maps
    
    ### Filter Persistence:
    - Your filter selections are automatically saved in browser cookies
    - They will be restored when you revisit the page
    - Use the "Clear All Filters" button to reset all selections
    """)

# Footer
st.markdown("---")
st.markdown("### About")
st.markdown("This dashboard analyzes Stormgate match data to help players understand strategies, win rates, and meta trends. Stormgate is a free-to-play real-time strategy game developed by Frost Giant Studios.")