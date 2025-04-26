import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    # Pull changes
    success, output = run_command("git pull")
    if success:
        print("[OK] successfully pulled changes")
        print(output.strip())
    else:
        print("[ERROR] failed to pull. Git output:")
        print(output.strip())

if __name__ == "__main__":
    main()
