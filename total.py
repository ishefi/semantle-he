import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sqlmodel import select

from common.session import get_session
from common.tables import SecretWord


def analyze_solver_counts(remove_outliers=True, iqr_factor=1.5):
    """
    Analyze solver counts for all secret words.
    Shows how many players solved each daily challenge.

    Args:
        remove_outliers: Whether to remove statistical outliers from the analysis
        iqr_factor: The IQR multiplier used to identify outliers (default: 1.5)
    """
    with get_session() as session:
        # Query all secret words with their solver counts
        query = select(
            SecretWord.word, SecretWord.game_date, SecretWord.solver_count
        ).order_by(SecretWord.game_date)

        print("Fetching all secret words and their solver counts...")
        results = session.exec(query).all()

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(
            [(r.word, r.game_date, r.solver_count) for r in results],
            columns=["word", "game_date", "solver_count"],
        )

        # Explicitly convert game_date to datetime type
        df["game_date"] = pd.to_datetime(df["game_date"])

        total_words = len(df)
        print(
            f"Analyzing {total_words} secret words from {df['game_date'].min()} to {df['game_date'].max()}"
        )

        if df.empty:
            print("No data found.")
            return df

        # Filter out words with 0 solvers (likely future words or data issues)
        zero_solvers = df[df["solver_count"] == 0]
        if not zero_solvers.empty:
            zero_count = len(zero_solvers)
            print(
                f"\nRemoved {zero_count} words with 0 solvers ({zero_count/total_words:.1%} of data)"
            )
            df = df[df["solver_count"] > 0]
            print(f"Continuing analysis with {len(df)} words")

        # Keep a copy of original data for comparison
        df_original = df.copy()

        # Remove outliers using IQR method if requested
        if remove_outliers:
            # Calculate IQR for solver_count
            Q1 = df["solver_count"].quantile(0.25)
            Q3 = df["solver_count"].quantile(0.75)
            IQR = Q3 - Q1

            # Define bounds for outliers
            lower_bound = Q1 - (iqr_factor * IQR)
            upper_bound = Q3 + (iqr_factor * IQR)

            # Identify outliers
            outliers = df[
                (df["solver_count"] < lower_bound) | (df["solver_count"] > upper_bound)
            ]

            # Filter data to remove outliers
            df = df[
                (df["solver_count"] >= lower_bound)
                & (df["solver_count"] <= upper_bound)
            ]

            # Report on outliers
            outlier_count = len(outliers)
            print(
                f"\nRemoved {outlier_count} outliers ({outlier_count/len(df_original):.1%} of non-zero data)"
            )
            print(
                f"Outlier threshold: <{lower_bound:.1f} or >{upper_bound:.1f} solvers"
            )

            if not outliers.empty:
                print("\nTop 5 High Outliers:")
                high_outliers = outliers[
                    outliers["solver_count"] > upper_bound
                ].sort_values("solver_count", ascending=False)
                if not high_outliers.empty:
                    print(high_outliers.head()[["word", "game_date", "solver_count"]])

                print("\nTop 5 Low Outliers:")
                low_outliers = outliers[
                    outliers["solver_count"] < lower_bound
                ].sort_values("solver_count")
                if not low_outliers.empty:
                    print(low_outliers.head()[["word", "game_date", "solver_count"]])

        # Calculate day of week for each game date before exporting
        df["day_of_week"] = df["game_date"].dt.day_name()

        # Export the filtered data to CSV
        csv_filename = "solver_counts_filtered.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\nExported filtered data to {csv_filename}")

        # Display basic statistics
        print("\nSolver Count Statistics (After filtering):")
        print(f"Average solvers per word: {df['solver_count'].mean():.1f}")
        print(f"Median solvers per word: {df['solver_count'].median():.1f}")
        print(
            f"Minimum solvers: {df['solver_count'].min()} (Word: {df.loc[df['solver_count'].idxmin(), 'word']})"
        )
        print(
            f"Maximum solvers: {df['solver_count'].max()} (Word: {df.loc[df['solver_count'].idxmax(), 'word']})"
        )

        # Create visualizations

        # 1. Time series plot of solver counts
        plt.figure(figsize=(15, 6))
        if remove_outliers:
            # Plot both original and cleaned data
            plt.plot(
                df_original["game_date"],
                df_original["solver_count"],
                "o",
                alpha=0.3,
                color="lightgray",
                label="Before outlier removal",
            )
        plt.plot(
            df["game_date"],
            df["solver_count"],
            marker="o",
            linestyle="-",
            alpha=0.7,
            label="Filtered data",
        )
        plt.title(
            "Number of Solvers per Secret Word Over Time"
            + (" (Outliers Removed)" if remove_outliers else "")
        )
        plt.xlabel("Game Date")
        plt.ylabel("Number of Solvers")
        plt.grid(True, alpha=0.3)

        # Add trend line
        z = np.polyfit(range(len(df)), df["solver_count"], 1)
        p = np.poly1d(z)
        plt.plot(
            df["game_date"],
            p(range(len(df))),
            "r--",
            alpha=0.8,
            label=f"Trend: {z[0]:.2f} solvers/day",
        )
        plt.legend()

        plt.tight_layout()
        plt.savefig("solver_count_trend.png")

        # 2. Histogram of solver counts
        plt.figure(figsize=(12, 6))
        plt.hist(
            df["solver_count"], bins=20, alpha=0.7, color="skyblue", edgecolor="black"
        )
        plt.title(
            "Distribution of Solver Counts"
            + (" (Outliers Removed)" if remove_outliers else "")
        )
        plt.xlabel("Number of Solvers")
        plt.ylabel("Frequency")
        plt.grid(True, alpha=0.3)
        plt.savefig("solver_count_distribution.png")

        # 3. Day of week analysis
        plt.figure(figsize=(12, 6))
        sns.boxplot(
            x="day_of_week",
            y="solver_count",
            data=df,
            order=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )
        plt.title(
            "Solver Count by Day of Week"
            + (" (Outliers Removed)" if remove_outliers else "")
        )
        plt.xlabel("Day of Week")
        plt.ylabel("Number of Solvers")
        plt.grid(True, alpha=0.3)
        plt.savefig("solver_count_by_day.png")

        # 4. Top 10 most difficult and easiest words (from clean data)
        print("\nTop 10 Most Difficult Words (Fewest Solvers):")
        print(
            df.sort_values("solver_count").head(10)[
                ["word", "game_date", "solver_count"]
            ]
        )

        print("\nTop 10 Easiest Words (Most Solvers):")
        print(
            df.sort_values("solver_count", ascending=False).head(10)[
                ["word", "game_date", "solver_count"]
            ]
        )

        # 5. Monthly averages
        df["year_month"] = df["game_date"].dt.to_period("M")
        monthly_avg = df.groupby("year_month")["solver_count"].mean().reset_index()
        monthly_avg["date"] = monthly_avg["year_month"].dt.to_timestamp()

        plt.figure(figsize=(15, 6))
        plt.plot(
            monthly_avg["date"], monthly_avg["solver_count"], marker="o", linestyle="-"
        )
        plt.title(
            "Average Monthly Solver Count"
            + (" (Outliers Removed)" if remove_outliers else "")
        )
        plt.xlabel("Month")
        plt.ylabel("Average Solvers")
        plt.grid(True, alpha=0.3)
        plt.savefig("monthly_avg_solvers.png")

        return df


if __name__ == "__main__":
    # Set remove_outliers=False if you want to keep all data points
    results = analyze_solver_counts(remove_outliers=True, iqr_factor=1.5)
    print(f"\nAnalysis complete. {len(results)} secret words analyzed after filtering.")
