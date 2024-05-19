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
import os
from requests import get

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

def filter_outliers(coordinates, df, outlier_thresh=3):
	towns = df["Municipi"].tolist()
	
	# Step 1: Identify outliers using Z-score
	coordinates_np = np.array(coordinates)
	z_scores = np.abs(stats.zscore(coordinates_np))
	outliers = np.any(z_scores > outlier_thresh, axis=1)

	# Step 2: Filter coordinates and towns
	filtered_coordinates = [coord for i, coord in enumerate(coordinates) if not outliers[i]]
	filtered_towns = [town for i, town in enumerate(towns) if not outliers[i]]
	outlier_towns = [town for i, town in enumerate(towns) if outliers[i]]
	return filtered_coordinates, filtered_towns, outliers

def build_graph(coordinates, distance_matrix, df, k, outlier_thresh=3):
	towns = df["Municipi"].tolist()

	# Step 1: Filter out outliers
	filtered_coordinates, filtered_towns, outliers = filter_outliers(coordinates, distance_matrix, df, outlier_thresh)
	
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

def get_route_times(coordinates):
	with open("credentials.json") as f:
		credentials = json.load(f)
	api_key = credentials["tomtom_API_key"]
	link = "https://api.tomtom.com/routing/1/calculateRoute/"

	times = []
	prev_coord = coordinates[0]
	previous = "%2C".join(str(x) for x in prev_coord) + "%3A"
	for coord in tqdm(coordinates[1:]):
		actual = "%2C".join(str(x) for x in coord) + "%3A"
		route = get(link + previous + actual + "/json?key=" + api_key)
		# time.sleep(0.2)
		previous = actual
		if route.status_code != 200:
			# print(f"Error: {route.status_code}")
			times.append(None)
			continue
		else:
			pass
			# print(f"Success: {route.status_code}")
		time_ = route.json()["routes"][0]["summary"]["travelTimeInSeconds"]
		times.append(time_)
	return times

# Plotting function
def plot_graph(nodes, edges_gdf, min_x, max_x, min_y, max_y, coords, ax=None, color="red"):
	if ax is None:
		fig, ax = plt.subplots(1, 1, figsize=(10, 10))
		world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
		world.boundary.plot(ax=ax, linewidth=1)
		ax.set_xlim(min_x - 0.1, max_x + 0.1)  # Adding a small buffer for better visualization
		ax.set_ylim(min_y - 0.1, max_y + 0.1)
	else:
		fig = plt.gcf()

	# Plot edges
	edges_gdf.plot(ax=ax, linewidth=0.2, edgecolor='gray')

	# Plot nodes
	nodes.plot(ax=ax, color='blue', markersize=20)

	# Add labels
	for x, y, label in zip(nodes.geometry.x, nodes.geometry.y, nodes['town']):
		ax.text(x, y, label, fontsize=8, ha='right')

	# Highlight the starting point (green) and ending point (blue)
	start_point = coords[0]
	end_point = coords[-1]

	ax.scatter([start_point[0]], [start_point[1]], color='green', s=100, zorder=5, label='Start Point')
	ax.scatter([end_point[0]], [end_point[1]], color='blue', s=100, zorder=5, label='End Point')

	# Plot the tour with direction arrows
	for i in range(len(coords) - 1):
		u, v = coords[i], coords[i + 1]
		line = LineString([Point(u), Point(v)])
		gpd.GeoSeries([line]).plot(ax=ax, color=color)

		# Draw arrow
		ax.annotate(
			'',
				xy=(v[0], v[1]),
				xytext=(u[0], u[1]),
				arrowprops=dict(arrowstyle="->", color=color, lw=1),
				size=15
			)

	return fig, ax

def estancia_to_seconds(estancia):
    time, unit = estancia.split()
    time = int(time)
    if "MINUTO" in unit:
        return time * 60
    elif "HORA" in unit:
        return time * 3600
    else:
        return 0

