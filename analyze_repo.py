import subprocess
import tempfile
import shutil
import os
import stat
from datetime import datetime, timedelta
from collections import Counter

def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def run_git_command(args, cwd):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, text=True, check=True)
    return result.stdout.strip()

def analyze_repo(repo_url):
    print(f"[*] Cloning repository: {repo_url}")
    temp_dir = tempfile.mkdtemp()

    try:
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True, capture_output=True)
        raw_log = run_git_command(['git', 'log', '--format=%aI|%an'], cwd=temp_dir)

        if not raw_log:
            return

        commits = []
        for line in raw_log.split('\n'):
            date_str, author = line.split('|', 1)
            dt = datetime.fromisoformat(date_str)
            commits.append({'date': dt, 'author': author})

        commits.sort(key=lambda x: x['date'])

        total_commits = len(commits)
        author_counts = Counter(c['author'] for c in commits)
        top_authors = author_counts.most_common(5)

        first_commit_date = commits[0]['date']
        last_commit_date = commits[-1]['date']
        total_days = (last_commit_date - first_commit_date).days
        avg_commits_per_day = total_commits / total_days if total_days > 0 else total_commits

        max_gap = timedelta(0)
        for i in range(1, total_commits):
            gap = commits[i]['date'] - commits[i-1]['date']
            if gap > max_gap:
                max_gap = gap

        one_year_ago = datetime.now(first_commit_date.tzinfo) - timedelta(days=365)
        recent_commits = [c for c in commits if c['date'] >= one_year_ago]
        month_counts = Counter(c['date'].strftime('%Y-%m') for c in recent_commits)

        print("\n==========================================")
        print("          REPOSITORY HEALTH REPORT        ")
        print("==========================================")
        print(f"Total Commits Evaluated: {total_commits}")
        print(f"Average Commits/Day:     {avg_commits_per_day:.2f}")
        print(f"Longest Commit Gap:      {max_gap.days} days")

        print("\n--- Top 5 Contributors ---")
        for author, count in top_authors:
            print(f"  {count:4d} commits | {author}")

        print("\n--- Activity Last 12 Months ---")
        for month in sorted(month_counts.keys()):
            print(f"  {month}: {month_counts[month]} commits")

    finally:
        print("\n[*] Cleaning up temporary files...")
        shutil.rmtree(temp_dir, onerror=remove_readonly)

if __name__ == "__main__":
    target_repo = "https://github.com/torvalds/pesconvert.git"
    analyze_repo(target_repo)
