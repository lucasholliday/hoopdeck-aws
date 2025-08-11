import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import urllib.parse
import string
import random

from configparser import ConfigParser

def lambda_handler(event, context):
    try: 
        print("**STARTING**")
        print("**lambda: hoopdeck_stats**")

        params = event["pathParameters"]
        team = str(params["team"])
        year = str(params["year"])
        decoded_team = urllib.parse.unquote(team)

        bypass = False
        if decoded_team.endswith("_exact"):
            bypass = True
            decoded_team = decoded_team[:-6]  # Remove trailing '>'


        config_file = 'hoopdeck-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        configur = ConfigParser()
        configur.read(config_file)

        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd = configur.get('rds', 'user_pwd')
        rds_dbname = configur.get('rds', 'db_name')

        print("**Opening DB connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

        ############
        # sql = "SELECT team_name FROM teams"
        # row = datatier.retrieve_all_rows(dbConn, sql, [])
        # team_list = []
        # for i in row:
        #     team_list.append(i[0])
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps(team_list)
        # }
        ############

        if year == "2025":
            table = "teams"
        else:
            table = "teams" + year


        if bypass:
            sql = "SELECT * FROM teams WHERE team_name = %s;"
            row = datatier.retrieve_one_row(dbConn, sql, [decoded_team])
            if row is None:
                return {
                'statusCode': 400,
                'body': json.dumps("No team found...")
            }
        else:    
            sql = "SELECT * FROM teams WHERE team_name LIKE %s;"
            row = datatier.retrieve_all_rows(dbConn, sql, [f"%{decoded_team}%"])
            if len(row) > 1:
                if len(row) == 2:
                    team1 = row[0][2]
                    team2 = row[1][2]
                    message = f"Multiple teams match your search. Did you mean {team1} or {team2}?"
                elif len(row) == 3:
                    team1 = row[0][2]
                    team2 = row[1][2]
                    team3 = row[2][2]
                    message = f"Multiple teams match your search. Did you mean {team1}, {team2}, or {team3}?"
                else:
                    #random 3 teams?
                    random_indices = random.sample(range(len(row)), 3)
                    rand1, rand2, rand3 = random_indices
                    team1 = row[rand1][2]
                    team2 = row[rand2][2]
                    team3 = row[rand3][2]
                    num = len(row) - 3
                    message = f"Multiple teams match your search. Did you mean {team1}, {team2}, {team3}, or one of {num} other teams?"
                return {
                    'statusCode': 400,
                    'body': json.dumps(message)
                }
            elif len(row) == 1:
                row = row[0]
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps("No team found...")
                }

        # example cell: ['364', 'Mississippi Valley State', '31', '39.9', '54.1', '19.7', '50.6', '.389', '4.5', '15.3', '.296', '10.3', '15.5', '.660', '6.9', '19.0', '25.9', '8.3', '6.0', '1.9', '15.4', '16.4']
        # Team #, GP, MPG, PPG, FGM, FGA, FG%, 3PM, 3PA, 3P%, FTM, FTA, FT%, ORB, DRB, RPG, APG, SPG, BPG, TOV, PF
        team_stats = {
            'team_name': row[2],
            'GP': row[3],      # Games Played
            'MPG': row[4],     # Minutes Per Game'
            'PPG': row[5],    # Points Per Game
            'FGM': row[6],    # Field Goals Made
            'FGA': row[7],    # Field Goals Attempted
            'FG%': row[8],    # Field Goal Percentage
            '3PM': row[9],    # Three-Point Field Goals Made
            '3PA': row[10],   # Three-Point Field Goals Attempted
            '3P%': row[11],   # Three-Point Percentage
            'FTM': row[12],   # Free Throws Made
            'FTA': row[13],   # Free Throws Attempted
            'FT%': row[14],   # Free Throw Percentage
            'ORB': row[15],   # Offensive Rebounds
            'DRB': row[16],   # Defensive Rebounds
            'RPG': row[17],   # Rebounds Per Game
            'APG': row[18],   # Assists Per Game
            'SPG': row[19],   # Steals Per Game
            'BPG': row[20],   # Blocks Per Game
            'TOV': row[21],   # Turnovers Per Game
            'PF': row[22]     # Personal Fouls
        }

        return {
            'statusCode': 200,
            'body': json.dumps(team_stats)
        }
    except Exception as err:
        print(err)
        return {
            'statusCode': 500,
            'body': json.dumps(str(err))
        }

