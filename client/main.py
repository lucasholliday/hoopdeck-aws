#
# Client-side python app for hoop deck app, which is calling
# a set of lambda functions in AWS through API Gateway.

#
# Authors:
#   Lucas Holliday, Sid Javeri, Helena Yuan
#
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#   CS 310
#

import requests
import jsons

import uuid
import pathlib
import logging
import sys
import os
import base64
import time
from datetime import datetime 
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from configparser import ConfigParser
from getpass import getpass

from io import BytesIO
from PIL import Image
import numpy as np

# ------------------------------------------------------------
# Helper function: get_image_from_url2

  # Fetches an image from the given URL, removes its white background,
  # and returns a transparent image.

  # Parameters
  # ----------
  # url : str
  #     The URL of the image to be processed.

  # Returns
  # -------
  #   Image:
  #   Processed image with a transparent background, or None if the request fails.
    
def get_image_from_url2(url):
    """Fetches an image, removes the white background, and returns a transparent image."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGBA")  # Ensure transparency

            # Convert image to numpy array
            data = np.array(img)
            red, green, blue, alpha = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]

            # Create mask where the background is white (or near white)
            white_mask = (red > 200) & (green > 200) & (blue > 200)

            # Set those pixels to transparent
            data[white_mask] = [0, 0, 0, 0]

            # Convert back to an image
            img = Image.fromarray(data, "RGBA")
            return img
        else:
            #print(f"Failed to load image: {url}")
            return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 204, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    

############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
      print()
      print(">> Enter a command:")
      print("   0 => end")
      print("   1 => find games")
      print("   2 => team stats")
      print("   3 => analyze stats")
      print("   4 => predict winner")
      print("   5 => stats legend")

      cmd = input()

      if cmd == "":
        cmd = -1
      elif not cmd.isnumeric():
        cmd = -1
      else:
        cmd = int(cmd)

      return cmd

  except Exception as e:
      print("**ERROR")
      print("**ERROR: invalid input")
      print("**ERROR")
      return -1

############################################################
#
# stats legend
#
#   Prints a legend explaining basketball statistics abbreviations.
#
def statsKey():
  print("")
  print("PPG: Points Per Game")
  print("FGM: Field Goals Made")
  print("FGA: Field Goals Attempted")
  print("FG%: Field Goal Percentage")
  print("3PM: Three-Point Field Goals Made")
  print("3PA: Three-Point Field Goals Attempted")
  print("3P%: Three-Point Percentage")
  print("FTM: Free Throws Made")
  print("FTA: Free Throws Attempted")
  print("FT%: Free Throw Percentage")
  print("ORB: Offensive Rebounds")
  print("DRB: Defensive Rebounds")
  print("RPG: Rebounds Per Game")
  print("APG: Assists Per Game")
  print("SPG: Steals Per Game")
  print("BPG: Blocks Per Game")
  print("TOV: Turnovers Per Game")
  print("PF: Personal Fouls")

############################################################
#
# ticketmaster
#
def ticketmaster(baseurl):
  """
  Prints out basketball games in the inputed city in the next _3_ weeks using ticketmaster API

  Parameters
  ----------
  baseurl: baseurl for hoop deck web service

  Returns
  -------
  nothing
  """

  try:
    print("")
    print("Enter a city>")
    city = input()

    # call the web service:
    api = '/events'
    params = f'/{city}'
    url = baseurl + api + params

    # res = requests.get(url)
    res = web_service_get(url)

    print("")
    print("Displaying Ticketmaster Games for the Next 3 Weeks")

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 204: #no games found
      print("")
      print("No games found...")
      return
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return

    body = res.json()

    for name, time, formatted_time, date, formatted_date, minPrice, maxPrice, gameUrl, venue, address in body:
      print(f"""
