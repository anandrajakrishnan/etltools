# for default user
aws s3 ls

# for test user
aws s3 ls --profile test

#ls on a specific bucket
aws s3 ls vnsny-das-staging-test/ --profile test

#copy a file from local to s3 bucket

aws s3 cp C:\Documents\dataFiles\VNS_CBH_CMGC_DATA_EXTRACTS_CDC1_2021-07-06.zip s3://vnsny-das-staging-test/ --profile test

#delete a file from s3 bucket

aws s3api delete-object --bucket vnsny-das-staging-test --key tmg_claims_diagnosis.csv --profile test

#check size of s3 bucket

aws s3 ls s3://vnsny-das-staging-test --recursive --human-readable --summarize --profile test
