import pandas as pd
from typing import List, Tuple
from collections import defaultdict
import re
import json
import os
from datetime import datetime

# Function to load players
def load_players() -> Tuple[dict, dict]:
    players = [
        ("Gurpreet", "SRH"),
        ("Sreedhar", "SRH"),
        ("Utkarsh", "MI"),
        ("Jagjit", "DC"),
        ("Nishit", "MI"),
        ("Niraj", "CSK"),
        ("Adithya", "GT"),
        ("Parminder", "KKR"),
        ("Manish", "KKR"),
        ("Param", "RR"),
        ("Karam", "PBKS"),
        ("Shravan", "RCB"),
        ("Harman", "PBKS"),
        ("Atul", "GT"),
        ("Ankur", "RCB"),
        ("Amar", "LSG"),
        ("Anshuman", "CSK"),
    ]
    player_team_map = {name: team for name, team in players}
    team_owners_map = defaultdict(list)
    for name, team in players:
        team_owners_map[team].append(name)
    return player_team_map, team_owners_map

# Parse multiple matches
def parse_multiple_matches(input_str: str) -> List[Tuple[str, List[str], str, List[str]]]:
    matches = input_str.strip().split('----------------------------------------------------------------------')
    parsed_matches = []
    for match in matches:
        lines = [line.strip() for line in match.strip().split('\n') if line.strip()]
        if len(lines) >= 4:
            team1_line, team1_users = lines[0], lines[1]
            team2_line, team2_users = lines[2], lines[3]
            team1 = re.match(r'(\w+)', team1_line).group(1)
            team2 = re.match(r'(\w+)', team2_line).group(1)
            team1_bettors = [name.strip() for name in team1_users.split(',') if name.strip()]
            team2_bettors = [name.strip() for name in team2_users.split(',') if name.strip()]
            parsed_matches.append((team1, team1_bettors, team2, team2_bettors))
    return parsed_matches

# Updated result computation
def compute_betting_result_df(
    team1: str,
    team2: str,
    winner: str,
    team1_bettors: List[str],
    team2_bettors: List[str],
    player_team_map: dict,
    team_owners_map: dict
) -> pd.DataFrame:
    results = []
    game = f"{team1} vs {team2}"

    all_players = set(player_team_map.keys())
    team1_owners = set(team_owners_map.get(team1, []))
    team2_owners = set(team_owners_map.get(team2, []))
    all_owners = team1_owners.union(team2_owners)

    voted_players = set(team1_bettors + team2_bettors)
    non_voters = all_players - voted_players - all_owners

    # Determine the losing team
    losing_team = team2 if winner == team1 else team1

    # Owners' automatic bets
    owner_bets = {}
    if len(team1_owners) == 1 and len(team2_owners) == 1:
        for owner in team1_owners | team2_owners:
            owner_bets[owner] = 15
    elif len(team1_owners) == 2 and len(team2_owners) == 1:
        for owner in team1_owners:
            owner_bets[owner] = 7.5
        for owner in team2_owners:
            owner_bets[owner] = 15
    elif len(team1_owners) == 1 and len(team2_owners) == 2:
        for owner in team1_owners:
            owner_bets[owner] = 15
        for owner in team2_owners:
            owner_bets[owner] = 7.5
    else:
        for owner in team1_owners | team2_owners:
            owner_bets[owner] = 15

    for owner, amount in owner_bets.items():
        owner_team = player_team_map[owner]
        results.append({
            "Name": owner,
            "Game": game,
            "Type": "Owner",
            "Team": owner_team,
            "BetOn": owner_team,
            "BetAmount": amount,
            "NetResult": amount if owner_team == winner else -amount
        })

    # Filter owners from voting bettors
    clean_team1_bettors = [b for b in team1_bettors if b not in all_owners]
    clean_team2_bettors = [b for b in team2_bettors if b not in all_owners]

    # Assign non-voters to the losing team (unless they are owners)
    auto_assigned = [(nv, losing_team) for nv in non_voters]

    # Final list of (bettor, team)
    non_owner_bettors = [(b, team1) for b in clean_team1_bettors] + \
                        [(b, team2) for b in clean_team2_bettors] + \
                        auto_assigned

    # Deduplicate
    seen = set()
    unique_non_owner_bettors = []
    for b, t in non_owner_bettors:
        if b not in seen:
            unique_non_owner_bettors.append((b, t))
            seen.add(b)

    total_pool = len(unique_non_owner_bettors) * 8
    winning_bettors = [b for b, t in unique_non_owner_bettors if t == winner]
    share = total_pool / len(winning_bettors) if winning_bettors else 0

    for bettor, team in unique_non_owner_bettors:
        results.append({
            "Name": bettor,
            "Game": game,
            "Type": "Non-owner",
            "Team": player_team_map.get(bettor, "Unknown"),
            "BetOn": team,
            "BetAmount": 8,
            "NetResult": round(share - 8, 2) if team == winner else -8
        })

    df = pd.DataFrame(results)
    df = df[["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"]]
    return df.sort_values(by="Name").reset_index(drop=True)

