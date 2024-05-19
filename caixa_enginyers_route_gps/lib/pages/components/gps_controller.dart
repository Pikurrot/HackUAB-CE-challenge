

import 'package:caixa_enginyers_route_gps/providers/gps.dart';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

class GpsControllerWidget extends StatelessWidget {
  const GpsControllerWidget({super.key});

  void moveGps(BuildContext context, Vector2 direction) {
    GPSProvider gpsProvider = Provider.of<GPSProvider>(context, listen: false);
    LatLng pos = gpsProvider.currentPosition;
    const double mult = 0.0001;

    LatLng nextPos = LatLng(pos.latitude + direction.y * mult, pos.longitude + direction.x * mult);

    gpsProvider.update(nextPos);
  }

  void setGps(BuildContext context, LatLng nextPos) {
    Provider.of<GPSProvider>(context, listen: false).update(nextPos);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(children: [
          ElevatedButton(onPressed: () {setGps(context, const LatLng(41.73187, 2.26860));}, child: const Text("Reset")),
          ElevatedButton(onPressed: () {moveGps(context, Vector2(0, 1));}, child: const Icon(Icons.arrow_upward))
        ],),
        Row(children: [
          ElevatedButton(onPressed: () {moveGps(context, Vector2(-1, 0));}, child: const Icon(Icons.arrow_left)),
          ElevatedButton(onPressed: () {moveGps(context, Vector2(0, -1));}, child: const Icon(Icons.arrow_downward)),
          ElevatedButton(onPressed: () {moveGps(context, Vector2(1, 0));}, child: const Icon(Icons.arrow_right))
          
        ],)
      ],
    );
  }
}

class Vector2 {
  double x;
  double y;
  Vector2(this.x, this.y);
}