def main(lot=2, start=None, plot=False):
	assert lot in [2, 4, 5], "Invalid lot number"
	# Load the data
	df2 = pd.read_csv(f'data/Dades_Municipis_Lot_{lot}.csv')
	blocks = df2['BLOC'].unique()
	df2_blocks = [df2[df2["BLOC"] == i] for i in blocks]
	if start is None:
		start = random.choice(df2[df2["BLOC"] == 1]['Municipi'].tolist())
	start_row = df2[df2['Municipi'] == start]
	for i, block in enumerate(df2_blocks[1:], start=1):
		# append start to each block
		block = pd.concat([start_row, block], ignore_index=True)
		df2_blocks[i] = block
	df2 = pd.concat(df2_blocks, ignore_index=True)
	estancy_dict2 = {row['Municipi']: estancia_to_seconds(row['Estancia Minima']) for _, row in df2.iterrows()}

	# Get coordinates for each town
	# coordinates2 = apply_coordinates(df2)
	coordinates2 = [[eval(i) for i in block['coordinates'].to_list()] for block in df2_blocks]

	# Build the full distance matrix
	distance_matrices2 = []
	for i, block in enumerate(df2_blocks):
		if os.path.exists(f'data/distance_matrix{lot}_{i}.npy'):
			distance_matrix2 = np.load(f'data/distance_matrix{lot}_{i}.npy')
		else:
			distance_matrix2 = build_full_distance_matrix(coordinates2[i])
			np.save(f'data/distance_matrix{lot}_{i}.npy', distance_matrix2)
		distance_matrices2.append(distance_matrix2)

	k = 3
	merged_coordinates2 = [coord for block in coordinates2 for coord in block]
	filtered_coordinates2_, filtered_towns2_, _ = filter_outliers(merged_coordinates2, df2)
	filtered_towns2, filtered_coordinates2 = [], []
	for i, block in enumerate(df2_blocks):
		filtered_towns2.append([town for town in filtered_towns2_ if town in block['Municipi'].tolist()])
		filtered_coordinates2.append([coord for coord in filtered_coordinates2_ if coord in coordinates2[i]])

	filtered_distance_matrix2 = []
	for i, block in enumerate(df2_blocks):
		filtered_distance_matrix2_block = squareform(pdist(filtered_coordinates2[i], metric='euclidean'))	
		filtered_distance_matrix2.append(filtered_distance_matrix2_block)

	G2, pos2 = [], []
	for i, block in enumerate(df2_blocks):
		G2_block, pos2_block = create_knn_graph(filtered_towns2[i], filtered_coordinates2[i], filtered_distance_matrix2[i], k)
		G2.append(G2_block)
		pos2.append(pos2_block)

	tours2 = []
	for i, block in enumerate(df2_blocks):
		tour = nearest_neighbor_algorithm(G2[i], start)
		complete_G2 = create_complete_graph(G2[i])
		optimized_tour = two_opt(tour, complete_G2)
		tours2.append(optimized_tour)

	town_to_coordinates2_ = {town: coord for town, coord in zip(filtered_towns2_, filtered_coordinates2_)}
	town_to_coordinates2, ordered_coordinates2 = [], []
	for i, block in enumerate(df2_blocks):
		town_to_coordinates2_block = {town: coord for town, coord in town_to_coordinates2_.items() if town in filtered_towns2[i]}
		ordered_coordinates2_block = [town_to_coordinates2_block[town] for town in tours2[i]]
		town_to_coordinates2.append(town_to_coordinates2_block)
		ordered_coordinates2.append(ordered_coordinates2_block)

	times2 = []
	for i, block in enumerate(df2_blocks):
		times2_block = get_route_times(ordered_coordinates2[i])
		times2.append(times2_block)

	distances2 = []
	for i, block in enumerate(df2_blocks):
		distances2_ = [filtered_distance_matrix2[i][filtered_towns2[i].index(u), filtered_towns2[i].index(v)]\
				 for u, v in zip(tours2[i][:-1], tours2[i][1:])]
		distances2.append(distances2_)

	# handle cases where time is None
	for i, block in enumerate(df2_blocks):
		# take example time and distance where time is not None
		j = 0
		while times2[i][j] is None:
			j += 1
		example_time = times2[i][j]
		example_distance = distances2[i][j]
		for k, time_ in enumerate(times2[i]):
			if time_ is None:
				# compute time based on distance
				dist = distances2[i][k]
				times2[i][k] = example_time * dist / example_distance

	estancy2 = []
	for i, block in enumerate(df2_blocks):
		estancy2_block = [estancy_dict2[town] for town in tours2[i]]
		estancy2.append(estancy2_block)

	working_hours = 8
	working_time = working_hours * 3600 

	tours_divs2 = []
	for b, block in enumerate(df2_blocks):
		sum_ = 0
		divs = []
		for i in range(len(ordered_coordinates2[b]) - 1):
			sum_ += estancy2[b][i]
			sum_ += times2[b][i]
			if sum_ > working_time:
				divs.append(i)
				sum_ = 0

		tours_divs = []
		for i, j in zip(divs, divs[1:]):
			tours_divs.append(tours2[b][i:j])
		tours_divs2.append(tours_divs)

	# Plot the graph on a map
	if plot:
		all_cordinates = [coord for block in ordered_coordinates2 for coord in block]
		min_x = min(coord[0] for coord in all_cordinates)
		max_x = max(coord[0] for coord in all_cordinates)
		min_y = min(coord[1] for coord in all_cordinates)
		max_y = max(coord[1] for coord in all_cordinates)

		fig, ax = None, None
		colors = ['red', 'blue', 'green', 'orange']
		
		for i, block in enumerate(df2_blocks):
			# routes = get_precise_routes(ordered_coordinates2[i])
			edges_gdf2, nodes2 = build_geodataframes(G2[i], pos2[i], filtered_towns2[i], filtered_coordinates2[i])
			fig, ax = plot_graph(nodes2, edges_gdf2, min_x, max_x, min_y, max_y, ordered_coordinates2[i], ax=ax, color=colors[i])

		# plot_graph(nodes2, edges_gdf2, min_x, max_x, min_y, max_y, optimized_tour2, pos2)
		plt.xlabel('Longitude')
		plt.ylabel('Latitude')
		plt.title('Graph of Towns with TSP Tour')
		# plt.legend()
		plt.show()

	# town coordinates by block, town names by block, town names by day by block, total days to complete Lot
	return ordered_coordinates2, tours2, tours_divs2, sum([len(t) for t in tours_divs2])