📅 {formatted_date}
🏀 **{name}**
🕒 Time: {formatted_time} local time
📍 Venue: {venue}
📌 Address: {address}
💰 Price Range: ${minPrice} - ${maxPrice}
🎟 TICKET HERE: {gameUrl}
""")
      
    return

  except Exception as e:
    logging.error("**ERROR: ticketmaster() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# stats
#
def stats(baseurl):
  """
  Prints out a team stats in the database

  Parameters
  ----------
  baseurl: baseurl for hoop deck web service

  Returns
  -------
  nothing
  """

  try:
    print("")

    yearUrl = "2025"

    while True:
      print("Enter a team>")
      team = input()

      if team == "cancel":
        print("canceling...")
        return
      

      # call the web service:
      api = '/stats'
      params = f'/{team}/{yearUrl}'
      url = baseurl + api + params

      # res = requests.get(url)
      res = web_service_get(url)

      year = "2024-2025"

      #
      # let's look at what we got back:
      #
      if res.status_code == 200: #success
        break
      elif res.status_code == 400: #no games found
        print("")
        print(res.json())
        if res.json() == "No team found...":
          print('[cancel] to quit team stats command')
        else:
          print("append _exact for a direct query (ex. Northwestern_exact)")

      else:
        # failed:
        print("**ERROR: failed with status code:", res.status_code)
        print("url: " + url)
        if res.status_code == 500:
          # we'll have an error message
          body = res.json()
          print("Error message:", body)
        return
      print()
    
    body = res.json()

    team_name = body["team_name"]
    ppg = body["PPG"]
    fgm = body["FGM"]
    fga = body["FGA"]
    fg_percent = body["FG%"]
    three_pm = body["3PM"]
    three_pa = body["3PA"]
    three_percent = body["3P%"]
    ftm = body["FTM"]
    fta = body["FTA"]
    ft_percent = body["FT%"]
    rpg = body["RPG"]
    apg = body["APG"]
    spg = body["SPG"]
    bpg = body["BPG"]
    tov = body["TOV"]
    pf = body["PF"]

    print("")
    print(f"Displaying {team_name} season averages for the {year} season")

    #print(f"\n**{team_name} Season Averages ({year})**")
    #print(f"\n{team_name} RECORD 17-15")
    print(f"""
📊 **Scoring:**
- PPG: {ppg}
- FG: {fgm}/{fga} ({fg_percent}%)
- 3P: {three_pm}/{three_pa} ({three_percent}%)
- FT: {ftm}/{fta} ({ft_percent}%)

🏀 **Rebounds & Assists:**
  - RPG: {rpg} | APG: {apg}

