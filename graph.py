import json
from opencage.geocoder import OpenCageGeocode
import openrouteservice
from openrouteservice import convert
import numpy as np
import time
from tqdm import tqdm
import scipy.stats as stats
import geopandas as gpd
from shapely.geometry import Point, LineString
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def instantiate_geocoder():
	with open("credentials.json") as f:
		credentials = json.load(f)
	return OpenCageGeocode(credentials["opencage_API_key"])

def get_coordinates(town: str, geocoder) -> list:
	result = geocoder.geocode(town, countrycode='ES')
	if result and len(result):
		lat = result[0]['geometry']['lat']
		lng = result[0]['geometry']['lng']
		return [lng, lat]
	else:
		return None
	
def apply_coordinates(df):
	geocoder = instantiate_geocoder()
	df['coordinates'] = df['Municipi'].apply(lambda x: get_coordinates(x, geocoder))
	return df["coordinates"].tolist()
	  
def instantiate_openroute_client():
	with open("credentials.json") as f:
		credentials = json.load(f)
	my_key = credentials["openrouteservice_API_key"]
	client = openrouteservice.Client(key=my_key)
	return client

def get_distances(coordinates):
    client = instantiate_openroute_client()

    # Get distance matrix
    distance_matrix = client.distance_matrix(
        locations=coordinates,
        profile='driving-car',
        metrics=['distance'],
        units='km'
    )

    return distance_matrix['distances']

def build_full_distance_matrix(coordinates, batch_size=10):
    n = len(coordinates)
    distance_matrix = np.zeros((n, n))  # Initialize a full distance matrix

    # Create batches of coordinates
    batches = [coordinates[i:i + batch_size] for i in range(0, n, batch_size)]
    batch_indices = [range(i, min(i + batch_size, n)) for i in range(0, n, batch_size)]

    # Process each pair of batches
    for idx1, batch1 in enumerate(batches):
        print(f"Processing batch {idx1 + 1}/{len(batches)}")
        for idx2, batch2 in tqdm(enumerate(batches), total=len(batches)):
            # Only process upper triangle and diagonal (since the distance matrix is symmetric)
            if idx1 <= idx2:
                combined_coordinates = batch1 + batch2

                # Get distances for the combined coordinates
                distances = get_distances(combined_coordinates)

                # Populate the distance matrix
                for i, src_idx in enumerate(batch_indices[idx1]):
                    for j, dest_idx in enumerate(batch_indices[idx2]):
                        distance_matrix[src_idx, dest_idx] = distances[i][j]
                        distance_matrix[dest_idx, src_idx] = distances[i][j]  # Symmetric

                time.sleep(0.3)

    return distance_matrix

def build_graph(coordinates, distance_matrix, df, k, outlier_thresh=3):
	towns = df["Municipi"].tolist()

	# Step 1: Identify outliers using Z-score
	coordinates_np = np.array(coordinates)
	z_scores = np.abs(stats.zscore(coordinates_np))
	outliers = np.any(z_scores > outlier_thresh, axis=1)

	# Step 2: Filter coordinates and towns
	filtered_coordinates = [coord for i, coord in enumerate(coordinates) if not outliers[i]]
	filtered_towns = [town for i, town in enumerate(towns) if not outliers[i]]

	# Step 3: Filter distance matrix
	filtered_indices = [i for i in range(len(towns)) if not outliers[i]]
	filtered_distance_matrix = distance_matrix[np.ix_(filtered_indices, filtered_indices)]

	# Create the directed graph
	G = nx.DiGraph()

	# Add nodes with positions
	pos = {}
	for i, town in enumerate(filtered_towns):
		G.add_node(town)
		pos[town] = (filtered_coordinates[i][0], filtered_coordinates[i][1])  # (longitude, latitude)

	# Add edges with weights only to k nearest neighbors
	for i in range(len(filtered_towns)):
		# Get the indices of the k smallest distances (excluding self-loops)
		nearest_neighbors = np.argsort(filtered_distance_matrix[i])[1:k+1]
		for j in nearest_neighbors:
			G.add_edge(filtered_towns[i], filtered_towns[j], weight=filtered_distance_matrix[i][j])

	return G, pos, filtered_towns, filtered_coordinates

def build_geodataframes(G, pos, filtered_towns, filtered_coordinates):
	# Create GeoDataFrames for nodes and edges
	nodes = gpd.GeoDataFrame({
		'town': filtered_towns,
		'geometry': [Point(lon, lat) for lon, lat in filtered_coordinates]
	})

	edges = []
	for u, v, data in G.edges(data=True):
		line = LineString([Point(pos[u]), Point(pos[v])])
		edges.append({'source': u, 'target': v, 'weight': data['weight'], 'geometry': line})

	edges_gdf = gpd.GeoDataFrame(edges)
	return edges_gdf, nodes

def plot_geo_data(edges_gdf, nodes, filtered_coordinates):
	# Determine the extent of the coordinates
	min_x = min(coord[0] for coord in filtered_coordinates)
	max_x = max(coord[0] for coord in filtered_coordinates)
	min_y = min(coord[1] for coord in filtered_coordinates)
	max_y = max(coord[1] for coord in filtered_coordinates)

	# Plotting the graph on a map
	fig, ax = plt.subplots(1, 1, figsize=(10, 10))
	world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

	# Plot base map within the bounds of the coordinates
	world.boundary.plot(ax=ax, linewidth=1)
	ax.set_xlim(min_x - 0.5, max_x + 0.5)  # Adding a small buffer for better visualization
	ax.set_ylim(min_y - 0.5, max_y + 0.5)

	# Plot edges
	edges_gdf.plot(ax=ax, linewidth=0.2, edgecolor='gray')

	# Plot nodes
	nodes.plot(ax=ax, color='blue', markersize=20)

	# Add labels
	for x, y, label in zip(nodes.geometry.x, nodes.geometry.y, nodes['town']):
		ax.text(x, y, label, fontsize=8, ha='right')

	plt.xlabel('Longitude')
	plt.ylabel('Latitude')
	plt.title('Graph of Towns with K Nearest Neighbors on Geographic Map')
	plt.show()
	
def main(plot=True):
	# Load the data
	df2 = pd.read_csv('data/Dades_Municipis_Lot_2.csv')

	# Get coordinates for each town
	coordinates2 = apply_coordinates(df2)

	# Build the full distance matrix
	distance_matrix2 = build_full_distance_matrix(coordinates2)

	# Build the graph
	k = 5
	G2, pos2, filtered_towns2, filtered_coordinates2 = build_graph(coordinates2, distance_matrix2, df2, k)

	# Plot the graph on a map
	if plot:
		# Build GeoDataFrames for plotting
		edges_gdf2, nodes2 = build_geodataframes(G2, pos2, filtered_towns2, filtered_coordinates2)
		plot_geo_data(edges_gdf2, nodes2, filtered_coordinates2)
