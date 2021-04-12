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
Matches = db.Matches
Standings = db.Standings
headers = {"apikey": "6f889a60-8edd-11eb-9084-05c23de9546d"}


@app.route("/PremeirLeague/Matches")
def getallPremeirLeague():
    data = Matches.find({"season_id": 352})
    return json_util.dumps(data)


@app.route("/LaLiga/Matches")
def getallLaLiga():
    data = Matches.find({"season_id": 1511})
    return json_util.dumps(data)


def prepareDB():
    prepareLeaguesDB()
    prepareMatchesDB()
    prepareStandings()


### LeaguesDB ###
def prepareLeaguesDB():
    leagues = getSubscribLeagues()
    seasons = getLeagueSeasonInfo(leagues)

    datas = list()
    for i in range(len(leagues)):
        data = dict()
        data["league_id"] = leagues[i]["league_id"]
        data["name"] = leagues[i]["name"]
        data["season_data"] = seasons[i]
        datas.append(data)

    # check is first init
    if "Leagues" in db.list_collection_names():
        i = 0
        for obj in Leagues.find({}):
            Leagues.replace_one({"_id": obj["_id"]}, datas[i])
            i += 1
    else:
        Leagues.insert_many(datas)


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


### MatchesDB ###
def prepareMatchesDB():
    firstInit = False
    if "Matches" not in db.list_collection_names():
        db.create_collection("Matches")
        firstInit = True

    current_season_list = getSeasonID()
    url = "https://app.sportdataapi.com/api/v1/soccer/matches"

    # get current season form premierLeague and LaLiga
    datas = list()
    for i in range(len(current_season_list)):
        current_season = current_season_list[i]
        params = {"season_id": current_season}
        datas.append(requests.get(url, headers=headers, params=params).json()["data"])

        # sort matches data orderby date
        sortedData = sorted(datas[i], key=lambda data: data["match_start_iso"])

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if firstInit:
            Matches.insert_many(sortedData)
        else:
            matchIndex = 0
            for match in Matches.find(params):
                Matches.replace_one({"_id": match["_id"]}, sortedData[matchIndex])
                matchIndex += 1


def getSeasonID():
    current_season_list = list()
    for obj in Leagues.find({}):
        seasons = obj["season_data"]
        for season in seasons:
            if season["is_current"] == 1:
                current_season_list.append(season["season_id"])
                break
    return current_season_list


### Standings ###
def prepareStandings():
    firstInit = False
    if "Standings" not in db.list_collection_names():
        db.create_collection("Standings")
        firstInit = True

    current_season_list = getSeasonID()
    url = "https://app.sportdataapi.com/api/v1/soccer/standings"

    for i in range(len(current_season_list)):
        current_season = current_season_list[i]
        params = {"season_id": current_season}
        data = requests.get(url, headers=headers, params=params).json()["data"]
        for s in range(len(data["standings"])):
            team_id = data["standings"][s]["team_id"]
            team_url = "https://app.sportdataapi.com/api/v1/soccer/teams/" + str(team_id)
            team_data = requests.get(team_url, headers=headers).json()["data"]
            data["standings"][s]["team_data"] = team_data

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if firstInit:
            Standings.insert_one(data)
        else:
            Standings.replace_one({"season_id": data["season_id"]}, data)


if __name__ == "__main__":
    # prepareDB()
    app.run()