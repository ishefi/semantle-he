import datetime

import matplotlib.pyplot as plt
import pandas as pd
from sqlmodel import text

from common.session import get_session  # Use your existing session


def analyze_guess_counts(sample_size=500, min_games=3, recent_months=12):
    """
    Analyze how players' guess counts change over time with improved performance.

    Args:
        sample_size: Number of users to sample for analysis
        min_games: Minimum number of games a user must have played to be included
        recent_months: Only analyze games from the most recent X months
    """
    with get_session() as session:
        # Get the cutoff date for recent data
        current_date = datetime.datetime.now()
        cutoff_date = current_date - datetime.timedelta(days=30 * recent_months)

        # Step 1: Sample active users with a more efficient query
        active_users_query = text(f"""
            SELECT TOP {sample_size} user_id
            FROM (
                SELECT user_id, COUNT(DISTINCT game_date) as game_count
                FROM userhistory 
                WHERE game_date >= '{cutoff_date.strftime('%Y-%m-%d')}'
                GROUP BY user_id
                HAVING COUNT(DISTINCT game_date) >= {min_games}
            ) as active_users
            ORDER BY NEWID()
        """)

        print(
            f"Sampling users who played {min_games}+ games in the last {recent_months} months..."
        )
        sample_user_ids = [row[0] for row in session.execute(active_users_query)]
        print(f"Sampled {len(sample_user_ids)} active users")

        if not sample_user_ids:
            print(
                "No users match the criteria. Try reducing min_games or increasing recent_months."
            )
            return pd.DataFrame()

        # Step 2: Pre-filter for only successful games (with distance=1000)
        # This greatly reduces the data we need to process
        success_query = text(f"""
            WITH UserSuccesses AS (
                -- Find all successful guesses
                SELECT user_id, game_date, MIN(id) as first_success_id
                FROM userhistory
                WHERE 
                    user_id IN ({','.join(['?'] * len(sample_user_ids))})
                    AND distance = 1000
                    AND game_date >= '{cutoff_date.strftime('%Y-%m-%d')}'
                GROUP BY user_id, game_date
            )
            -- Get the count of guesses needed to reach success
            SELECT 
                uh.user_id,
                uh.game_date,
                YEAR(uh.game_date) as year,
                MONTH(uh.game_date) as month,
                COUNT(*) as guess_count
            FROM userhistory uh
            JOIN UserSuccesses us 
                ON uh.user_id = us.user_id 
                AND uh.game_date = us.game_date
                AND uh.id <= us.first_success_id
            GROUP BY uh.user_id, uh.game_date, YEAR(uh.game_date), MONTH(uh.game_date)
            ORDER BY uh.user_id, uh.game_date
        """)

        print("Analyzing guess counts directly in SQL (much faster)...")
        results = session.execute(success_query, sample_user_ids).all()
        print(f"Found {len(results)} game results to analyze")

        # Process the aggregated data (already contains guess counts)
        results_by_month = {}
        for r in results:
            year_month = (r.year, r.month)
            if year_month not in results_by_month:
                results_by_month[year_month] = []
            results_by_month[year_month].append(r.guess_count)

        # Calculate average guesses per month
        data = []
        for (year, month), counts in sorted(results_by_month.items()):
            avg_guess_count = sum(counts) / len(counts) if counts else 0
            data.append(
                {
                    "year": year,
                    "month": month,
                    "avg_guess_count": avg_guess_count,
                    "samples": len(counts),
                }
            )

        df = pd.DataFrame(data)
        if df.empty:
            print("No data found for analysis.")
            return df

        # Create a date column for better plotting
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

        # Plot results
        plt.figure(figsize=(12, 6))
        plt.plot(df["date"], df["avg_guess_count"], marker="o")
        plt.title("Average Number of Guesses Until Success")
        plt.xlabel("Month")
        plt.ylabel("Average Guess Count")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("guess_count_trend.png")

        # Statistical analysis
        if len(df) > 1:
            correlation = df["date"].astype(int).corr(df["avg_guess_count"])
            print(
                f"Correlation between time and average guess count: {correlation:.4f}"
            )
            if correlation < -0.3:
                print(
                    "Players appear to be improving (taking fewer guesses to succeed)."
                )
            elif correlation > 0.3:
                print(
                    "Players appear to be performing worse (taking more guesses to succeed)."
                )
            else:
                print("No clear trend in number of guesses until success over time.")

        return df


if __name__ == "__main__":
    # Focus on a representative sample of active users in the last year
    results = analyze_guess_counts(
        sample_size=300,
        min_games=5,
        recent_months=3,
    )
    print(results)
