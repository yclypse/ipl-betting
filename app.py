import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import re
from datetime import datetime
import matplotlib.pyplot as plt
from PIL import Image

from data_utils import (
    load_players, 
    parse_multiple_matches, 
    compute_betting_result_df,
    save_match_data,
    load_match_data,
    update_match_data,
    delete_match_data,
    regenerate_results,
    save_results_to_csv,
    load_results_from_csv
)
from background_processor import BackgroundProcessor
from visualization import VisualizationGenerator

# Page configuration
st.set_page_config(
    page_title="IPL Betting Tracker",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = BackgroundProcessor()
    # Start the background processing
    st.session_state.processor.start_processing()

if 'viz_generator' not in st.session_state:
    st.session_state.viz_generator = VisualizationGenerator()

if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

if 'editing_match' not in st.session_state:
    st.session_state.editing_match = None

# Function to trigger UI refresh
def refresh_ui():
    st.session_state.refresh_counter += 1

# Register the refresh callback
st.session_state.processor.register_callback(refresh_ui)

# App title and description
st.title("IPL Betting Tracker 🏏")
st.markdown("""
This application helps track IPL betting results and visualize performance metrics.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Enter Match Data", "Match History", "View Results", "Player Stats", "Team Stats", "Advanced Analytics"])

# Load player and team data
player_team_map, team_owners_map = load_players()
all_teams = sorted(list(team_owners_map.keys()))
all_players = sorted(list(player_team_map.keys()))

# Enter Match Data page
if page == "Enter Match Data":
    st.header("Enter New Match Data")
    
    # Only batch format input
    st.markdown("""
    Enter match data in the following format:
    ```
    TEAM1 (number)
    Player1,Player2,Player3,...
    TEAM2 (number)
    Player1,Player2,Player3,...
    ----------------------------------------------------------------------
    ```
    You can include multiple matches separated by the dashed line.
    """)
    
    batch_input = st.text_area("Batch Input", height=200)
    winner_input = st.text_input("Winners (enter team codes separated by semicolons, e.g., RCB;SRH;MI)")
    
    if st.button("Process Batch"):
        if batch_input and winner_input:
            try:
                # Parse the batch input
                parsed_matches = parse_multiple_matches(batch_input)
                
                if parsed_matches:
                    # Parse winners
                    winners = [w.strip() for w in winner_input.split(';')]
                    
                    # Check if number of winners matches number of matches
                    if len(winners) != len(parsed_matches):
                        st.error(f"Number of winners ({len(winners)}) does not match number of matches ({len(parsed_matches)}). Please provide one winner for each match, separated by semicolons.")
                    else:
                        # Process all matches
                        all_results_dfs = []
                        
                        for i, (team1, team1_bettors, team2, team2_bettors) in enumerate(parsed_matches):
                            current_winner = winners[i]
                            
                            # Validate winner
                            if current_winner not in [team1, team2]:
                                st.error(f"Match {i+1}: Winner must be either {team1} or {team2}, but got {current_winner}")
                                continue
                            
                            # Save match data
                            match_data = {
                                "team1": team1,
                                "team1_bettors": team1_bettors,
                                "team2": team2,
                                "team2_bettors": team2_bettors,
                                "winner": current_winner
                            }
                            save_match_data(match_data)
                            
                            # Process match results
                            results_df = st.session_state.processor.process_new_match(
                                team1, team1_bettors, team2, team2_bettors, current_winner
                            )
                            
                            all_results_dfs.append(results_df)
                            st.success(f"Match {i+1}: {team1} vs {team2} processed successfully!")
                        
                        # Display combined results if any matches were processed
                        if all_results_dfs:
                            combined_results = pd.concat(all_results_dfs, ignore_index=True)
                            st.subheader("Combined Results")
                            st.dataframe(combined_results)
                else:
                    st.error("Could not parse the batch input. Please check the format.")
            except Exception as e:
                st.error(f"Error processing batch: {str(e)}")
        else:
            st.error("Please provide both batch input and winner.")

# Match History page
elif page == "Match History":
    st.header("Match History")
    
    # Load all matches
    matches = load_match_data()
    
    if matches:
        # Display matches in a table
        st.subheader("All Matches")
        
        # Create a dataframe for display
        match_data = []
        for match in matches:
            match_data.append({
                "ID": match.get('id', ''),
                "Match": f"{match.get('team1', '')} vs {match.get('team2', '')}",
                "Winner": match.get('winner', ''),
                "Date": datetime.fromisoformat(match.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M'),
                "Team1 Bettors": ", ".join(match.get('team1_bettors', [])),
                "Team2 Bettors": ", ".join(match.get('team2_bettors', []))
            })
        
        match_df = pd.DataFrame(match_data)
        
        # Display with edit and delete buttons
        for i, row in match_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
            
            with col1:
                st.write(f"**ID:** {row['ID']}")
            
            with col2:
                st.write(f"**{row['Match']}**")
                st.write(f"Winner: {row['Winner']}")
            
            with col3:
                st.write(f"Date: {row['Date']}")
            
            with col4:
                if st.button(f"Edit #{row['ID']}", key=f"edit_match_{row['ID']}_{i}"):
                    st.session_state.editing_match = next((m for m in matches if m.get('id') == row['ID']), None)
            
            with col5:
                if st.button(f"Delete #{row['ID']}", key=f"delete_match_{row['ID']}_{i}"):
                    delete_match_data(row['ID'])
                    # Regenerate results
                    regenerate_results()
                    st.success(f"Match {row['Match']} deleted successfully!")
                    st.experimental_rerun()
            
            st.markdown("---")
        
        # Edit form if a match is selected for editing
        if st.session_state.editing_match:
            st.subheader(f"Edit Match #{st.session_state.editing_match.get('id', '')}")
            
            edit_col1, edit_col2 = st.columns(2)
            
            with edit_col1:
                team1 = st.selectbox("Team 1", all_teams, index=all_teams.index(st.session_state.editing_match.get('team1')) if st.session_state.editing_match.get('team1') in all_teams else 0)
                team1_bettors = st.multiselect("Team 1 Bettors", all_players, default=st.session_state.editing_match.get('team1_bettors', []))
            
            with edit_col2:
                team2 = st.selectbox("Team 2", all_teams, index=all_teams.index(st.session_state.editing_match.get('team2')) if st.session_state.editing_match.get('team2') in all_teams else 0)
                team2_bettors = st.multiselect("Team 2 Bettors", all_players, default=st.session_state.editing_match.get('team2_bettors', []))
            
            winner = st.radio("Winner", [team1, team2], index=0 if st.session_state.editing_match.get('winner') == team1 else 1)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("Save Changes"):
                    # Update match data
                    updated_match = {
                        "team1": team1,
                        "team1_bettors": team1_bettors,
                        "team2": team2,
                        "team2_bettors": team2_bettors,
                        "winner": winner
                    }
                    
                    update_match_data(st.session_state.editing_match.get('id'), updated_match)
                    
                    # Regenerate results
                    regenerate_results()
                    
                    st.success("Match updated successfully!")
                    st.session_state.editing_match = None
                    st.experimental_rerun()
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.editing_match = None
                    st.experimental_rerun()
        
        # Button to regenerate all results
        if st.button("Regenerate All Results"):
            regenerate_results()
            st.success("All results regenerated successfully!")
            st.experimental_rerun()
    else:
        st.info("No match history available. Please enter match data first.")

# View Results page
elif page == "View Results":
    st.header("Match Results")
    
    # Load all results
    results_df = load_results_from_csv()
    
    if not results_df.empty:
        # Filter options
        st.subheader("Filter Results")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_games = st.multiselect(
                "Select Games", 
                options=sorted(results_df['Game'].unique()),
                default=sorted(results_df['Game'].unique())
            )
        
        with col2:
            selected_players = st.multiselect(
                "Select Players", 
                options=sorted(results_df['Name'].unique()),
                default=[]
            )
        
        # Apply filters
        filtered_df = results_df
        if selected_games:
            filtered_df = filtered_df[filtered_df['Game'].isin(selected_games)]
        if selected_players:
            filtered_df = filtered_df[filtered_df['Name'].isin(selected_players)]
        
        # Display filtered results
        st.subheader("Filtered Results")
        st.dataframe(filtered_df)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bets", len(filtered_df))
        
        with col2:
            st.metric("Total Amount", f"₹{filtered_df['BetAmount'].sum():.2f}")
        
        with col3:
            winning_bets = filtered_df[filtered_df['NetResult'] > 0]
            st.metric("Winning Bets", len(winning_bets))
        
        with col4:
            winning_percentage = len(winning_bets) / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
            st.metric("Winning %", f"{winning_percentage:.1f}%")
        
        # Net result by player
        st.subheader("Net Result by Player")
        player_chart = st.session_state.viz_generator.generate_player_performance_chart(filtered_df)
        st.plotly_chart(player_chart, use_container_width=True)
    else:
        st.info("No results data available. Please enter match data first.")

# Player Stats page
elif page == "Player Stats":
    st.header("Player Statistics")
    
    # Load results data
    results_df = load_results_from_csv()
    
    if not results_df.empty:
        # Player performance chart
        st.subheader("Player Performance")
        player_chart = st.session_state.viz_generator.generate_player_performance_chart(results_df)
        st.plotly_chart(player_chart, use_container_width=True)
        
        # Player selection for detailed view
        selected_player = st.selectbox(
            "Select a player for detailed view",
            options=sorted(results_df['Name'].unique())
        )
        
        if selected_player:
            # Player betting history
            st.subheader(f"Betting History for {selected_player}")
            history_chart = st.session_state.viz_generator.generate_player_betting_history(selected_player, results_df)
            st.plotly_chart(history_chart, use_container_width=True)
            
            # Player stats
            player_df = results_df[results_df['Name'] == selected_player]
            total_bets = len(player_df)
            total_amount = player_df['BetAmount'].sum()
            net_result = player_df['NetResult'].sum()
            winning_bets = player_df[player_df['NetResult'] > 0]
            winning_percentage = len(winning_bets) / total_bets * 100 if total_bets > 0 else 0
            
            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bets", total_bets)
            
            with col2:
                st.metric("Total Amount", f"₹{total_amount:.2f}")
            
            with col3:
                st.metric("Net Result", f"₹{net_result:.2f}", delta=f"{net_result:.2f}")
            
            with col4:
                st.metric("Winning %", f"{winning_percentage:.1f}%")
            
            # Display player's bets
            st.subheader(f"{selected_player}'s Bets")
            st.dataframe(player_df)
    else:
        st.info("No player statistics available. Please enter match data first.")

# Team Stats page
elif page == "Team Stats":
    st.header("Team Statistics")
    
    # Load results data
    results_df = load_results_from_csv()
    
    if not results_df.empty:
        # Team performance chart
        st.subheader("Team Performance")
        team_chart = st.session_state.viz_generator.generate_team_performance_chart(results_df)
        st.plotly_chart(team_chart, use_container_width=True)
        
        # Team betting distribution
        st.subheader("Betting Distribution by Team")
        distribution_chart = st.session_state.viz_generator.generate_betting_distribution_chart(results_df)
        st.plotly_chart(distribution_chart, use_container_width=True)
        
        # Team selection for detailed view
        selected_team = st.selectbox(
            "Select a team for detailed view",
            options=sorted(results_df['Team'].unique())
        )
        
        if selected_team:
            # Team stats
            team_df = results_df[results_df['Team'] == selected_team]
            total_bets = len(team_df)
            total_amount = team_df['BetAmount'].sum()
            net_result = team_df['NetResult'].sum()
            winning_bets = team_df[team_df['NetResult'] > 0]
            winning_percentage = len(winning_bets) / total_bets * 100 if total_bets > 0 else 0
            
            # Display stats in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bets", total_bets)
            
            with col2:
                st.metric("Total Amount", f"₹{total_amount:.2f}")
            
            with col3:
                st.metric("Net Result", f"₹{net_result:.2f}", delta=f"{net_result:.2f}")
            
            with col4:
                st.metric("Winning %", f"{winning_percentage:.1f}%")
            
            # Display team's bets
            st.subheader(f"{selected_team}'s Bets")
            st.dataframe(team_df)
    else:
        st.info("No team statistics available. Please enter match data first.")

# Advanced Analytics page
elif page == "Advanced Analytics":
    st.header("Advanced Analytics")
    
    # Load results data
    results_df = load_results_from_csv()
    
    if not results_df.empty:
        # Tabs for different analytics
        tab1, tab3 = st.tabs(["Cumulative Performance", "Correlation Analysis"])
        
        with tab1:
            st.subheader("Cumulative Player Performance")
            cumulative_chart = st.session_state.viz_generator.generate_cumulative_performance_chart(results_df)
            st.plotly_chart(cumulative_chart, use_container_width=True)
            
            st.markdown("""
            This chart shows how each player's net result accumulates over time across multiple games.
            It helps identify consistent winners and losers, as well as trend changes.
            """)
        
        with tab3:
            st.subheader("Player Correlation Analysis")
            
            # Generate heatmap
            _, heatmap_path = st.session_state.viz_generator.generate_heatmap(results_df)
            
            # Display heatmap if it exists
            if os.path.exists(heatmap_path):
                heatmap_img = Image.open(heatmap_path)
                st.image(heatmap_img, use_column_width=True)
                
                st.markdown("""
                This correlation heatmap shows how similar players' betting patterns are.
                - Values close to 1.0 (red) indicate players who frequently bet on the same teams
                - Values close to 0.0 (blue) indicate players who rarely bet on the same teams
                """)
            else:
                st.info("Correlation heatmap not available. Please enter more match data.")
    else:
        st.info("No advanced analytics available. Please enter match data first.")

# Dashboard page has been removed as requested

# Footer
st.markdown("---")
st.markdown("IPL Betting Tracker App | Created with Streamlit")

# Stop background processor when the app is closed
def on_shutdown():
    if 'processor' in st.session_state:
        st.session_state.processor.stop_processing_thread()

# Register the shutdown handler
import atexit
atexit.register(on_shutdown)
