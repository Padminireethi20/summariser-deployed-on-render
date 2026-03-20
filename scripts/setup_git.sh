#!/bin/bash
# Run this from inside the pdf-summarizer directory
# Usage: bash scripts/setup_git.sh YOUR_GITHUB_USERNAME

set -e

USERNAME=${1:-"YOUR_GITHUB_USERNAME"}
REPO="pdf-summarizer"

echo "🔧 Initializing git repo..."
git init
git add .
git commit -m "Initial commit: PDF summarizer with T5-small, FastAPI, PostgreSQL"

echo ""
echo "✅ Local git repo ready."
echo ""
echo "Next steps:"
echo "  1. Create a new repo on GitHub: https://github.com/new"
echo "     Name it: $REPO"
echo "     Keep it public or private (your choice)"
echo "     Do NOT add README or .gitignore (we already have them)"
echo ""
echo "  2. Then run:"
echo "     git remote add origin https://github.com/$USERNAME/$REPO.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "  3. Then follow the Render deploy steps in README.md"
