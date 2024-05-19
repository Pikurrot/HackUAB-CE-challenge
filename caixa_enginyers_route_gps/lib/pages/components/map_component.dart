


import 'package:caixa_enginyers_route_gps/providers/current_map.dart';
import 'package:caixa_enginyers_route_gps/providers/gps.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

class MapComponent extends StatefulWidget {
  const MapComponent({super.key});

  @override
  State<MapComponent> createState() => _MapComponentState();
}

class _MapComponentState extends State<MapComponent> {

  Widget getPolylineLayer(CurrentMap currentMap) {
    Polyline? visited = (currentMap.visitedPath.isEmpty) ? null : Polyline(
      points: currentMap.visitedPath,
      color: Colors.grey,
      strokeWidth: 10,
    );
    Polyline? notVisited = (currentMap.notVisitedPath.isEmpty) ? null : Polyline(
      points: currentMap.notVisitedPath,
      color: Colors.blue,
      strokeWidth: 10,
    );

    List<Polyline> path = [
      visited,
      notVisited
    ].whereType<Polyline>().toList();
    if (path.isEmpty) return Container( color: Colors.red, width: 40, height: 40,);
    return 
      PolylineLayer(polylines: path);
  }

  MarkerLayer getMarkerLayer(CurrentMap currentMap) {
    List<Marker> towns = currentMap.visitedTown.map((town) => Marker(
      point: town.position,
      width: 50,
      height: 50,
      rotate: true,
      child: Container(
        color: Colors.grey,
        child: const Icon(Icons.location_city, color: Colors.black, size: 40)
      )
    )).toList();
    towns.addAll(currentMap.nonVisitedTown.map((town)=> Marker(
      point: town.position,
      width: 50,
      height: 50,
      rotate: true,
      child: Container(
        color: Colors.blue,
        child: const Icon(Icons.location_city, color: Colors.black, size: 40)
      )
    )));

    return MarkerLayer(markers: towns);
  }

  MarkerLayer getPositionLayer(GPSProvider gpsProvider) {
    return MarkerLayer(markers: [
      Marker(
        point: gpsProvider.currentPosition,
        width: 60,
        height: 60,
        rotate: true,
        child: const Icon(Icons.location_on, size: 50, color: Colors.red),
      )
    ],);
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((timeStamp) {
        Provider.of<GPSProvider>(context, listen: false).onChange = (LatLng currentPosition) {
          mapController.move(currentPosition, 17);
          Provider.of<CurrentMap>(context, listen: false).updateCurrentPositionReturnIfRecalculateNeeded(currentPosition);
        };
    });
  }

  final mapController = MapController();

  @override
  Widget build(BuildContext context) {
    CurrentMap currentMap = Provider.of<CurrentMap>(context, listen: false);
    return FlutterMap(
      options: MapOptions(
        initialCenter: currentMap.currentPosition,
        initialZoom: 17
      ),
      mapController: mapController,
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.caixa_enginyers_route_gps.app',
        ),
        RichAttributionWidget(attributions: [
          TextSourceAttribution(
            'OpenStreetMap contributors',
            onTap: () => launchUrl(Uri.parse('https://openstreetmap.org/copyright'))
          )
        ]),
        Consumer<CurrentMap>(
          builder: (context, currentMap, child) {
            Widget polylineLayer = getPolylineLayer(currentMap);
            return polylineLayer;
          }
        ),
        Consumer<CurrentMap>(
          builder: (context, currentMap, child) {
            return getMarkerLayer(currentMap);
          }
        ),
        Consumer<GPSProvider>(
          builder: (context, gpsProvider, child) {
            return getPositionLayer(gpsProvider);
          },
        )
      ]
    );
  }
}