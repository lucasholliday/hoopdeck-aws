import json
import boto3
import os
import pandas as pd

# import uuid
# import base64
# import pathlib
# import urllib.parse
# import string
# import random

from configparser import ConfigParser

import requests

def lambda_handler(event, context):
    try:
        params = event["pathParameters"]
        teamA = str(params["teamA"])
        teamB = str(params["teamB"])
        year = params["year"]
        print("NEW")

        print(f"Hello from Lambda! {teamA} {teamB} {year}")

        config_file = 'hoopdeck-model-config.ini'
        configur = ConfigParser()
        configur.read(config_file)
        baseurl = configur.get('client', 'webservice')
        endpoint = configur.get('SageMaker', 'endpoint')
  
        print("read config file")

        # TEAM A
        api = '/stats'
        params = f'/{teamA}_exact/{year}'
        url = baseurl + api + params
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception("Error getting team A stats")
        bodyA = res.json()
        # example {"team_name": "Northwestern", "PPG": 72.4, "FGM": 26.1, "FGA": 59.1, "FG%": 0.441, "3PM": 6.7, "3PA": 20.2, "3P%": 0.333, "FTM": 13.6, "FTA": 18.5, "FT%": 0.733, "ORB": 9.7, "DRB": 21.9, "RPG": 31.6, "APG": 14.5, "SPG": 6.9, "BPG": 3.5, "TOV": 9.5, "PF": 17.6}
        print("team stats A recieved")

        # TEAM B
        api = '/stats'
        params = f'/{teamB}_exact/{year}'
        url = baseurl + api + params
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception("Error getting team B stats")
        bodyB = res.json()
        # example {"team_name": "Duke", "PPG": 83.3, "FGM": 29.1, "FGA": 59.5, "FG%": 0.489, "3PM": 10.3, "3PA": 27.0, "3P%": 0.381, "FTM": 14.8, "FTA": 18.7, "FT%": 0.788, "ORB": 10.6, "DRB": 26.9, "RPG": 37.5, "APG": 17.1, "SPG": 6.9, "BPG": 3.8, "TOV": 9.3, "PF": 15.9}
        print("team stats B recieved")

        features = [key for key in bodyA.keys() if key != "team_name"]
        features = [key for key in bodyA.keys()]
        dataA = [bodyA[feature] for feature in features]
        dataB = [bodyB[feature] for feature in features]
        totalData = [0] + dataA + dataB + ["winner"]
        
        

        test = pd.DataFrame([dataA + dataB])
        print("printing test")
        print(test)
        print("done printing test")

        print("formatting features data")
        client = boto3.client("runtime.sagemaker")
        body = pd.DataFrame(
            [totalData,
            [1, "teamA", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "teamB", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "winner"]] 
        ).to_csv(header=False, index=False).encode("utf-8")
        # body = pd.DataFrame(
        #     [dataA + dataB] 
        # ).to_csv(header=False, index=False).encode("utf-8")
    
        print("getting prediction")
        response = client.invoke_endpoint(
            EndpointName=endpoint,
            ContentType="text/csv",
            Body=body,
            Accept="application/json"
        )
        print("printing response")
        print(response)

        response_body = response['Body'].read().decode('utf-8')  # Read and decode the body to a string

        # Now parse the string into a JSON object
        prediction = json.loads(response_body)

        margin = prediction["predictions"][0]["score"]

        # Print the prediction or inspect it
        print("Prediction result:", prediction)

        return {
            'statusCode': 200,
            'body': margin
        }
    except Exception as err:
        print(err)
        return {
            'statusCode': 500,
            'body': json.dumps(str(err))
        }