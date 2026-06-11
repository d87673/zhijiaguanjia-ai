#!/bin/bash
# Read token from .env
cd "$(dirname "$0")/.."
TOKEN=$(grep GITHUB_TOKEN .env | cut -d= -f2)
git remote set-url origin "https://d87673:${TOKEN}@github.com/d87673/zhijiaguanjia-ai.git"
git push -u origin main
