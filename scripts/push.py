import os, subprocess

env_path = r"D:\用户文件\家政AI自动化系统\.env"
token = ""
with open(env_path, encoding="utf-8") as f:
    for line in f:
        if line.startswith("GITHUB_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break

url = f"https://d87673:{token}@github.com/d87673/zhijiaguanjia-ai.git"
repo = r"D:\用户文件\家政AI自动化系统"

subprocess.run(["git", "-C", repo, "remote", "set-url", "origin", url])
r = subprocess.run(["git", "-C", repo, "push", "-u", "origin", "main"], capture_output=True, text=True)
print(r.stdout)
print(r.stderr)
print("Exit:", r.returncode)
