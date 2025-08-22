import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import numpy as np

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
</style>
""", unsafe_allow_html=True)

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

# File upload
uploaded_file = st.sidebar.file_uploader("Upload your Stormgate data CSV", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    # Sidebar filters
    st.sidebar.markdown("### Filters")
    
    selected_races = st.sidebar.multiselect(
        "Select Races",
        options=df['race'].unique(),
        default=df['race'].unique()
    )
    
    selected_opponents = st.sidebar.multiselect(
        "Select Opponent Races",
        options=df['opponent_race'].unique(),
        default=df['opponent_race'].unique()
    )
    
    selected_leagues = st.sidebar.multiselect(
        "Select Leagues",
        options=df['league_before'].unique(),
        default=df['league_before'].unique()
    )
    
    # NEW: Filter for opponent league
    selected_opponent_leagues = st.sidebar.multiselect(
        "Select Opponent Leagues",
        options=df['opponent_league_before'].unique(),
        default=df['opponent_league_before'].unique()
    )
    
    # Filter data based on selections
    filtered_df = df[
        (df['race'].isin(selected_races)) &
        (df['opponent_race'].isin(selected_opponents)) &
        (df['league_before'].isin(selected_leagues)) &
        (df['opponent_league_before'].isin(selected_opponent_leagues))  # NEW: opponent league filter
    ]
    
    # Display basic metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Matches", len(filtered_df))
    with col2:
        win_rate = filtered_df['win'].mean() * 100 if len(filtered_df) > 0 else 0
        st.metric("Overall Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Unique Match-ups", filtered_df['match_up'].nunique())
    with col4:
        st.metric("Maps", filtered_df['map_name'].nunique())
    
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
            match_up_win_rate = filtered_df.groupby('match_up')['win'].agg(['mean', 'count']).reset_index()
            match_up_win_rate['win_percentage'] = match_up_win_rate['mean'] * 100
            match_up_win_rate = match_up_win_rate[match_up_win_rate['count'] >= 5]  # Only show match-ups with enough data
            
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
        
        with col2:
            # Win rate by league
            league_win_rate = filtered_df.groupby('league_before')['win'].agg(['mean', 'count']).reset_index()
            league_win_rate['win_percentage'] = league_win_rate['mean'] * 100
            league_win_rate = league_win_rate[league_win_rate['count'] >= 5]  # Only show leagues with enough data
            
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
            
        # NEW: Win rate by opponent league
        st.markdown('<div class="sub-header">Win Rate by Opponent League</div>', unsafe_allow_html=True)
        opponent_league_win_rate = filtered_df.groupby('opponent_league_before')['win'].agg(['mean', 'count']).reset_index()
        opponent_league_win_rate['win_percentage'] = opponent_league_win_rate['mean'] * 100
        opponent_league_win_rate = opponent_league_win_rate[opponent_league_win_rate['count'] >= 5]  # Only show leagues with enough data
        
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
    
    with tab2:
        st.markdown('<h2 class="section-header">Opening Strategies</h2>', unsafe_allow_html=True)
        
        # Most common opening structures
        st.subheader("Most Common Opening Structures")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # First 3 structures
            structure_3_counts = filtered_df['first_3_structures'].value_counts().head(10)
            fig = px.bar(
                x=structure_3_counts.values,
                y=structure_3_counts.index,
                orientation='h',
                title='Top 10 First 3 Structures',
                labels={'x': 'Frequency', 'y': 'Structures'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # First 4 structures
            structure_4_counts = filtered_df['first_4_structures'].value_counts().head(10)
            fig = px.bar(
                x=structure_4_counts.values,
                y=structure_4_counts.index,
                orientation='h',
                title='Top 10 First 4 Structures',
                labels={'x': 'Frequency', 'y': 'Structures'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        col3, col4 = st.columns(2)
        
        with col3:
            # NEW: First 5 structures
            structure_5_counts = filtered_df['first_5_structures'].value_counts().head(10)
            fig = px.bar(
                x=structure_5_counts.values,
                y=structure_5_counts.index,
                orientation='h',
                title='Top 10 First 5 Structures',
                labels={'x': 'Frequency', 'y': 'Structures'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # NEW: First 6 structures
            structure_6_counts = filtered_df['first_6_structures'].value_counts().head(10)
            fig = px.bar(
                x=structure_6_counts.values,
                y=structure_6_counts.index,
                orientation='h',
                title='Top 10 First 6 Structures',
                labels={'x': 'Frequency', 'y': 'Structures'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
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
        
        opening_win_rates = filtered_df.groupby(structure_col)['win'].agg(['mean', 'count']).reset_index()
        opening_win_rates = opening_win_rates[opening_win_rates['count'] >= 5]  # Only openings with enough data
        opening_win_rates['win_percentage'] = opening_win_rates['mean'] * 100
        
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
    
    with tab3:
        st.markdown('<h2 class="section-header">Unit Compositions</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most common unit combinations
            st.subheader("Most Common Unit Combinations")
            
            # Get top unit combinations for 2 units
            unit_2_list = filtered_df['units_2'].dropna().tolist()
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
        
        with col2:
            # Get top unit combinations for 3 units
            unit_3_list = filtered_df['units_3'].dropna().tolist()
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
            
        col3, col4 = st.columns(2)
        
        with col3:
            # NEW: Get top unit combinations for 4 units
            unit_4_list = filtered_df['units_4'].dropna().tolist()
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
            
        with col4:
            # NEW: Get top unit compositions (all units)
            # First, we need to process the units_comp column which contains all units with counts
            # This is a more complex processing, so we'll create a simplified version
            # Let's count how many times each unit appears in the composition strings
            all_units = []
            for comp_str in filtered_df['units_comp'].dropna():
                # Split by '-' and extract unit names (ignoring counts in parentheses)
                units = [unit.split('(')[0].strip() for unit in comp_str.split('-')]
                all_units.extend(units)
            
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
        
        unit_comp_win_rates = filtered_df.groupby(unit_col)['win'].agg(['mean', 'count']).reset_index()
        unit_comp_win_rates = unit_comp_win_rates[unit_comp_win_rates['count'] >= 3]  # Only compositions with enough data
        unit_comp_win_rates['win_percentage'] = unit_comp_win_rates['mean'] * 100
        
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
    
    with tab4:
        st.markdown('<h2 class="section-header">Map Analysis</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Map popularity
            map_counts = filtered_df['map_name'].value_counts()
            fig = px.pie(
                values=map_counts.values,
                names=map_counts.index,
                title='Map Popularity Distribution'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Win rate by map
            map_win_rates = filtered_df.groupby('map_name')['win'].agg(['mean', 'count']).reset_index()
            map_win_rates['win_percentage'] = map_win_rates['mean'] * 100
            map_win_rates = map_win_rates[map_win_rates['count'] >= 5]  # Only maps with enough data
            
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
    
    with tab5:
        st.markdown('<h2 class="section-header">Raw Data</h2>', unsafe_allow_html=True)
        st.dataframe(filtered_df)

else:
    st.info("👈 Please upload a CSV file to begin analysis.")
    st.markdown("""
    ### How to use this dashboard:
    1. Run the scraping script to collect Stormgate data
    2. Upload the generated CSV file using the sidebar uploader
    3. Use the filters to select specific races, opponents, and leagues
    4. Explore the different tabs to analyze various aspects of the data
    
    ### What you can analyze:
    - **Win Rate Analysis**: See win rates by match-up and league
    - **Opening Strategies**: Discover the most common and effective opening builds
    - **Unit Compositions**: Analyze which unit combinations are popular and successful
    - **Map Analysis**: Understand map preferences and performance on different maps
    """)

# Footer
st.markdown("---")
st.markdown("### About")
st.markdown("This dashboard analyzes Stormgate match data to help players understand strategies, win rates, and meta trends. Stormgate is a free-to-play real-time strategy game developed by Frost Giant Studios that features asymmetric factions, deep strategic gameplay, and a competitive ladder system :cite[2]:cite[4].")