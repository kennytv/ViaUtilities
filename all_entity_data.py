import subprocess
import entity_data


def get_commit_list() -> list:
    # Get all commit hashes and titles from oldest to newest
    result = subprocess.run(
        ['git', 'log', '--reverse', '--pretty=format:%H %s'],
        stdout=subprocess.PIPE,
        text=True
    )

    # Parse each commit into (hash, title)
    commits = result.stdout.splitlines()
    commit_list = [(line.split(' ', 1)[0], line.split(' ', 1)[1]) for line in commits]

    return commit_list


def main():
    # Go through all release commits in reverse
    commits = get_commit_list()
    last_content: str = ""
    for commit_hash, commit_title in commits:
        if 'w' in commit_title or '-' in commit_title:
            # Skip snapshots
            continue

        subprocess.run(['git', 'checkout', commit_hash])
        last_content = entity_data.main(commit_title, last_content)


if __name__ == "__main__":
    main()
