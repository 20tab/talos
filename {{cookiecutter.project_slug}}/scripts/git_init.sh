#!/bin/bash

git init
git add .
git commit -m'First commit'
git remote add origin $1
git push -u origin master -o ci.skip
git checkout -b develop
git push -u origin develop -o ci.skip
