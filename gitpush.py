import sys
import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    if len(sys.argv) < 2:
        print("Usage: python gitpush.py \"commit message\"")
        return

    commit_message = sys.argv[1]
    
    # Add all files
    success, output = run_command("git add .")
    if success:
        print("[OK] successfully added files")
    else:
        print("[ERROR] failed to add files:")
        print(output.strip())
        return

    # Commit changes - use double quotes for Windows compatibility
    commit_cmd = 'git commit -m "\\"{}\\""'.format(commit_message)
    success, output = run_command(commit_cmd)
    if success:
        print("[OK] successfully commited")
    else:
        print("[ERROR] failed to commit. Git output:")
        print(output.strip() or "No output from git")
        return

    # Push changes
    success, output = run_command("git push")
    if success:
        print("[OK] success. commit info:", output.strip())
    else:
        print("[ERROR] failed to push. Git output:")
        print(output.strip())

if __name__ == "__main__":
    main()