# Function to save match data to JSON
def save_match_data(match_data, file_path="data/matches.json"):
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Load existing data if file exists
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    # Add timestamp and unique ID to new data
    match_data['timestamp'] = datetime.now().isoformat()
    match_data['id'] = str(len(existing_data))
    
    # Append new data
    existing_data.append(match_data)
    
    # Save updated data
    with open(file_path, 'w') as f:
        json.dump(existing_data, f, indent=2)
    
    return file_path

# Function to load match data from JSON
def load_match_data(file_path="data/matches.json"):
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return []

# Function to update a specific match
def update_match_data(match_id, updated_match, file_path="data/matches.json"):
    # Load existing data
    matches = load_match_data(file_path)
    
    # Find the match with the given ID
    for i, match in enumerate(matches):
        if match.get('id') == match_id:
            # Preserve the original timestamp and ID
            updated_match['timestamp'] = match.get('timestamp')
            updated_match['id'] = match_id
            
            # Update the match
            matches[i] = updated_match
            break
    
    # Save updated data
    with open(file_path, 'w') as f:
        json.dump(matches, f, indent=2)
    
    return file_path

# Function to delete a specific match
def delete_match_data(match_id, file_path="data/matches.json"):
    # Load existing data
    matches = load_match_data(file_path)
    
    # Filter out the match with the given ID
    updated_matches = [match for match in matches if match.get('id') != match_id]
    
    # Save updated data
    with open(file_path, 'w') as f:
        json.dump(updated_matches, f, indent=2)
    
    return file_path

# Function to regenerate results after editing matches
def regenerate_results(file_path="data/matches.json", results_file="data/results.csv"):
    # Load all matches
    matches = load_match_data(file_path)
    
    # Clear existing results
    if os.path.exists(results_file):
        os.remove(results_file)
    
    # Load player data
    player_team_map, team_owners_map = load_players()
    
    # Process each match and save results
    all_results = []
    for match in matches:
        team1 = match.get('team1')
        team2 = match.get('team2')
        winner = match.get('winner')
        team1_bettors = match.get('team1_bettors', [])
        team2_bettors = match.get('team2_bettors', [])
        
        # Compute results
        results_df = compute_betting_result_df(
            team1, team2, winner, team1_bettors, team2_bettors,
            player_team_map, team_owners_map
        )
        
        all_results.append(results_df)
    
    # Combine all results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        
        # Save to CSV
        save_results_to_csv(combined_results, results_file)
        
        return combined_results
    
    return pd.DataFrame(columns=["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"])

# Function to save results data to CSV
def save_results_to_csv(results_df, file_path="data/results.csv"):
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save to CSV (overwrite mode)
    results_df.to_csv(file_path, index=False)
    
    return file_path

# Function to load all results from CSV
def load_results_from_csv(file_path="data/results.csv"):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"])
    
    try:
        return pd.read_csv(file_path)
    except:
        return pd.DataFrame(columns=["Name", "Game", "Type", "Team", "BetOn", "BetAmount", "NetResult"])
