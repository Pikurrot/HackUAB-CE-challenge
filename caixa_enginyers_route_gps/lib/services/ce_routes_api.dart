

import 'package:caixa_enginyers_route_gps/services/models/test_status.dart';
import 'package:http/http.dart' as http;


class CeRoutesApi {
  static const String api = 'http://172.20.10.2:5000';

  static Future<List<PathModel>> getTowns() async {
    http.Response status = await fetchTowns();
    List<PathModel> sms = PathModel.fromRawJsonList(status.body);

    return sms;
  }

  static Future<http.Response> fetchTowns() {
    return http.get(Uri.parse("$api/lot/2"));
  }

  static Future<List<PathModel>> getPath() async {
    http.Response status = await fetchTowns();
    List<PathModel> sms = PathModel.fromRawJsonList(status.body);

    return sms;
  }

  static Future<http.Response> fetchPath() {
    return http.get(Uri.parse("$api/lot/2/day/"));
  }
}