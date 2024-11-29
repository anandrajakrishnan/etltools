#Create the Snowflake Secret to store the AWS user ID and password
USE DATABASE DB_NAME
;
USE SCHEMA SCHEMA_NAME
;
CREATE OR REPLACE SECRET AWS_KEY_EC2
    TYPE = password
    USERNAME = 'xxxxxxxxxxxxxxxxxxxx'
    PASSWORD = 'ppppppppppppppppppppp'
;

#Create the Snowflake NETWORK RULE
CREATE OR REPLACE NETWORK RULE NETWORK_RULE_NAME
MODE = EGRESS
TYPE = HOST_PORT
VALUE_LIST = ('api.xxx.xxxxxx.com','sts.xxxxxxxx.com','secretsmanager.ca-central-1.amazonaws.com')
;

# Create External Access Integration using ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION INTEGRATION_NAME
ALLOWED_NETWORK_RULES = (NETWORK_NAME)
ALLOWED_AUTHENTICATION_SECRETS = (AWS_KEY_EC2)
ENABLED = true
;

# Run below Grants using ACCOUNTADMIN
GRANT USAGE ON SECRET AWS_KEY_EC2 TO ROLE ROLE_NAME;
GRANT USAGE ON INTEGRATION INTEGRATION_NAME TO ROLE ROLE_NAME;

#Use the ROLE_NAME to define the procedure where you want to access AWS Secret
USE ROLE DT_ADMIN_PROD
;
CREATE OR REPLACE PROCEDURE DB_NAME.STAGE_NAME.PROCEDURE_NAME("BATCH_ID" NUMBER(38,0))
RETURNS VARCHAR(16777216)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('pyyaml==6.0.1','requests==2.31.0','snowflake-snowpark-python==*','boto3','snowflake')
HANDLER = 'main'
EXTERNAL_ACCESS_INTEGRATIONS = (INTEGRATION_NAME)
SECRETS = ('aws_key_ec2' = AWS_KEY_EC2)
EXECUTE AS OWNER
AS
$$
#
import snowflake.snowpark as snowpark
import _snowflake
import boto3
import yaml
import time
import requests
import json
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

#
def get_aws_credentials():
    aws_key_object = _snowflake.get_username_password('aws_key_ec2')
    region = 'ca-central-1'
    boto3_session_args = {
        'aws_access_key_id': aws_key_object.username,
        'aws_secret_access_key': aws_key_object.password,
        'region_name': region
    }

    return boto3_session_args, region
def main(session: snowpark.Session, batch_id):
    boto3_session_args, region = get_aws_credentials()
    boto3_session = boto3.Session(**boto3_session_args)
    #boto3_session = boto3.session.Session()
    sts_client = boto3_session.client('sts')
    assumed_role_object=sts_client.assume_role(
    RoleArn="arn:aws:iam::22222222222:role/snowflakeRole",
    RoleSessionName="RoleNonProd"
    )
    credentials=assumed_role_object['Credentials']
    secret_client=boto3.client('secretsmanager', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'], region_name='ca-central-1')
    get_secret_value_response = secret_client.get_secret_value(SecretId='AWSsecretName')['SecretString']
