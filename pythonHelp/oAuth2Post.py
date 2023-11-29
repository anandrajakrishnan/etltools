import requests
import json
#
client_id='XXXXXXXX'
client_secret='XXXXXXX'
token_req_payload = {'grant_type': 'client_credentials'}
#
token_response=requests.post(auth_url,data=token_req_payload,auth=(client_id,client_secret))
if token_response.status_code==200:
    print('Successful!!')
    token=json.loads(token_response.text)
    print(token)
