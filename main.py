#!/usr/bin/env python
import pandas as pd
import argparse

def load_data(csv_path):
    # Read CSV with low_memory=False to avoid DtypeWarning.
    df = pd.read_csv(csv_path, low_memory=False)
    # Convert the 'Date' column, coercing errors to NaT
    # Remove deprecated infer_datetime_format parameter
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Drop rows where 'Date' could not be parsed.
    df = df.dropna(subset=['Date'])
    return df


def filter_time_period(df, start_date, end_date):
    """
    Filter the DataFrame rows based on the provided date range.
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return df[(df['Date'] >= start) & (df['Date'] <= end)]

def compute_alignment(df, target_country):
    """
    Compute the percentage of votes in common for the target country against all other countries.
    It assumes that vote columns begin after the fixed metadata columns (i.e., after 'token').
    """
    # Identify vote columns – adjust the index if your CSV structure changes.
    vote_columns = df.columns.tolist()[11:]
    
    if target_country not in vote_columns:
        raise ValueError(f"Target country '{target_country}' not found in vote columns.")
    
    # Initialize dictionaries to track common votes and total comparisons.
    common_votes = {country: 0 for country in vote_columns if country != target_country}
    total_votes = {country: 0 for country in vote_columns if country != target_country}
    
    # Iterate over each resolution row.
    for _, row in df.iterrows():
        target_vote = row[target_country]
        # Skip if target vote is missing.
        if pd.isna(target_vote):
            continue
        # Compare with every other country.
        for country in vote_columns:
            if country == target_country:
                continue
            other_vote = row[country]
            if pd.isna(other_vote):
                continue
            total_votes[country] += 1
            if other_vote == target_vote:
                common_votes[country] += 1
                
    # Calculate percentage of alignment for each country.
    percentages = {}
    vote_counts = {}
    for country in common_votes:
        if total_votes[country] > 0:
            percentages[country] = common_votes[country] / total_votes[country]
            vote_counts[country] = total_votes[country]
        else:
            percentages[country] = None  # Not enough data for comparison.
            vote_counts[country] = 0
    return percentages, vote_counts

def find_top_allies_and_enemies(percentages, vote_counts, top_n=3, min_votes=20):
    """
    Identify the top N allies (highest percentage) and top N enemies (lowest percentage)
    from the computed percentages.
    
    Parameters:
    - percentages: Dict of country name to alignment percentage
    - vote_counts: Dict of country name to number of votes compared
    - top_n: Number of allies/enemies to return
    - min_votes: Minimum number of votes required to be considered
    """
    # Filter countries with enough votes
    valid = {country: pct for country, pct in percentages.items() 
             if pct is not None and vote_counts[country] >= min_votes}
    
    if not valid:
        return [], [], [], [], [], []
        
    # Sort valid countries by alignment percentage
    sorted_countries = sorted(valid.items(), key=lambda x: x[1], reverse=True)
    
    # Get top N allies (highest alignment)
    top_allies = sorted_countries[:top_n]
    allies = [country for country, _ in top_allies]
    allies_pct = [pct for _, pct in top_allies]
    allies_votes = [vote_counts[country] for country in allies]
    
    # Get top N enemies (lowest alignment)
    top_enemies = sorted_countries[-top_n:]
    top_enemies.reverse()  # Reverse to show worst first
    enemies = [country for country, _ in top_enemies]
    enemies_pct = [pct for _, pct in top_enemies]
    enemies_votes = [vote_counts[country] for country in enemies]
    
    return allies, enemies, allies_pct, enemies_pct, allies_votes, enemies_votes

def analyze_alignment_shift(df, target_country, start_date, end_date, min_votes=20):
    """
    Split the time period in half and analyze which countries had the biggest shifts
    in their voting alignment with the target country.
    
    Parameters:
    - df: The complete dataframe with voting data
    - target_country: The country to analyze alignment with
    - start_date: The start date of the analysis period
    - end_date: The end date of the analysis period
    - min_votes: Minimum number of votes required in each half to be considered
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    midpoint = start + (end - start) / 2
    
    # Filter data for first and second half of the period
    first_half = df[(df['Date'] >= start) & (df['Date'] < midpoint)]
    second_half = df[(df['Date'] >= midpoint) & (df['Date'] <= end)]
    
    # Compute alignments for both periods
    first_alignments, first_vote_counts = compute_alignment(first_half, target_country)
    second_alignments, second_vote_counts = compute_alignment(second_half, target_country)
    
    # Calculate shifts in alignment with minimum vote threshold
    shifts = {}
    for country in first_alignments:
        if (country in second_alignments and 
            first_alignments[country] is not None and 
            second_alignments[country] is not None and
            first_vote_counts[country] >= min_votes and
            second_vote_counts[country] >= min_votes):
            shifts[country] = second_alignments[country] - first_alignments[country]
    
    if not shifts:
        return None, None, 0, 0, 0, 0, 0
    
    # Find country with biggest positive and negative shifts
    max_shift_country = max(shifts.items(), key=lambda x: x[1])
    min_shift_country = min(shifts.items(), key=lambda x: x[1])
    
    # If the biggest shift is more significant than the biggest negative shift
    if abs(max_shift_country[1]) >= abs(min_shift_country[1]):
        biggest_shift = max_shift_country
        shift_direction = "positive"
    else:
        biggest_shift = min_shift_country
        shift_direction = "negative"
    
    country = biggest_shift[0]
    
    return (country, 
            shift_direction, 
            biggest_shift[1], 
            first_alignments.get(country), 
            second_alignments.get(country),
            first_vote_counts.get(country, 0),
            second_vote_counts.get(country, 0))

