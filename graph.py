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
from scipy.spatial.distance import pdist, squareform
from itertools import combinations
import random

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
	
def create_knn_graph(filtered_towns, filtered_coordinates, filtered_distance_matrix, k):
	G = nx.DiGraph()
	pos = {}
	for i, town in enumerate(filtered_towns):
		G.add_node(town)
		pos[town] = (filtered_coordinates[i][0], filtered_coordinates[i][1])  # (longitude, latitude)

	for i in range(len(filtered_towns)):
		nearest_neighbors = np.argsort(filtered_distance_matrix[i])[1:k+1]
		for j in nearest_neighbors:
			G.add_edge(filtered_towns[i], filtered_towns[j], weight=filtered_distance_matrix[i][j])
	
	return G, pos

# Nearest Neighbor algorithm with restart for disconnected components
def nearest_neighbor_algorithm(G, start):
	unvisited = set(G.nodes)
	tour = [start]
	unvisited.remove(start)
	current = start

	while unvisited:
		# Find the nearest unvisited neighbor, falling back to shortest path if necessary
		nearest_neighbor = None
		nearest_distance = float('inf')
		for node in unvisited:
			if G.has_edge(current, node):
				distance = G[current][node]['weight']
				if distance < nearest_distance:
					nearest_neighbor = node
					nearest_distance = distance
			else:
				try:
					distance = nx.shortest_path_length(G, current, node, weight='weight')
					if distance < nearest_distance:
						nearest_neighbor = node
						nearest_distance = distance
				except nx.NetworkXNoPath:
					continue
		
		if nearest_neighbor is None:
			# If no reachable node is found, restart from the next unvisited node
			current = unvisited.pop()
			tour.append(current)
		else:
			tour.append(nearest_neighbor)
			unvisited.remove(nearest_neighbor)
			current = nearest_neighbor
	
	tour.append(start)  # return to the start
	return tour

# Create a complete graph for 2-opt optimization
def create_complete_graph(G):
	complete_G = nx.complete_graph(G.nodes, create_using=nx.DiGraph())
	for u, v in complete_G.edges:
		if G.has_edge(u, v):
			complete_G[u][v]['weight'] = G[u][v]['weight']
		else:
			try:
				complete_G[u][v]['weight'] = nx.shortest_path_length(G, u, v, weight='weight')
			except nx.NetworkXNoPath:
				complete_G[u][v]['weight'] = float('inf')
	return complete_G

# 2-opt optimization with shortest path fallback
def two_opt(tour, complete_G):
	best_tour = tour
	improved = True

	def tour_length(tour):
		length = 0
		for i in range(len(tour) - 1):
			length += complete_G[tour[i]][tour[i + 1]]['weight']
		return length

	while improved:
		improved = False
		for i, j in combinations(range(1, len(tour) - 1), 2):
			if j - i == 1: continue
			new_tour = tour[:i] + tour[i:j][::-1] + tour[j:]
			if tour_length(new_tour) < tour_length(best_tour):
				best_tour = new_tour
				improved = True
	
	return best_tour

# Plotting function
def plot_graph(nodes, edges_gdf, min_x, max_x, min_y, max_y, hamiltonian_path, pos):
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

	# Highlight the starting point (green) and ending point (blue)
	start_point = hamiltonian_path[0]
	end_point = hamiltonian_path[-1]

	ax.scatter([pos[start_point][0]], [pos[start_point][1]], color='green', s=100, zorder=5, label='Start Point')
	ax.scatter([pos[end_point][0]], [pos[end_point][1]], color='blue', s=100, zorder=5, label='End Point')

	# Plot the tour with direction arrows
	for i in range(len(hamiltonian_path) - 1):
		u, v = hamiltonian_path[i], hamiltonian_path[i + 1]
		line = LineString([Point(pos[u]), Point(pos[v])])
		gpd.GeoSeries([line]).plot(ax=ax, color='red')

		# Draw arrow
		ax.annotate(
			'',
			xy=(pos[v][0], pos[v][1]),
			xytext=(pos[u][0], pos[u][1]),
			arrowprops=dict(arrowstyle="->", color='red', lw=1),
			size=15
		)

	plt.xlabel('Longitude')
	plt.ylabel('Latitude')
	plt.title('Graph of Towns with TSP Tour')
	plt.legend()
	plt.show()


def main(plot=False):
	# Load the data
	df2 = pd.read_csv('data/Dades_Municipis_Lot_2.csv')

	# Get coordinates for each town
	coordinates2 = apply_coordinates(df2)

	# Build the full distance matrix
	distance_matrix2 = build_full_distance_matrix(coordinates2)

	# Build the graph
	k = 3
	G2, pos2, filtered_towns2, filtered_coordinates2 = build_graph(coordinates2, distance_matrix2, df2, k)

	filtered_distance_matrix2 = squareform(pdist(filtered_coordinates2, metric='euclidean'))

	G2, pos = create_knn_graph(filtered_towns2, filtered_coordinates2, filtered_distance_matrix2, k)

	start = random.choice(filtered_towns2)
	initial_tour2 = nearest_neighbor_algorithm(G2, start)
	 
	complete_G2 = create_complete_graph(G2)
	
	optimized_tour2 = two_opt(initial_tour2, complete_G2)
	
	nodes2 = gpd.GeoDataFrame({
		'town': filtered_towns2,
		'geometry': [Point(lon, lat) for lon, lat in filtered_coordinates2]
	})
	 
	edges2 = []
	for u, v, data in G2.edges(data=True):
		line = LineString([Point(pos[u]), Point(pos[v])])
		edges2.append({'source': u, 'target': v, 'weight': data['weight'], 'geometry': line})

	edges_gdf2 = gpd.GeoDataFrame(edges2)

	town_to_coordinates2 = dict(zip(df2['Municipi'], df2['coordinates']))
	towns2 = df2["Municipi"].tolist()
	ordered_coordinates2 = [town_to_coordinates2[town] for town in towns2]

	# Plot the graph on a map
	if plot:
		min_x = min(coord[0] for coord in filtered_coordinates2)
		max_x = max(coord[0] for coord in filtered_coordinates2)
		min_y = min(coord[1] for coord in filtered_coordinates2)
		max_y = max(coord[1] for coord in filtered_coordinates2)
		plot_graph(nodes2, edges_gdf2, min_x, max_x, min_y, max_y, optimized_tour2)

	return ordered_coordinates2