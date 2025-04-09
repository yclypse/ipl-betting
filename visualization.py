import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from typing import Dict, List, Optional, Tuple

class VisualizationGenerator:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def load_results_data(self) -> pd.DataFrame:
        """Load results data from CSV file"""
        results_file = os.path.join(self.data_dir, "results.csv")
        if not os.path.exists(results_file):
            return pd.DataFrame(columns=["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"])
        
        try:
            return pd.read_csv(results_file)
        except:
            return pd.DataFrame(columns=["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"])
    
    def generate_player_performance_chart(self, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate an interactive player performance chart"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="No Player Performance Data Available",
                xaxis_title="Player",
                yaxis_title="Net Result (₹)"
            )
            return fig
        
        # Aggregate results by player
        player_results = results_df.groupby('Name')['NetResult'].sum().reset_index()
        player_results = player_results.sort_values('NetResult', ascending=False)
        
        # Create color scale based on values
        colors = ['red' if x < 0 else 'green' for x in player_results['NetResult']]
        
        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=player_results['Name'],
                y=player_results['NetResult'],
                marker_color=colors,
                text=player_results['NetResult'].apply(lambda x: f'₹{x:.2f}'),
                textposition='auto',
                hoverinfo='text',
                hovertext=[f"{name}: ₹{value:.2f}" for name, value in 
                           zip(player_results['Name'], player_results['NetResult'])]
            )
        )
        
        # Update layout
        fig.update_layout(
            title="Player Performance",
            xaxis_title="Player",
            yaxis_title="Net Result (₹)",
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            xaxis=dict(tickangle=-45),
            height=600
        )
        
        # Save the figure data
        player_results.to_csv(os.path.join(self.data_dir, "player_performance.csv"), index=False)
        
        return fig
    
    def generate_team_performance_chart(self, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate an interactive team performance chart"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="No Team Performance Data Available",
                xaxis_title="Team",
                yaxis_title="Net Result (₹)"
            )
            return fig
        
        # Aggregate results by team
        team_results = results_df.groupby('Team')['NetResult'].sum().reset_index()
        team_results = team_results.sort_values('NetResult', ascending=False)
        
        # Create color scale based on values
        colors = ['red' if x < 0 else 'green' for x in team_results['NetResult']]
        
        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=team_results['Team'],
                y=team_results['NetResult'],
                marker_color=colors,
                text=team_results['NetResult'].apply(lambda x: f'₹{x:.2f}'),
                textposition='auto',
                hoverinfo='text',
                hovertext=[f"{team}: ₹{value:.2f}" for team, value in 
                           zip(team_results['Team'], team_results['NetResult'])]
            )
        )
        
        # Update layout
        fig.update_layout(
            title="Team Performance",
            xaxis_title="Team",
            yaxis_title="Net Result (₹)",
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            height=500
        )
        
        # Save the figure data
        team_results.to_csv(os.path.join(self.data_dir, "team_performance.csv"), index=False)
        
        return fig
    
    def generate_betting_distribution_chart(self, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate a pie chart showing distribution of bets by team"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="No Betting Distribution Data Available"
            )
            return fig
        
        # Get bet counts by team
        team_bet_counts = results_df['BetOn'].value_counts().reset_index()
        team_bet_counts.columns = ['Team', 'Count']
        
        # Create figure
        fig = go.Figure(
            go.Pie(
                labels=team_bet_counts['Team'],
                values=team_bet_counts['Count'],
                hole=0.4,
                textinfo='label+percent',
                marker=dict(
                    colors=px.colors.qualitative.Pastel
                )
            )
        )
        
        # Update layout
        fig.update_layout(
            title="Distribution of Bets by Team",
            height=500
        )
        
        # Save the figure data
        team_bet_counts.to_csv(os.path.join(self.data_dir, "betting_distribution.csv"), index=False)
        
        return fig
    
    def generate_player_betting_history(self, player_name: str, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate a line chart showing a player's betting history over time"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty or player_name not in results_df['Name'].unique():
            # Return empty figure if no data or player not found
            fig = go.Figure()
            fig.update_layout(
                title=f"No Betting History Available for {player_name}",
                xaxis_title="Game",
                yaxis_title="Net Result (₹)"
            )
            return fig
        
        # Filter data for the specified player
        player_df = results_df[results_df['Name'] == player_name]
        
        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=player_df['Game'],
                y=player_df['NetResult'],
                mode='lines+markers',
                name=player_name,
                line=dict(width=3),
                marker=dict(
                    size=10,
                    color=player_df['NetResult'],
                    colorscale='RdYlGn',
                    showscale=True
                )
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f"Betting History for {player_name}",
            xaxis_title="Game",
            yaxis_title="Net Result (₹)",
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            xaxis=dict(tickangle=-45),
            height=500
        )
        
        return fig
    
    def generate_cumulative_performance_chart(self, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate a cumulative performance chart for all players"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="No Cumulative Performance Data Available",
                xaxis_title="Game",
                yaxis_title="Cumulative Net Result (₹)"
            )
            return fig
        
        # Get unique players and games
        players = results_df['Name'].unique()
        games = results_df['Game'].unique()
        
        # Create figure
        fig = go.Figure()
        
        # For each player, calculate cumulative sum across games
        for player in players:
            player_df = results_df[results_df['Name'] == player]
            player_results = []
            cumulative_sum = 0
            
            for game in games:
                game_result = player_df[player_df['Game'] == game]['NetResult'].sum()
                cumulative_sum += game_result
                player_results.append(cumulative_sum)
            
            # Add trace for this player
            fig.add_trace(
                go.Scatter(
                    x=games,
                    y=player_results,
                    mode='lines+markers',
                    name=player,
                    hoverinfo='text',
                    hovertext=[f"{player} (after {game}): ₹{result:.2f}" 
                               for game, result in zip(games, player_results)]
                )
            )
        
        # Update layout
        fig.update_layout(
            title="Cumulative Player Performance Over Time",
            xaxis_title="Game",
            yaxis_title="Cumulative Net Result (₹)",
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            xaxis=dict(tickangle=-45),
            height=700,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def generate_heatmap(self, results_df: Optional[pd.DataFrame] = None) -> Tuple[plt.Figure, str]:
        """Generate a heatmap showing correlation between players' betting patterns"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, "No Heatmap Data Available", 
                    horizontalalignment='center', verticalalignment='center')
            plt.close(fig)
            return fig, os.path.join(self.data_dir, "heatmap.png")
        
        # Create a pivot table: players vs games with bet team as values
        pivot_df = results_df.pivot_table(
            index='Name', 
            columns='Game', 
            values='BetOn', 
            aggfunc='first'
        ).fillna('')
        
        # Calculate correlation matrix
        # 1 if two players bet on the same team, 0 otherwise
        players = pivot_df.index.tolist()
        n_players = len(players)
        corr_matrix = pd.DataFrame(0.0, index=players, columns=players, dtype=float)
        
        for i in range(n_players):
            # Set diagonal to 1.0
            corr_matrix.iloc[i, i] = 1.0
            
            for j in range(i+1, n_players):  # Only calculate upper triangle
                # Count matches where both players bet on the same team
                player1_bets = pivot_df.iloc[i].values
                player2_bets = pivot_df.iloc[j].values
                
                # Count same bets and common games
                same_bet_count = 0
                common_game_count = 0
                
                for k in range(len(player1_bets)):
                    if player1_bets[k] != '' and player2_bets[k] != '':
                        common_game_count += 1
                        if player1_bets[k] == player2_bets[k]:
                            same_bet_count += 1
                
                # Calculate correlation
                if common_game_count > 0:
                    correlation = same_bet_count / common_game_count
                else:
                    correlation = 0.0
                
                # Set values in both upper and lower triangle
                corr_matrix.iloc[i, j] = correlation
                corr_matrix.iloc[j, i] = correlation  # Mirror value
        
        # Ensure all values are float
        corr_matrix = corr_matrix.astype(float)
        
        try:
            # Create heatmap
            plt.figure(figsize=(12, 10))
            sns.set(font_scale=1.2)
            heatmap = sns.heatmap(
                corr_matrix, 
                annot=True, 
                cmap='coolwarm', 
                linewidths=0.5, 
                fmt='.2f',
                vmin=0, 
                vmax=1
            )
            plt.title('Correlation of Betting Patterns Between Players', fontsize=16)
            plt.tight_layout()
            
            # Save the heatmap
            heatmap_path = os.path.join(self.data_dir, "heatmap.png")
            plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return heatmap.figure, heatmap_path
        except Exception as e:
            # Fallback if heatmap generation fails
            print(f"Error generating heatmap: {e}")
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, f"Error generating heatmap: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center')
            
            # Save the error message as image
            error_path = os.path.join(self.data_dir, "heatmap_error.png")
            plt.savefig(error_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            return fig, error_path
    
    def generate_summary_dashboard(self, results_df: Optional[pd.DataFrame] = None) -> go.Figure:
        """Generate a comprehensive dashboard with multiple visualizations"""
        if results_df is None:
            results_df = self.load_results_data()
        
        if results_df.empty:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title="No Dashboard Data Available"
            )
            return fig
        
        # Create subplot figure with 2x2 grid, but only use 3 cells
        fig = make_subplots(
            rows=2, 
            cols=2,
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "bar"}, None]  # Changed to None to remove the 4th plot
            ],
            subplot_titles=[
                "All Players by Net Result", 
                "Betting Distribution by Team",
                "Team Performance"
            ]
        )
        
        # 1. All Players (not just top 5)
        player_results = results_df.groupby('Name')['NetResult'].sum().reset_index()
        all_players = player_results.sort_values('NetResult', ascending=False)
        
        fig.add_trace(
            go.Bar(
                x=all_players['Name'],
                y=all_players['NetResult'],
                marker_color='lightgreen',
                text=all_players['NetResult'].apply(lambda x: f'₹{x:.2f}'),
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # 2. Betting Distribution
        team_bet_counts = results_df['BetOn'].value_counts().reset_index()
        team_bet_counts.columns = ['Team', 'Count']
        
        fig.add_trace(
            go.Pie(
                labels=team_bet_counts['Team'],
                values=team_bet_counts['Count'],
                textinfo='label+percent'
            ),
            row=1, col=2
        )
        
        # 3. Team Performance
        team_results = results_df.groupby('Team')['NetResult'].sum().reset_index()
        team_results = team_results.sort_values('NetResult', ascending=False)
        
        fig.add_trace(
            go.Bar(
                x=team_results['Team'],
                y=team_results['NetResult'],
                marker_color=['red' if x < 0 else 'green' for x in team_results['NetResult']],
                text=team_results['NetResult'].apply(lambda x: f'₹{x:.2f}'),
                textposition='auto'
            ),
            row=2, col=1
        )
        
        # Recent Betting Trends section has been removed as requested
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="IPL Betting Dashboard",
            plot_bgcolor='rgba(240, 240, 240, 0.8)'
        )
        
        # Update axes
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        fig.update_xaxes(tickangle=-45, row=2, col=1)
        
        return fig
