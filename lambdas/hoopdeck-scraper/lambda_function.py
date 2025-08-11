# Authors: Lucas Holliday, Sid Javeri, Helena Yuan
#
#
# Scrapes team statistics from “Real GM” using a BeautifulSoup layer 
# and stores these statistics in an RDS database from config file. 
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import urllib.parse
import string

from configparser import ConfigParser
from pypdf import PdfReader

import requests
from bs4 import BeautifulSoup



def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: hoopdeck_scraper**")

        config_file = 'hoopdeck-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        configur = ConfigParser()
        configur.read(config_file)

        s3_profile = 's3readwrite'
        boto3.setup_default_session(profile_name=s3_profile)
        bucketname = configur.get('s3', 'bucket_name')
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucketname)


        ## SCRAPE LOGOS FROM WEBPAGE

        print("**Accessing webpage**")

        url = "https://basketball.realgm.com/ncaa/team-stats"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"class": "tablesaw"})

        if not table:
            raise ValueError("Stats table not found on the page!")
        print("YES TABLE EXISTS")

        headers = [th.text.strip() for th in table.find("thead").find_all("th")]

        print("**Opening DB connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
        createTableSQL = """
        CREATE TABLE IF NOT EXISTS teams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            team_rank INT,
            team_name VARCHAR(255),
            games_played INT,
            minutes_per_game FLOAT,
            points_per_game FLOAT,
            field_goals_made FLOAT,
            field_goals_attempted FLOAT,
            field_goal_percentage FLOAT,
            three_pointers_made FLOAT,
            three_pointers_attempted FLOAT,
            three_point_percentage FLOAT,
            free_throws_made FLOAT,
            free_throws_attempted FLOAT,
            free_throw_percentage FLOAT,
            offensive_rebounds FLOAT,
            defensive_rebounds FLOAT,
            rebounds_per_game FLOAT,
            assists_per_game FLOAT,
            steals_per_game FLOAT,
            blocks_per_game FLOAT,
            turnovers FLOAT,
            personal_fouls FLOAT
        )
        """
        datatier.perform_action(dbConn, createTableSQL, [])

        insertSQL = """
        INSERT INTO teams (team_rank, team_name, games_played, minutes_per_game, points_per_game, 
                           field_goals_made, field_goals_attempted, field_goal_percentage, 
                           three_pointers_made, three_pointers_attempted, three_point_percentage,
                           free_throws_made, free_throws_attempted, free_throw_percentage,
                           offensive_rebounds, defensive_rebounds, rebounds_per_game, 
                           assists_per_game, steals_per_game, blocks_per_game, turnovers, personal_fouls) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data = []
        for row in table.find("tbody").find_all("tr"):
            cells = [td.text.strip() for td in row.find_all("td")]
            # example cell: ['364', 'Mississippi Valley State', '31', '39.9', '54.1', '19.7', '50.6', '.389', '4.5', '15.3', '.296', '10.3', '15.5', '.660', '6.9', '19.0', '25.9', '8.3', '6.0', '1.9', '15.4', '16.4']
            # Team #, GP, MPG, PPG, FGM, FGA, FG%, 3PM, 3PA, 3P%, FTM, FTA, FT%, ORB, DRB, RPG, APG, SPG, BPG, TOV, PF
            data.append(cells)

            if len(cells) != 22:  # Ensure correct number of columns
                print(f"⚠️ Skipping row due to incorrect column count: {cells}")
                continue

            datatier.perform_action(dbConn, insertSQL, cells)
            
        print("✅ Data successfully inserted into RDS!")
        return {
            'statusCode': 200,
            'body': json.dumps('Data successfully scraped and inserted into RDS!')
        }
    except Exception as err:
        print("**ERROR SCRAPING**")
        print(str(err))

