
import 'package:latlong2/latlong.dart';

class MapRoute {
  final List<List<LatLng>> pathList;
  final List<Stop> stopList;

  const MapRoute({required this.pathList, required this.stopList});
}

class Stop {
  final LatLng position;
  final bool big;
  bool visited;
  
  Stop({required this.position, required this.big, required this.visited});
}