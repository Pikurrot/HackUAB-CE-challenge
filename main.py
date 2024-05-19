import graph

from flask import Flask
import pandas as pd
import json

app = Flask(__name__)

precomputed_data = {}

def precompute_data():
    # Precompute data for each route and store in global dictionary
    for lot in [2, 4, 5]:
        ordered_coordinates, tours, total_days = graph.main(lot)
        precomputed_data[lot] = {
            "ordered_coordinates": ordered_coordinates,
            "tours": tours,
            "total_days": total_days
        }

@app.route("/route1")
def route1():
	ordered_coordinates2 = precomputed_data[2]["ordered_coordinates"]
	total_days2 = precomputed_data[2]["total_days"]

	df = pd.read_csv("Dades_Municipis_Lot_2.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		if not pob.is_integer():
			pob *= 1000
		locations[coord] = [town, int(pob)]

	towns = []
	for coord in ordered_coordinates2:
		towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
	return json.dumps(towns)

@app.route("/route2")
def route2():
	ordered_coordinates4 = precomputed_data[4]["ordered_coordinates"]
	total_days4 = precomputed_data[4]["total_days"]

	df = pd.read_csv("Dades_Municipis_Lot_4.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		if not pob.is_integer():
			pob *= 1000
		locations[coord] = [town, int(pob)]

	towns = []
	for coord in ordered_coordinates4:
		towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
	return json.dumps(towns)

@app.route("/route3")
def route3():
	ordered_coordinates5 = precomputed_data[5]["ordered_coordinates"]
	total_days5 = precomputed_data[5]["total_days"]

	df = pd.read_csv("Dades_Municipis_Lot_5.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		if not pob.is_integer():
			pob *= 1000
		locations[coord] = [town, int(pob)]

	towns = []
	for coord in ordered_coordinates5:
		towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
	return json.dumps(towns)

def main():
	precompute_data()

if __name__ == "__main__":
	app.run()
