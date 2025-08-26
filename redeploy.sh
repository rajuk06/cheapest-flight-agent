#!/usr/bin/env bash
set -e

cd ~/cheapest-flight-agent

# Make a dummy change to trigger Vercel build
echo "# Trigger $(date)" > .vercel-redeploy

git add .vercel-redeploy
git commit -m "Trigger redeploy at $(date)" || echo "No changes to commit"

git push
