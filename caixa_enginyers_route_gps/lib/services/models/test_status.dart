import 'dart:convert';

class PathModel {
    double latitude;
    double longitude;

    PathModel({
        required this.latitude,
        required this.longitude,
    });

    factory PathModel.fromRawJson(String str) => PathModel.fromJson(json.decode(str));
    static List<PathModel> fromRawJsonList(String str) {
      List<dynamic> list = json.decode(str);
      List<PathModel> values = list.map((val) => PathModel.fromJson(val)).toList();
      return values;
    }

    String toRawJson() => json.encode(toJson());

    factory PathModel.fromJson(List<dynamic> json) => PathModel(
        latitude: json[0],
        longitude: json[1],
    );

    List<dynamic> toJson() => [latitude, longitude];
}
