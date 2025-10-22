# pull a branch to local
# first checkout the branch
git checkout origin/branchName
# pull the branch from remote to local
git pull origin branchName

# push a new local branch to remote
git push -n origin feature/branchName

# track a remote feature branch on local
git branch --track Feature_1379_New1 origin/Feature_1379_New1
# or use the below
git checkout --track origin/Feature_1379_New1

# get latest hash from git
git rev-parse HEAD | cut -c 1-8

# refresh branch list in clone from remote
git remote update origin --prune

# delete branch from local
git branch -d ETRNL_178_CoreLogic_Deploy_Assignment_Data_Vault_tables

# delete a remote branch
git push origin --delete feature/1413-CoreLogic---Initial-Data-Vault-Deploy-to-NON-PROD-and-PROD

# when you add a file to git using git add, then the file is moved to staging area
# you can get the hash value of files in staging area using below
git ls-files --stage

# after you change a file (before moving it to staging area), you can see the 
# hash value of that version of file using below
git hash-object <filename>

# REMOVE A FILE FROM GIT
# if a new file is added in a git repository but not staged yet
# then you can remove that file using below
rm <filename>

# if a new file is added in a git repository and staged using git add
# then you can remove the file using below
git rm --cached <filename>
# note that the above command will move the file from staging to
# untracked layer. So, the physical file will still exist in git repository

# if a new file is added in a git repository and staged and commited using git
 # then you can remove that file using below
git rm <filename>

# to restore a deleted remote git branch
# step 1: the below will give the sha value of the latest change done to the deleted branch
git fsck --full --no-reflogs --unreachable --lost-found | grep commit | cut -d\ -f3 | xargs -n 1 git log -n 1 --pretty=oneline

# step 2: using the sha value from above step, recreate a new branch
git branch <new branch name> <sha>


# to create a new feature branch in github
# go to github repository in github.com and create a new feature branch as "feature/your-feature-name"
# to update the local list of remote branches use the below:
git remote update origin --prune
# now you can see the new feature branch on your local

# checkout a branch from commit ID
git checkout -b <new_branch_name> 7d4c83d1

#see log of a branch between 2 dates
git log --since='Apr 1 2021' --until='Apr 4 2021'
#
# To update the new pass key, enter the below commaond on git bash
#
git config --global credential.helper store
#
# After than if you pull or push, git will prompt for user ID and password
# enter user ID as your libertymutual email ID
# and use the pass key as your password
#
#
# to change git editor to vim
git config --global core.editor "vim"
#
# to revert a commit in a branch
# checkout the branch that you want to modify
# using git log, find the hasv value to which you want to revert to
# then using below set of commands revert to previous commit
git checkout <hash value> .
git add .
git commit -m "Reverting to <hash value>"
git push
#decorate git log
git log --graph --decorate --oneline

# get list of git push from a particular branch
git reflog show feature/DAT-837-build-pipelines-for-data-vault

#delete branch locally
git branch -d localBranchName

#delete branch remotely
git push origin --delete remoteBranchName

#show difference between 2 branches
# step 1: checkout the branch that you want to compare
#step 2: 
git diff --name-only origin/main..HEAD

# create ssh key
# go to folder C:\Users\rajakrishnana\.ssh
# run the below command
ssh-keygen -t ed25519 -b 256

#the above command will create 2 files in .ssh folder
# copy the content of the *.pub file to github ssh key

# to revert git add, use below
git reset
#
# list all components that differ between 2 branches
# git checkout branch 1
# then run below to compare with main branch
git diff --name-status main

# get difference between a file in 2 branches
# go to branch A
# cd to the folder where the file is located
# use the below command
git diff <branch 2> -- CONTROL.ETL_APPLICATION.sql

# see older version of file in a branch
git show HEAD@{2025-01-08}:./cf_utils_v2.py

# see list of components that changed between
# two commits
git diff --name-only <commit1> <commit2>

# see history of all changes done to a file
gitk -- <filename>--name

# git merge dry run to check if the merge 
# has any conflict

git merge --no-commit --no-ff <branch to merge>

# after checking any conflict, abort the merge

git merge --abort
