#!/bin/bash

# Script to setup the new repository remote
# Usage: ./setup-new-repo.sh <new-repository-url>

if [ -z "$1" ]; then
    echo "Usage: ./setup-new-repo.sh <new-repository-url>"
    echo "Example: ./setup-new-repo.sh https://github.com/yourusername/your-repo.git"
    exit 1
fi

NEW_REPO_URL=$1

echo "Setting up new repository remote..."
git remote add origin "$NEW_REPO_URL"

echo "Verifying remote setup..."
git remote -v

echo ""
echo "✅ Repository remote configured successfully!"
echo ""
echo "Next steps:"
echo "1. Make sure your new repository exists on GitHub/GitLab/etc."
echo "2. Push your code: git push -u origin main"
echo "3. Update documentation with the new repository URL"

