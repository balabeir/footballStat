from flask import Flask, jsonify
from pymongo import MongoClient
from bson import json_util
import requests
from pprint import pprint


app = Flask(__name__)

# mongo database URI
client = MongoClient("mongodb://localhost:27017/")
# database name
db = client["SoccerScore"]
Leagues = db.Leagues
Teams = db.Teams
Matches = db.Matches
Standings = db.Standings
headers = {"apikey": "6f889a60-8edd-11eb-9084-05c23de9546d"}


# @app.route("/PremeirLeague/Matches")
# def getallPremeirLeague():
#     data = Matches.find({"season_id": 352})
#     return json_util.dumps(data)


# @app.route("/LaLiga/Matches")
# def getallLaLiga():
#     data = Matches.find({"season_id": 1511})
#     return json_util.dumps(data)


def prepareDB():
    prepareLeaguesDB()
    prepareTeamDB()
    prepareMatchesDB()
    prepareStandings()


### LeaguesDB ###
# find league_id, season_id and country_id in subscribLeagues
def prepareLeaguesDB():
    leagues = getSubscribLeagues()
    seasons = getLeagueSeasonInfo(leagues)

    for i in range(len(leagues)):
        # filter before put to db
        league_data = dict()
        league_data = leagues[i]
        league_data["season_data"] = seasons[i]

        filter = {"league_id": league_data["league_id"]}
        update = {"$set": league_data}
        Leagues.update_one(filter=filter, update=update, upsert=True)


def getSubscribLeagues():
    params = {"subscribed": True}

    response = requests.get("https://app.sportdataapi.com/api/v1/soccer/leagues", headers=headers, params=params).json()
    datas = response["data"]

    return datas


def getLeagueSeasonInfo(leagues):

    seasonData = list()
    for league in leagues:
        params = {"league_id": league["league_id"]}
        response = requests.get(
            "https://app.sportdataapi.com/api/v1/soccer/seasons", headers=headers, params=params
        ).json()
        seasonData.append(response["data"])

    return seasonData


### TeamDB ###
# find every team in country is subscrib
def prepareTeamDB():

    for league in Leagues.find({}):
        # find team by country_id
        params = {"country_id": league["country_id"]}
        response = requests.get(
            "https://app.sportdataapi.com/api/v1/soccer/teams", headers=headers, params=params
        ).json()

        # update team_data and insert team isn't exist
        team_data = response["data"]
        for data in team_data:
            filter = {"team_id": data["team_id"]}
            update = {"$set": data}
            Teams.update_one(filter=filter, update=update, upsert=True)


### MatchesDB ###
def prepareMatchesDB():

    current_season_list = getSeasonID()  # get current season form subscrib Leagues
    url = "https://app.sportdataapi.com/api/v1/soccer/matches"

    datas = list()
    for i in range(len(current_season_list)):
        current_season = current_season_list[i]
        params = {"season_id": current_season}
        datas.append(requests.get(url, headers=headers, params=params).json()["data"])

        # sort matches data orderby date
        sortedData = sorted(datas[i], key=lambda data: data["match_start_iso"])

        for match in sortedData:
            filter = {"match_id": match["match_id"]}
            update = {"$set": match}
            Matches.update_one(filter=filter, update=update, upsert=True)


def getSeasonID():
    current_season_list = list()
    for obj in Leagues.find({}):
        seasons = obj["season_data"]
        for season in seasons:
            if season["is_current"] == 1:
                current_season_list.append(season["season_id"])
                break
    return current_season_list


### Standings Ranking ###
def prepareStandings():

    current_season_list = getSeasonID()
    url = "https://app.sportdataapi.com/api/v1/soccer/standings"

    for i in range(len(current_season_list)):
        current_season = current_season_list[i]
        params = {"season_id": current_season}
        data = requests.get(url, headers=headers, params=params).json()["data"]

        filter = {"season_id": data["season_id"]}
        update = {"$set": data}
        Standings.update_one(filter=filter, update=update, upsert=True)


if __name__ == "__main__":
    prepareDB()
    # app.run()