def main():
    parser = argparse.ArgumentParser(description="Analyze UN voting alignments to find best allies and worst enemies.")
    parser.add_argument('--csv', type=str, required=True, help="Path to the UN data CSV file")
    parser.add_argument('--country', type=str, required=True, help="Target country to analyze (e.g., 'SENEGAL')")
    parser.add_argument('--start', type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument('--min-votes', type=int, default=20, help="Minimum number of votes required for a country to be considered (default: 20)")
    parser.add_argument('--top-n', type=int, default=5, help="Number of top allies and enemies to show (default: 5)")
    args = parser.parse_args()
    
    # Load and filter data
    df = load_data(args.csv)
    df_filtered = filter_time_period(df, args.start, args.end)
    
    # Compute vote alignments
    percentages, vote_counts = compute_alignment(df_filtered, args.country)
    
    # Find top allies and enemies
    allies, enemies, allies_pct, enemies_pct, allies_votes, enemies_votes = find_top_allies_and_enemies(
        percentages, vote_counts, top_n=args.top_n, min_votes=args.min_votes
    )
    
    # Analyze alignment shifts over time
    shift_results = analyze_alignment_shift(
        df, args.country, args.start, args.end, min_votes=args.min_votes
    )
    
    shift_country, shift_direction, shift_value, first_half_value, second_half_value, first_half_votes, second_half_votes = shift_results
    
    if not allies:
        print(f"No valid vote comparisons with at least {args.min_votes} votes found for the specified period.")
    else:
        print(f"Analysis for {args.country} between {args.start} and {args.end} (minimum {args.min_votes} votes):")
        
        # Display top allies
        print(f"\nTop {args.top_n} Allies:")
        for i, (country, pct, votes) in enumerate(zip(allies, allies_pct, allies_votes)):
            print(f"  {i+1}. {country} with {pct*100:.2f}% votes in common ({votes} votes)")
        
        # Display top enemies
        print(f"\nTop {args.top_n} Enemies:")
        for i, (country, pct, votes) in enumerate(zip(enemies, enemies_pct, enemies_votes)):
            print(f"  {i+1}. {country} with {pct*100:.2f}% votes in common ({votes} votes)")
        
        # Display biggest shift
        if shift_country:
            print(f"\nBiggest Alignment Shift: {shift_country}")
            print(f"  Direction: {shift_direction}")
            print(f"  First half alignment: {first_half_value*100:.2f}% ({first_half_votes} votes)")
            print(f"  Second half alignment: {second_half_value*100:.2f}% ({second_half_votes} votes)")
            print(f"  Shift: {abs(shift_value)*100:.2f}% {'increase' if shift_value > 0 else 'decrease'}")
        else:
            print(f"\nNo significant alignment shifts detected with at least {args.min_votes} votes in each period.")

if __name__ == "__main__":
    main()
