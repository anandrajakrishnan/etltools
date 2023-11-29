import requests
import json
#
api_url='www.abcdefghijklmno.pqr'
token='take from oAuthPost.py'
api_call_headers = {'Authorization': 'Bearer ' + token}
#
api_call_response=requests.get(api_url,headers=api_call_headers)
#
if api_call_response.status_code==200:
    print('Successful!!')
    payload=json.loads(api_call_response.text)
  print(payload)
#
