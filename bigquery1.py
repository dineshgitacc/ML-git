import json
import pandas as pd
import requests
import logging
import datetime
import google.auth.crypt
import google.auth.jwt
from google.oauth2 import service_account

logging.basicConfig(level=logging.DEBUG)


# def create_jwt(service_account_info):
#     payload={
#         "iss": service_account_info["client_email"],
#         "scope": "https://www.googleapis.com/auth/bigquery",
#         "aud":"https://oauth2.googleapis.com/token",
#         "iat":datetime.now(),
#         "exp":datetime.now()+3600
#     }

from google.cloud import bigquery
from google.auth.transport.requests import Request

# Set the path to your service account key file
# service_account_key = "arlo-opexwise-5b13f58b35dc.json"
# a="data.json"
service_account_key={
  
  "project_id": "arlo-opexwise",
  "private_key_id": "5b13f58b35dc859437377e357ac937aae",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCs56w3XHRCY+qx\nIvEXsoNvr5tZ5kZq456FsLBibcBSfuKOMC2cBRyWaQPyasZXW51d5j9ihoU3NGfY\nbpVyQ9qfOXCZNRrxQ5gboRw1ViM91g+wqPgyujA0YuidAxnxBQDtBcHzT2uFfzwx\nAWlnuNJ8Wu41YvxfJEz6rulRsKKpCEUI2kgknLeiqC4NyxKvcc0fvS195i/D1sH5\nueDECL4/WJaWChuhYXCCM6uMjhbFKBN2aeYkKKCf+bodJlLdEfGB4BBkHa+nBL3L\nM2MwnERM4n7SxFQDWaBDxvGKqy5emC+0/ou7M57//xMXsHEEZEJnX5UNaMPF1qjN\nS4cC6f2zAgMBAAECggEADWdeTeJgbt8hC/9Z8kzX7JoP8H2t+s5PdSy318GLVbnZ\nZU1t07j/uNdGQ44sdww2nFdjlYc5H4jz/e7Arh19frdst6vKvWZQjd/E+IuHat1D\n1R2cNA6D+yOpxbY+VhVdt4IpQWvoOW6eI2xpF+3Xf2VrLv9P8i41u39AviDz0yec\nzjJGE85c0bNhSTUh96kuNfgC/gPT/EuWlhIhVjjVvf/W/wVCtzuZuPqbnsE72Wu/\nF/SVbkULewLVeGFUmZ2t6/xzR740sudE1QCFJD6yfshEhc367Mu9To28UQSO7bZ0\nAQZvjBJglPEpoNQCyrRt1RNyx85ksO/TrJ7unSh6fQKBgQDctmlw8EYIIlVAA0Kz\nbsuuOahVaqCy3MjaeJVnCBnAHw919uamIVCnHFpCQITPZgXbtaA206ORQ+LDXmNY\n3EgCjUrBIRc7FpP3SfiUolAbMppZmu/fmCXIJaetUqZ8upmbQt9bGoWPlbs57VK7\n9ItGQERV/LB1trlabjA49Mc7ZwKBgQDIjIj2is8IYkHMYIZy0FMv8qRnTc6Ye/MH\nI/zszeN0mTB2XXgTMTD2UL6zRkyeO+g4OLqzLTlDQd8oxTivh/4vRK6+FQVf+ZQJ\nIVjunWwYTI55Asus8OaX1QGEupT1ptjtteXRmBeq0rVlUn5g2fiNOMDoFN5F4SJD\nimKeS3RH1QKBgEHhSPPnJGBFL0EeOAirJ6znlPF6FGGPOXzMxXutlVIdc1X4zrwD\n8bkP43knHP1zLIh6XEpBPe+cXdGHGQxrJCtu1UN0hySiBqSntcVX9aVIo33fm34Y\nQh7N7pDzvLI6WKNZgKYG8pr7TJlr12g3BGOBx2QLOvjIA+eUQFyf4+A9AoGBAIHg\nUUqotk8NouMCl89/DoB8uO+VufeSPd8f9Uo+Q9Fc67+b5Ik5UCYUQIvFORU4YrkW\nNAKZhP4DiMvUfVNf1MMzzZ6X6nUvIimPiRJurHRID/RaVSDYmd02OteEJbe4p7+6\nDu1fe+RKtOK7O9DpGEgMuxERgqjqlc/7rMYqw1FJAoGBAL/UcsSOChQidMvKTjNx\nLWwFWj2DirBVohwDhoYPEMae/SKwXraxYqN0J6dZ0oCg/3VCxIKmG+Ro7MqBzLny\ntVO1AArLkSU8Ur0Tz6KUcDIy3pv2UC5Gb9lmMnDtFs1wYiCvs4PqZOAjki+R1PB7\nnN7Plc65CWrW+u0St5EMnU4B\n-----END PRIVATE KEY-----\n",
  "client_email": "opexwise-bq@arlo-opexwise.iam.gserviceaccount.com",
  "client_id": "117071520550909845483",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/opexwise-bq%40arlo-opexwise.iam.gserviceaccount.com"
  
}

