import os
import subprocess

def get_changed_files():
    """Get the list of changed files in the working directory."""
    result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    return [file for file in files if file]

def get_added_files():
    """Get the list of added files in the working directory."""
    result = subprocess.run(['git', 'diff', '--name-only', '--cached'], capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    return [file for file in files if file]

def get_untracked_files():
    """Get the list of untracked files in the working directory."""
    result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    return [file for file in files if file]

def group_files_by_subdirectory(files):
    """Group the changed, added, and untracked files by their subdirectories."""
    file_groups = {}

    for file in files:
        # Split the path into directories
        dirs = file.split(os.sep)

        if len(dirs) > 1:
            # Create a subdirectory path (excluding the file name)
            sub_dir_path = os.sep.join(dirs[:-1])
            if sub_dir_path not in file_groups:
                file_groups[sub_dir_path] = []
            file_groups[sub_dir_path].append(file)
        else:
            # Handle files at the root level
            if 'root' not in file_groups:
                file_groups['root'] = []
            file_groups['root'].append(file)

    return file_groups

def create_commits(file_groups):
    """Stage files and create separate commits for each subdirectory."""
    for sub_dir, files in file_groups.items():
        # Stage the files for the commit
        for file in files:
            subprocess.run(['git', 'add', file])

        # Create a commit message with the desired format
        # Split the sub_dir into its components
        sub_dir_components = sub_dir.split(os.sep)
        commit_title = ": ".join(sub_dir_components) + ": Import Xiaomi changes"

        # Commit the changes
        subprocess.run(['git', 'commit', '-m', commit_title, '-s'])

def main():
    # Step 1: Get the list of changed, added, and untracked files
    changed_files = get_changed_files()
    added_files = get_added_files()
    untracked_files = get_untracked_files()

    # Combine changed, added, and untracked files
    all_files = changed_files + added_files + untracked_files

    if not all_files:
        print("No changes detected.")
        return

    # Step 2: Group files by their subdirectories
    file_groups = group_files_by_subdirectory(all_files)

    # Step 3: Create commits for each group of files
    create_commits(file_groups)

if __name__ == "__main__":
    main()
