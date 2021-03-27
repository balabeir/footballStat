from flask import Flask, jsonify
import requests

app = Flask(__name__)


@app.route("/PremeirLeague")
def getallPremeirLeague():
    url = "https://app.sportdataapi.com/api/v1/soccer/matches"
    headers = {"apikey": "6f889a60-8edd-11eb-9084-05c23de9546d"}
    payload = {"season_id": "352"}
    data = requests.get(url, headers=headers, params=payload).json()
    return data


@app.route("/LaLiga")
def getallLaLiga():
    url = "https://app.sportdataapi.com/api/v1/soccer/matches"
    headers = {"apikey": "6f889a60-8edd-11eb-9084-05c23de9546d"}
    payload = {"season_id": "1511"}
    data = requests.get(url, headers=headers, params=payload).json()
    return data


if __name__ == "__main__":
    app.run()