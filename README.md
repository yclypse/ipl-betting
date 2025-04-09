# IPL Betting Tracker

A Streamlit application for tracking IPL cricket betting results and visualizing performance metrics.

## Features

- **Match Data Entry**: Enter match data in batch format with multiple matches support
- **Match History**: View, edit, and delete past matches with automatic result regeneration
- **Results Viewing**: Comprehensive results table with filtering options
- **Player Statistics**: Interactive performance charts and detailed player analytics
- **Team Statistics**: Team performance visualization and betting distribution
- **Advanced Analytics**: Cumulative performance tracking, betting pattern analysis, and correlation heatmaps
- **Dashboard**: Summary dashboard with key metrics and recent match history

## Project Structure

- `app.py`: Main Streamlit application
- `data_utils.py`: Data handling utilities for loading, saving, and processing match data
- `background_processor.py`: Background processing for data updates and visualization generation
- `visualization.py`: Visualization components for charts and analytics
- `sample_data.py`: Script to generate sample data for testing
- `data/`: Directory for storing match data and results

## Requirements

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- Matplotlib
- Seaborn

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ipl-betting-tracker.git
cd ipl-betting-tracker

# Install dependencies
pip install streamlit pandas plotly matplotlib seaborn
```

## Usage

```bash
# Run the Streamlit application
streamlit run app.py
```

## Data Format

The application accepts match data in the following format:

```
TEAM1 (number)
Player1,Player2,Player3,...
TEAM2 (number)
Player1,Player2,Player3,...
----------------------------------------------------------------------
```

Multiple matches can be included by separating them with dashed lines. Winners should be specified as team codes separated by semicolons (one for each match).

## License

MIT
