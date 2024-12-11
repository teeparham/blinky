#!python3

import argparse
import subprocess
from datetime import datetime, timedelta

def get_git_log(since_date: str) -> list[str]:
    """Get the git log since a date."""
    try:
        log_output = subprocess.check_output(
            ["git", "log", f"--since={since_date}", "--pretty=format:%H%x09%s"],
            text=True
        ).strip()
        return [line.split("\t", 1) for line in log_output.split("\n") if line] if log_output else []
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving git log: {e}")
        return []

def get_commit_diff_stats(commit_hash: str) -> tuple[int, int]:
    """Get the diff stats for a given commit hash."""
    try:
        diff_stat = subprocess.check_output(
            ["git", "show", "--stat", commit_hash],
            text=True
        )
        added = sum(int(x.split()[0]) for x in diff_stat.splitlines() if "insertions(" in x)
        deleted = sum(int(x.split()[0]) for x in diff_stat.splitlines() if "deletions(" in x)
        return added, deleted
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error retrieving diff stats for commit {commit_hash[:8]}: {e}")
        return 0, 0

def find_commits(since_date: str, min_lines: int, min_pct: int) -> None:
    """Find and print red commits."""
    commits = get_git_log(since_date)
    for commit_hash, commit_subject in commits:
        if commit_subject.startswith("Merge branch"):
            continue
        
        added, deleted = get_commit_diff_stats(commit_hash)
        total_lines = added + deleted
        if total_lines >= min_lines:
            percent_deleted = (deleted / total_lines) * 100 if total_lines > 0 else 0
            if percent_deleted >= min_pct:
                commit_author = subprocess.check_output(
                    ["git", "log", "-1", "--pretty=format:%an", commit_hash],
                    text=True
                ).strip()
                add_str = f"+{added}"
                del_str = f"-{deleted}"
                print(
                    f"{commit_hash[:8]} | "
                    f"{add_str:>5}, {del_str:>6} | "
                    f"{percent_deleted:>3.0f}% | "                    
                    f"{commit_author}"
                )

def main() -> None: 
    parser = argparse.ArgumentParser(description="Find red git commits")

    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    parser.add_argument(
        "--since",
        type=str,
        default=thirty_days_ago,
        help="Start date for filtering commits (format: YYYY-MM-DD). Default is 1 month ago."
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=10,
        help="Minimum number of lines deleted. Default is 10."
    )    
    parser.add_argument(
        "--min-pct",
        type=int,
        default=95,
        help="Minimum percentage of lines deleted. Default is 95."
    )    
    args = parser.parse_args()

    print(f"Searching for commits since {args.since}...")
    find_commits(args.since, args.min_lines, args.min_pct)

if __name__ == "__main__":
    main()
