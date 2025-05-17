# for default user
aws s3 ls

# for test user
aws s3 ls --profile test

#ls on a specific bucket
aws s3 ls xxxx-das-staging-test/ --profile test

#copy a file from local to s3 bucket

aws s3 cp C:\Documents\dataFiles\VNS_CBH_CMGC_DATA_EXTRACTS_CDC1_2021-07-06.zip s3://xxxx-das-staging-test/ --profile test

#delete a file from s3 bucket

aws s3api delete-object --bucket xxxx-das-staging-test --key tmg_claims_diagnosis.csv --profile test

#check size of s3 bucket

aws s3 ls s3://xxxx-das-staging-test --recursive --human-readable --summarize --profile test

# configure aws cli on laptop

aws configure sso

# Get list of all ec2 instances in table format

aws ec2 describe-instances --filters Name=tag-key,Values=Name --query "Reservations[*].Instances[*].{Instance:InstanceId,State:State.Name,Name:Tags[?Key=='Name']|[0].Value}" --output table --region "ca-central-1"

# login to an ec2 instance
aws ssm start-session --target i-xxxxxxxxxxxxxxxx --region "ca-central-1"

# Access aws secret
# parameters:
#    secret-id : name of aws secret
#    query : name of the attribute from aws secret. usually it will be SecretString
#    jq -r : within single quote use dot operator to access each key in the json
aws secretsmanager get-secret-value --secret-id secretName --query SecretString --output text | jq -r '.passphrase'
