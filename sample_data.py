import os
import pandas as pd
from data_utils import save_match_data, save_results_to_csv, load_players, compute_betting_result_df

def generate_sample_data():
    """Generate sample data for testing the application"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Load player data
    player_team_map, team_owners_map = load_players()
    
    # Sample matches
    sample_matches = [
        {
            "team1": "RCB",
            "team1_bettors": ["Param", "Amar", "Sreedhar", "Atul", "Anshuman"],
            "team2": "KKR",
            "team2_bettors": ["Utkarsh", "Gurpreet", "Harman", "Jagjit", "Karam", "Nishit", "Adithya", "Niraj"],
            "winner": "KKR"
        },
        {
            "team1": "SRH",
            "team1_bettors": ["Shravan", "Jagjit", "Atul", "Manish", "Ankur", "Utkarsh", "Parminder", "Karam", "Niraj", "Adithya"],
            "team2": "RR",
            "team2_bettors": ["Harman", "Anshuman", "Amar", "Nishit"],
            "winner": "SRH"
        },
        {
            "team1": "MI",
            "team1_bettors": ["Utkarsh", "Nishit", "Gurpreet", "Ankur"],
            "team2": "CSK",
            "team2_bettors": ["Niraj", "Anshuman", "Sreedhar", "Param"],
            "winner": "CSK"
        }
    ]
    
    # Save sample matches and compute results
    all_results = []
    
    for match in sample_matches:
        # Save match data
        save_match_data(match)
        
        # Compute results
        results_df = compute_betting_result_df(
            match["team1"], 
            match["team2"], 
            match["winner"], 
            match["team1_bettors"], 
            match["team2_bettors"],
            player_team_map, 
            team_owners_map
        )
        
        all_results.append(results_df)
    
    # Combine all results
    combined_results = pd.concat(all_results, ignore_index=True)
    
    # Save combined results
    save_results_to_csv(combined_results)
    
    print(f"Generated sample data for {len(sample_matches)} matches")
    print(f"Total betting records: {len(combined_results)}")

if __name__ == "__main__":
    generate_sample_data()
