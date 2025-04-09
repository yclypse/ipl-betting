import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_utils import load_players, compute_betting_result_df, load_results_from_csv
import os
import threading
import time
from typing import Dict, List, Callable

class BackgroundProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.player_team_map, self.team_owners_map = load_players()
        self.results_file = os.path.join(data_dir, "results.csv")
        self.callback_functions = []
        self.processing_thread = None
        self.stop_processing = False
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def register_callback(self, callback_fn: Callable):
        """Register a callback function to be called when data is updated"""
        self.callback_functions.append(callback_fn)
    
    def notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback_fn in self.callback_functions:
            try:
                callback_fn()
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def start_processing(self, interval=5):
        """Start background processing thread"""
        if self.processing_thread is not None and self.processing_thread.is_alive():
            return
        
        self.stop_processing = False
        self.processing_thread = threading.Thread(
            target=self._background_process, 
            args=(interval,)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_processing_thread(self):
        """Stop the background processing thread"""
        self.stop_processing = True
        if self.processing_thread is not None:
            self.processing_thread.join(timeout=1)
    
    def _background_process(self, interval):
        """Background processing function that runs periodically"""
        while not self.stop_processing:
            try:
                # Process data and update visualizations
                self.update_visualizations()
                
                # Notify callbacks that data has been updated
                self.notify_callbacks()
            except Exception as e:
                print(f"Error in background processing: {e}")
            
            # Sleep for the specified interval
            time.sleep(interval)
    
    def update_visualizations(self):
        """Update all visualizations based on current data"""
        # This will be called periodically by the background thread
        # and will update all visualization data
        
        # Load the latest results
        results_df = load_results_from_csv(self.results_file)
        
        # Generate visualization data
        self.generate_player_performance_chart(results_df)
        self.generate_team_performance_chart(results_df)
        self.generate_betting_summary(results_df)
    
    def generate_player_performance_chart(self, results_df):
        """Generate player performance chart data"""
        if results_df.empty:
            return None
        
        # Aggregate results by player
        player_results = results_df.groupby('Name')['NetResult'].sum().reset_index()
        player_results = player_results.sort_values('NetResult', ascending=False)
        
        # Save the chart data
        player_results.to_csv(os.path.join(self.data_dir, "player_performance.csv"), index=False)
        
        return player_results
    
    def generate_team_performance_chart(self, results_df):
        """Generate team performance chart data"""
        if results_df.empty:
            return None
        
        # Aggregate results by team
        team_results = results_df.groupby('Team')['NetResult'].sum().reset_index()
        team_results = team_results.sort_values('NetResult', ascending=False)
        
        # Save the chart data
        team_results.to_csv(os.path.join(self.data_dir, "team_performance.csv"), index=False)
        
        return team_results
    
    def generate_betting_summary(self, results_df):
        """Generate betting summary statistics"""
        if results_df.empty:
            return None
        
        # Calculate summary statistics
        total_bets = len(results_df)
        total_amount = results_df['BetAmount'].sum()
        winning_bets = results_df[results_df['NetResult'] > 0]
        winning_percentage = len(winning_bets) / total_bets * 100 if total_bets > 0 else 0
        
        # Create summary dataframe
        summary = pd.DataFrame([{
            'TotalBets': total_bets,
            'TotalAmount': total_amount,
            'WinningBets': len(winning_bets),
            'WinningPercentage': winning_percentage
        }])
        
        # Save the summary data
        summary.to_csv(os.path.join(self.data_dir, "betting_summary.csv"), index=False)
        
        return summary
    
    def process_new_match(self, team1, team1_bettors, team2, team2_bettors, winner):
        """Process a new match and update results"""
        # Compute betting results
        results_df = compute_betting_result_df(
            team1, team2, winner, team1_bettors, team2_bettors,
            self.player_team_map, self.team_owners_map
        )
        
        # Save results to CSV (append mode)
        results_file = os.path.join(self.data_dir, "results.csv")
        file_exists = os.path.isfile(results_file)
        results_df.to_csv(results_file, mode='a', header=not file_exists, index=False)
        
        # Update visualizations immediately
        self.update_visualizations()
        
        # Notify callbacks
        self.notify_callbacks()
        
        return results_df
