import 'dart:convert';

import 'package:caixa_enginyers_route_gps/api_key.dart';
import 'package:caixa_enginyers_route_gps/services/models/test_status.dart';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';


class TomTomApi {
  static const String api = 'https://api.tomtom.com/';
  static const String apiKey = tomTomApiKey;

  static Future<List<LatLng>> getTomTomRoute(List<LatLng> route) async {
    http.Response status = await fetchTomTomRoute(route);
    List<PathModel> sms = PathModel.fromRawJsonList(status.body);

    Map<String, dynamic> routes = json.decode(status.body);
    List<dynamic> routeList = routes["routes"];
    List<LatLng> points = routeList.map((val) {
      List<dynamic> legList = val["legs"];
      return legList.map((leg) {
        List<dynamic> points = leg["points"];
        return points.map((point) =>
          LatLng(point["latitude"], point["longitude"])
        ).toList();
      }).expand((i) => i).toList();
    }).expand((i) => i).toList();

    return points;
  }

  static Future<http.Response> fetchTomTomRoute(List<LatLng> route) {
    String locations = route.map((node) => "${node.latitude},${node.longitude}").toString();

    return http.get(Uri.parse("$api/routing/1/calculateRoute/$locations/json"));
  }
}