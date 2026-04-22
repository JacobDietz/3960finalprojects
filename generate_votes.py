# ***IMPORTANT NOTE***
# I used AI to generate this fake data (I needed fake voting data for teams)


import sqlite3
import random

# add path
DB_PATH = "/Users/jacobdietz/Documents/school/3960/project/nba_career_stats.db"

NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
    "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
    "Utah Jazz", "Washington Wizards"
]

PICKS_PER_TEAM = 5
RANDOM_SEED = 42

# Stat columns each team can weight differently
STAT_COLS = ["PTS", "AST", "REB", "STL", "BLK", "FG_PCT", "FT_PCT"]

def compute_team_score(player, weights):
    """Weighted sum of stats for a player row (dict), given a weight dict."""
    return sum(weights.get(col, 0) * (player[col] or 0) for col in STAT_COLS)

def main():
    random.seed(RANDOM_SEED)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Deduplicate players, keep best row per name
    cur.execute("""
        SELECT FULL_NAME, MAX(PTS) as PTS, MAX(AST) as AST, MAX(REB) as REB,
               MAX(STL) as STL, MAX(BLK) as BLK, MAX(FG_PCT) as FG_PCT,
               MAX(FT_PCT) as FT_PCT
        FROM player_career_stats
        GROUP BY FULL_NAME
    """)
    players = [dict(row) for row in cur.fetchall()]
    print(f"Unique players: {len(players)}")

    # Drop and recreate teams table
    cur.execute("DROP TABLE IF EXISTS teams")
    cur.execute("CREATE TABLE teams (team_name TEXT PRIMARY KEY)")
    cur.executemany("INSERT INTO teams VALUES (?)", [(t,) for t in NBA_TEAMS])

    # Drop and recreate votes table
    cur.execute("DROP TABLE IF EXISTS votes")
    cur.execute("""
        CREATE TABLE votes (
            team_name TEXT,
            player_full_name TEXT,
            FOREIGN KEY (team_name) REFERENCES teams(team_name),
            FOREIGN KEY (player_full_name) REFERENCES player_career_stats(FULL_NAME)
        )
    """)

    vote_rows = []

    for team in NBA_TEAMS:
        # Each team gets a random stat preference profile
        weights = {col: random.uniform(0, 1) for col in STAT_COLS}

        # Score every player and pick top 5
        scored = sorted(players, key=lambda p: compute_team_score(p, weights), reverse=True)
        top5 = scored[:PICKS_PER_TEAM]

        for player in top5:
            vote_rows.append((team, player["FULL_NAME"]))

    cur.executemany("INSERT INTO votes VALUES (?, ?)", vote_rows)
    conn.commit()

    print(f"Total votes inserted: {len(vote_rows)}")

    # Show sample rosters
    print("\nSample rosters:")
    for team in NBA_TEAMS[:5]:
        cur.execute("SELECT player_full_name FROM votes WHERE team_name = ?", (team,))
        picks = [r[0] for r in cur.fetchall()]
        print(f"  {team}: {picks}")

    # Show how many teams approved the most popular players
    print("\nMost approved players:")
    cur.execute("""
        SELECT player_full_name, COUNT(*) as approvals
        FROM votes
        GROUP BY player_full_name
        ORDER BY approvals DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: approved by {row[1]} teams")

    conn.close()
    print("\nDone. Tables 'teams' and 'votes' created successfully.")

if __name__ == "__main__":
    main()
