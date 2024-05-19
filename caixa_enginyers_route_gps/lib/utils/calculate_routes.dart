import 'package:latlong2/latlong.dart';
import 'package:caixa_enginyers_route_gps/utils/routes_types.dart';

class CalculateRoutes {
  Future<MapRoute> calculateRoute(List<String> stopsDone, LatLng currentPosition) async {

    // List<PathModel> towns = await CeRoutesApi.getTowns();

    // towns.map((town) => 
    //   Stop(position: LatLng(town.latitude, town.longitude), big:false, visited:false)
    // ).toList();

    return MapRoute(
      pathList: const [
        [LatLng(41.73187, 2.26860), LatLng(41.73282,2.26870), LatLng(41.73409,2.26781)],
        [LatLng(41.73409,2.26781), LatLng(41.73412,2.26915)],
        [LatLng(41.73412,2.26915), LatLng(41.73530, 2.26907), LatLng(41.73647, 2.26873), LatLng(41.73762, 2.26738)],
      ],
      stopList: [
        Stop(position: const LatLng(41.73187, 2.26860), big: false, visited: false),
        Stop(position: const LatLng(41.73409, 2.26781), big: false, visited: false),
        Stop(position: const LatLng(41.73412, 2.26915), big: false, visited: false),
        Stop(position: const LatLng(41.73762, 2.26738), big: false, visited: false)
      ]
    );
  }
}