# print(service_account_key["private_key"])
z=json.dumps(service_account_key)
a=json.loads(z)
print(a)
b=a["private_key"].replace("\\n","\n")
print(b)


# a=json.dumps(service_account_key)

# Create a BigQuery client using the service account credentials
# credentials=service_account.Credentials.from_service_account_info(service_account_key,
                                        # scopes=["https://www.googleapis.com/auth/cloud-platform"],)
# client = bigquery.Client.from_service_account_json(a)
# client = bigquery.Client.from_service_account_info(service_account_key)
# # client=bigquery.Client.from_service_account_json(service_account_key)
# # service_account_info = client.get_service_account_email()

# # print(service_account_info)
# credentials=service_account.Credentials.from_service_account_file("/home/dineshanand/practice/data.json")
# client=bigquery.Client(credentials=credentials,project=credentials.project_id)



credentials=service_account.Credentials.from_service_account_info(a)



# If you want to disable SSL verification (not recommended for production)

            
client=bigquery.Client(credentials=credentials,project=credentials.project_id)
datasets = list(client.list_datasets(service_account_key["project_id"]))
for i in datasets:
      response = client._http.request(
        method='GET',
        url="https://bigquery.googleapis.com/bigquery/v2/projects/arlo-opexwise/datasets/opexwise",
        headers={'Content-Type': 'application/json'},
        verify=False
      )
   
      print(i.dataset_id)


# Now you can interact with BigQuery using the 'client' object
# project_id="arlo-opexwise"

# query="select * from arlo-opexwise.opexwise.test"

# query_job=client.query(query)
# # print("xxxx---------xxxxxxxx")
# result=query_job.result().to_dataframe()

# print(result)
# columns=result.columns.tolist() 
#                 # print(df.dtypes)
# converted_columns=[]
# for col in columns:
#       if " " in col:
#               x=col.replace(" ","_")
#               converted_columns.append(x)
#       else:
#               converted_columns.append(col)
# print("converted columns",converted_columns) 
# result.columns=converted_columns
# print(result) 


# a=result.to_dict(orient="records")
# print(a)
# # for i in result:
#     print(i)

# for i in result:
#     print(i)


# print(result)


# project_id="arlo-opexwise"

# datasets = list(client.list_datasets(project_id ))

# a=[]
# for i in datasets:
    
#     a.append(i.dataset_id)
# print(a)


# tables list

# dataset_id= "arlo-opexwise.opexwise"   

# dataset=client.get_dataset(dataset_id)
# print("xxxx dataset xxxx",dataset)   

# tables=client.list_tables(dataset)
# print("xxxxt able xxxx",dataset)  
# b=[]
# for i in tables:
#     print(b.append(i.table_id))


# df = pd.DataFrame(b, columns=['table_name'])   
# print(df) 

# df.insert(1, "api_category_name", df['table_name'], True)
# df.insert(2, "api_category_value", df['table_name'], True)
# df = df[['api_category_name', 'api_category_value']]
# df = df[df.api_category_name != '']
# print(df)
# response_data = {'api_details': df.to_dict(orient='records')}
# print(response_data)





# print({client.test_iam_permissions})
# print(client._connection)
# for dataset in datasets:
#     print(dataset.dataset_id)