🛡️ **Defense & Ball Control:**
  - SPG: {spg} | BPG: {bpg}
  - TOV: {tov} | PF: {pf}
    """)

    return

  except Exception as e:
    logging.error("**ERROR: ticketmaster() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# graph
#
def graph(baseurl, teamImages):
  """
  Creates custom graphs analyzing march madness fields

  Parameters
  ----------
  baseurl: baseurl for hoop deck web service

  Returns
  -------
  file path of created graph
  """

  try:

    # load images
    #team_logos_2024 = {"Alabama" : "https://content.sportslogos.net/logos/30/597/thumbs/59771422018.gif", "Northwestern" : "https://content.sportslogos.net/logos/33/787/thumbs/78733582012.gif", "Duke" : "https://content.sportslogos.net/logos/31/663/thumbs/66395011978.gif", "Wisconsin" : "https://content.sportslogos.net/logos/35/914/thumbs/91436912017.gif"}
    team_logos_2024 = {
      "Purdue": "https://content.sportslogos.net/logos/33/809/thumbs/80966442012.gif",
      "Tennessee": "https://content.sportslogos.net/logos/34/861/thumbs/86166262015.gif",
      "Creighton": "https://content.sportslogos.net/logos/30/652/thumbs/65227962013.gif",
      "Kansas": "https://content.sportslogos.net/logos/32/718/thumbs/t96oee4doe8n2oxaft7f.gif",
      "Gonzaga": "https://content.sportslogos.net/logos/31/691/thumbs/69163362011.gif",
      "South Carolina": "https://content.sportslogos.net/logos/34/835/thumbs/83565612002.gif",
      "Texas": "https://content.sportslogos.net/logos/34/865/thumbs/86561462019.gif",
      "Utah State": "https://content.sportslogos.net/logos/35/893/thumbs/89352172019.gif",
      "TCU": "https://content.sportslogos.net/logos/34/868/thumbs/86837962013.gif",
      "Virginia": "https://content.sportslogos.net/logos/35/898/thumbs/89873152020.gif",
      "Oregon": "https://content.sportslogos.net/logos/33/797/thumbs/by8dfvb6j89hs5nrvlb1ibx5e.gif",
      "McNeese State": "https://content.sportslogos.net/logos/32/745/thumbs/74570442011.gif",
      "Samford": "https://content.sportslogos.net/logos/34/824/thumbs/82413822016.gif",
      "Akron": "https://content.sportslogos.net/logos/30/596/thumbs/59689742022.gif",
      "Saint Peter's": "https://content.sportslogos.net/logos/34/853/thumbs/85395302020.gif",
      "Montana State": "https://content.sportslogos.net/logos/32/760/thumbs/76067842013.gif",
      "Alabama": "https://content.sportslogos.net/logos/30/597/thumbs/59771422018.gif",
      "Arizona": "https://content.sportslogos.net/logos/30/603/thumbs/60395182011.gif",
      "Baylor": "https://content.sportslogos.net/logos/30/613/thumbs/61311562019.gif",
      "Clemson": "https://content.sportslogos.net/logos/30/643/thumbs/2451.gif",
      "Dayton": "https://content.sportslogos.net/logos/31/655/thumbs/65553062014.gif",
      "Grand Canyon": "https://content.sportslogos.net/logos/31/5050/thumbs/505019672023.gif",
      "Michigan State": "https://content.sportslogos.net/logos/32/751/thumbs/75112152010.gif",
      "Nevada": "https://content.sportslogos.net/logos/33/767/thumbs/76753092008.gif",
      "North Carolina": "https://content.sportslogos.net/logos/33/775/thumbs/77515392015.gif",
      "Saint Mary's": "https://content.sportslogos.net/logos/34/822/thumbs/82293832022.gif",
      "Long Beach State": "https://content.sportslogos.net/logos/32/730/thumbs/73010942018.gif",
      "Charleston": "https://content.sportslogos.net/logos/30/637/thumbs/63731552013.gif",
      "Colgate": "https://content.sportslogos.net/logos/30/646/thumbs/64634482020.gif",
      "New Mexico": "https://content.sportslogos.net/logos/33/769/thumbs/new_mexico_lobos_logo_primary_2023sportslogosnet1811.gif",
      "Central Michigan": "https://content.sportslogos.net/logos/30/636/thumbs/6843.gif",
      "Ball State": "https://content.sportslogos.net/logos/30/612/thumbs/61273522015.gif",
      "Houston": "https://content.sportslogos.net/logos/31/700/thumbs/70018072017.gif",
      "Auburn": "https://content.sportslogos.net/logos/30/610/thumbs/61011451968.gif",
      "Duke": "https://content.sportslogos.net/logos/31/663/thumbs/66395011978.gif",
      "Florida": "https://content.sportslogos.net/logos/31/675/thumbs/67570762013.gif",
      "Arkansas": "https://content.sportslogos.net/logos/30/606/thumbs/60692202014.gif",
      "Texas A&M": "https://content.sportslogos.net/logos/34/866/thumbs/86656342021.gif",
      "Iowa": "https://content.sportslogos.net/logos/32/712/thumbs/71289231979.gif",
      "Marquette": "https://content.sportslogos.net/logos/32/741/thumbs/lk47sf36h6g3y141mktt.gif",
      "Providence": "https://content.sportslogos.net/logos/33/808/thumbs/80824872017.gif",
      "USC": "https://content.sportslogos.net/logos/34/840/thumbs/84036162016.gif",
      "Kentucky": "https://content.sportslogos.net/logos/32/721/thumbs/72178322016.gif",
      "Memphis": "https://content.sportslogos.net/logos/32/746/thumbs/74692712021.gif",
      "Indiana": "https://content.sportslogos.net/logos/32/709/thumbs/70922132002.gif",
      "Illinois": "https://content.sportslogos.net/logos/32/706/thumbs/70667022022.gif",
      "West Virginia": "https://content.sportslogos.net/logos/35/907/thumbs/90764092016.gif",
      "Rutgers": "https://content.sportslogos.net/logos/33/817/thumbs/81738102016.gif",
      "UConn": "https://content.sportslogos.net/logos/35/884/thumbs/88464902013.gif",
      "UCLA": "https://content.sportslogos.net/logos/35/882/thumbs/88285272017.gif",
      "Maryland": "https://content.sportslogos.net/logos/32/743/thumbs/74354442012.gif",
      "Xavier": "https://content.sportslogos.net/logos/35/919/thumbs/91958462008.gif",
      "Miami (FL)": "https://content.sportslogos.net/logos/32/748/thumbs/miami_hurricanes_logo_primary_2024sportslogosnet7626.gif",
      "Florida State": "https://content.sportslogos.net/logos/31/679/thumbs/67959842014.gif",
      "Wisconsin": "https://content.sportslogos.net/logos/35/914/thumbs/91436912017.gif",
      "Missouri": "https://content.sportslogos.net/logos/32/757/thumbs/75746882018.gif",
      "Seton Hall": "https://content.sportslogos.net/logos/35/920/thumbs/92018352019.gif",
      "Louisville": "https://content.sportslogos.net/logos/32/734/thumbs/73446722007.gif",
      "Georgetown": "https://content.sportslogos.net/logos/31/686/thumbs/41oxa3jgd3ht8c7a6zf2hbf99.gif",
      "Syracuse": "https://content.sportslogos.net/logos/34/859/thumbs/85984312015.gif",
      "Oklahoma": "https://content.sportslogos.net/logos/33/793/thumbs/79328022018.gif",
      "Pittsburgh": "https://content.sportslogos.net/logos/33/803/thumbs/80338912019.gif",
      "Colorado": "https://content.sportslogos.net/logos/30/647/thumbs/7489.gif",
      "Brigham Young": "https://content.sportslogos.net/logos/30/622/thumbs/62210722021.gif",
      "Northwestern": "https://content.sportslogos.net/logos/33/787/thumbs/78733582012.gif"
    }


    march_madness_2024 = [
      "Purdue", "Tennessee", "Creighton", "Kansas", "Gonzaga", "South Carolina", "Texas", "Utah State",
      "TCU", "Virginia", "Oregon", "McNeese State", "Samford", "Akron", "Saint Peter's", "Montana State",
      "Alabama", "Arizona", "Baylor", "Clemson", "Dayton", "Grand Canyon", "Michigan State", "Nevada",
      "North Carolina", "Saint Mary's", "Long Beach State", "Charleston", "Colgate", "New Mexico",
      "Central Michigan", "Ball State", "Houston", "Auburn", "Duke", "Florida", "Arkansas", "Texas A&M", 
      "Iowa", "Marquette", "Providence", "USC", "Kentucky", "Memphis", "Indiana", "Illinois", "West Virginia", 
      "Rutgers", "UConn", "UCLA", "Maryland", "Xavier", "Miami (FL)", "Florida State", "Wisconsin", "Missouri",
      "Seton Hall", "Louisville", "Georgetown", "Syracuse", "Oklahoma", "Pittsburgh", "Colorado", "Brigham Young",
      "Northwestern"
    ]

    valid_stats = ["PPG", "FGM", "FGA", "FG%", "3PM", "3PA", "3P%", "FTM", "FTA", "FT%", "ORB", "DRB", "RPG", "APG", "SPG", "BPG", "TOV", "PF"]
    print("")
    print("Stats: PPG, FGM, FGA, FG%, 3PM, 3PA, 3P%, FTM, FTA, FT%, ORB, DRB, RPG, APG, SPG, BPG, TOV, PF")
    
    xAxis = ""
    while True:
      print("Enter a x-axis stat>")
      xAxis = input()
      if xAxis == "cancel":
        print("canceling...")
        return
      if xAxis in valid_stats:
        break
      print("Invalid stat...")

    yAxis = ""
    while True:
      print("Enter a y-axis stat>")
      yAxis = input()
      if yAxis == "cancel":
        print("canceling...")
        return
      if yAxis in valid_stats:
        break
      print("Invalid stat...")

    year = "2025"
    api = '/stats'

    print(" ")
    save_path = os.path.join(os.path.dirname(__file__), f"{year}_{xAxis}_{yAxis}_graph.png")
    if os.path.exists(save_path):
            print(f"Graph already exists at {save_path}, skipping save.")
            return save_path
    
    print("Generating graph...")

    x = []
    y = []

    plt.clf()
    fig, ax = plt.subplots()
    for team_in_group in march_madness_2024:
      
      params = f'/{team_in_group}_exact/{year}'
      url = baseurl + api + params

      # res = requests.get(url)
      res = web_service_get(url)

      if res.status_code == 200:
        pass
      elif res.status_code == 400: #no games found
        print(f"{team_in_group} in march_madness_2024 is invalid")
        return
      else:
        print("**ERROR: failed with status code:", res.status_code)
        print("url: " + url)
        if res.status_code == 500:
          body = res.json()
          print("Error message:", body)
        return
      
      body = res.json()
      x_value = body[xAxis]
      y_value = body[yAxis]
      x.append(x_value)
      y.append(y_value)


      # Get the image URL for each team's logo (you can modify this to your actual URLs)
      if team_in_group in team_logos_2024:
        team_logo_url = team_logos_2024[team_in_group]
        size = 0.15
      else:
        print(f"Getting {team_in_group} image failed.")
        team_logo_url = "https://cdn3.iconfinder.com/data/icons/meteocons/512/n-a-512.png"
        size = 0.025
      
      logo_image = get_image_from_url2(team_logo_url)
      if logo_image == None:
        print(f"Failed to load image for {team_in_group}: {team_logo_url}")
        team_logo_url = "https://cdn3.iconfinder.com/data/icons/meteocons/512/n-a-512.png"
        logo_image = get_image_from_url2(team_logo_url)
        size = 0.025

      
      if logo_image:
        imagebox = OffsetImage(logo_image, zoom=size)  # Adjust zoom for image size
        #imagebox.set_resample(False)
        ab = AnnotationBbox(imagebox, (x_value, y_value), frameon=False)
        ax.add_artist(ab)

      
    # ALABAMA VERSION
    ax.set_xlabel(xAxis)
    ax.set_ylabel(yAxis)
    ax.set_title(f"{xAxis} vs {yAxis} ({year})")
    ax.plot(x, y, 'o', color='white', alpha=0)
    #ax.plot(x, y, 'o', color='blue') # Overlay data points
    #ax.grid(color='gray', linestyle='dashed', linewidth=0.3, alpha=0.5)
    ax.grid(False)

    # VERSION 1
    # plt.plot(x, y, marker='o', linestyle='', color='b')
    # plt.xlabel(xAxis)
    # plt.ylabel(yAxis)
    # plt.title(f"{xAxis} vs {yAxis} ({year})")
    # plt.grid(True)

    # NAMES VERSION
    # plt.scatter(x, y, color='b')
    # for i, team in enumerate(march_madness_2024):
    #   plt.text(x[i], y[i], team, fontsize=8, ha='right', va='bottom')
    # plt.xlabel(xAxis)
    # plt.ylabel(yAxis)
    # plt.title(f"{xAxis} vs {yAxis} ({year})")
    # plt.grid(True)
    


    plt.savefig(save_path, dpi = 300)
    print(f"Graph saved at {save_path}")
      
    return save_path

  except Exception as e:
    logging.error("**ERROR: graph() failed:")
    logging.error(e)
    return

############################################################
#
# predict
#
def predict(baseurl):
  """
  Predict game result of inputted teams using trained model in AWS SageMaker 

  Parameters
  ----------
  baseurl: baseurl for hoop deck web service

  Returns
  -------
  nothing
  """

  try:
    print("")

    yearUrl = "2025"

    while True:
      print("Enter team A (away)>")
      teamA = input()

      if teamA == "cancel":
        print("canceling...")
        return
      
      # call the web service:
      api = '/stats'
      params = f'/{teamA}/{yearUrl}'
      url = baseurl + api + params

      # res = requests.get(url)
      res = web_service_get(url)

      year = "2024-2025"

      if res.status_code == 200:
        break
      elif res.status_code == 400:
        print("")
        print(res.json())
        if res.json() == "No team found...":
          print('[cancel] to quit team stats command')
        else:
          print("Append _exact for a direct query (ex. Northwestern_exact)")  
      else:
        # failed:
        print("**ERROR: failed in predict with status code:", res.status_code)
        return
    
    bodyA = res.json()

    while True:
      print("Enter team B (home)>")
      teamB = input()

      if teamB == "cancel":
        print("canceling...")
        return
      
      # call the web service:
      api = '/stats'
      params = f'/{teamB}/{yearUrl}'
      url = baseurl + api + params

      # res = requests.get(url)
      res = web_service_get(url)

      year = "2024-2025"

      if res.status_code == 200:
        break
      elif res.status_code == 400:
        print("")
        print(res.json())
        if res.json() == "No team found...":
          print('[cancel] to quit team stats command')
        else:
          print("Append _exact for a direct query (ex. Northwestern_exact)")  
      else:
        # failed:
        print("**ERROR: failed in predict with status code:", res.status_code)
        return
    
    bodyB = res.json()

    team_nameA = bodyA["team_name"]
    team_nameB = bodyB["team_name"]

    print(f"Running model for {team_nameA} and {team_nameB} in {year} season...")

    api = '/predict'
    params = f'/{team_nameA}/{team_nameB}/{yearUrl}'
    url = baseurl + api + params
    # res = requests.get(url)

    res = web_service_get(url)


    if res.status_code == 200:
      pass
    else:
      print("Error in client predict function calling lambda")
      return
    
    
    margin = res.json()
    abs_margin = abs(margin)

    if margin > 0:
      print(f"Model predicts {team_nameA} will win by {abs_margin}!")
    else:
      print(f"Model predicts {team_nameB} will win by {abs_margin}!")
    

    return

  except Exception as e:
    logging.error("**ERROR: predict() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# check_url
#
def check_url(baseurl):
  """
  Performs some checks on the given url, which is read from a config file.
  Returns updated url if it needs to be modified.

  Parameters
  ----------
  baseurl: url for a web service

  Returns
  -------
  same url or an updated version if it contains an error
  """

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]
    
  return baseurl
  

############################################################
# main
#
try:
  print('**Welcome to HoopDeck! 🏀')

#   print("Creators: Lucas Holliday, Sid Javeri, and Helena Yuan")
#   print()
#   print("""
# Hoop Deck is designed for the avid March Madness Fan who wants to analyze team statistics, 
# gain AI-driven game predictions, and easily discover games to attend. Our app provides data-driven
# insights to help users make informed bracket decisions while also offering tools for interactive statistical analysis.
# """)

# TicketMaster games, # team stats, game predictions



  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  hoopdeck_config_file = 'hoopdeck-client-config.ini'
  
  if not pathlib.Path(hoopdeck_config_file).is_file():
    print("**ERROR: hoopdeck config file '", hoopdeck_config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(hoopdeck_config_file)
  baseurl = configur.get('client', 'webservice')
  
  baseurl = check_url(baseurl)

  # GET TEAM IMAGES FROM FILE

  teamImages = []
  
  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1: # print("   1 => find games")
      ticketmaster(baseurl)
    elif cmd == 2: # print("   2 => team stats")
      stats(baseurl)
    elif cmd == 3: # print("   3 => analyze stats")
      graph(baseurl, teamImages)
    elif cmd == 4: # print("   4 => predict winner")
      predict(baseurl)
    elif cmd == 5:
      statsKey()
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
