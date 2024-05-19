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


LOTS = [2, 4, 5];
N_WEEKS = 4;
N_DAYS = 5;

@app.route("/lot/{lot}")
def getRoute(lot):
	if not lot in LOTS:
		return
	
	ordered_coordinates = precomputed_data[lot]["ordered_coordinates"]
	total_days = precomputed_data[lot]["total_days"]

	df = pd.read_csv(f"Dades_Municipis_Lot_{lot}.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		if not pob.is_integer():
			pob *= 1000
		locations[coord] = [town, int(pob)]

	towns = []
	for coord in ordered_coordinates:
		towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
	return json.dumps(towns)

def main():
	precompute_data()

if __name__ == "__main__":
	app.run()
