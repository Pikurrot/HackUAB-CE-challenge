import graph

from flask import Flask
import pandas as pd
import json

app = Flask(__name__)

precomputed_data = {}

def precompute_data():
    # Precompute data for each route and store in global dictionary
    for lot in [2, 4, 5]:
        ordered_coordinates, tours, coordinates_divs2, tours_divs, total_days = graph.main(lot)
        precomputed_data[lot] = {
            "ordered_coordinates": ordered_coordinates,
            "tours": tours,
			"coordinates_divs": coordinates_divs2,
			"tours_divs": tours_divs,
            "total_days": total_days
        }


LOTS = [2, 4, 5];
N_WEEKS = 4;
N_DAYS = 5;

@app.route("/lot/<lot>")
def getRoute(lot):
	lot = int(lot)
	if not lot in LOTS:
		return
	
	ordered_coordinates = precomputed_data[lot]["ordered_coordinates"]
	total_days = precomputed_data[lot]["total_days"]

	df = pd.read_csv(f"data/Dades_Municipis_Lot_{lot}.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		locations[coord] = [town, int(pob)]

	blocks = {}
	for b, block in enumerate(ordered_coordinates):
		towns = []
		for coord in block:
			towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
		blocks[f"block{b}"] = towns
		
	return json.dumps(towns)

@app.route("/lot/<lot>/days/<b>/<d>")
def getRouteDays(lot, b, d):
	lot = int(lot)
	b = int(b)
	d = int(d)
	if not lot in LOTS:
		return
	
	coordinates_divs = precomputed_data[lot]["coordinates_divs"]
	total_days = precomputed_data[lot]["total_days"]

	df = pd.read_csv(f"data/Dades_Municipis_Lot_{lot}.csv")
	locations = {}
	for town, pob, coord in zip(df["Municipi"], df["Pob."], df["coordinates"]):
		locations[coord] = [town, int(pob)]

	towns = []
	block = coordinates_divs[b]
	day = block[d]
	for coord in day:
		towns.append({"location":locations[str(coord)][0], "population":locations[str(coord)][1], "coordinates":coord})
		
	return json.dumps(towns)

@app.route("/")
def root():
	main()
	return "Go to /lot/2 or /lot/4 or /lot/5, or also /lot/2/days, ..."

def main():
	precompute_data()

if __name__ == "__main__":
	app.run()
