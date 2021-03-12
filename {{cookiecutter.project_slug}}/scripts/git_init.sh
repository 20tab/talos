#!/usr/bin/env bash

# Bash "strict mode", to help catch problems and bugs in the shell script
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

git init
git add .
git commit -m'Initial commit'
git remote add origin $1
git push -u origin master -o ci.skip
git checkout -b develop
git push -u origin develop -o ci.skip
