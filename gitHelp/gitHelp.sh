# pull a branch to local
# first checkout the branch
git checkout origin/branchName
# pull the branch from remote to local
git pull origin branchName

# push a new local branch to remote
git push -n origin feature/branchName

track a remote feature branch on local
git branch --track Feature_1379_New1 origin/Feature_1379_New1
# or use the below
git checkout --track origin/Feature_1379_New1

# get latest hash from git
git rev-parse HEAD | cut -c 1-8

# refresh branch list in clone from remote
git remote update origin --prune

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

