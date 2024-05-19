


import 'package:caixa_enginyers_route_gps/pages/components/gps_controller.dart';
import 'package:caixa_enginyers_route_gps/pages/components/map_component.dart';
import 'package:caixa_enginyers_route_gps/pages/stop_page.dart';
import 'package:caixa_enginyers_route_gps/providers/gps.dart';
import 'package:caixa_enginyers_route_gps/utils/calculate_routes.dart';
import 'package:caixa_enginyers_route_gps/providers/current_map.dart';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {

  void initGps(BuildContext context) {
    GPSProvider gpsProvider = Provider.of<GPSProvider>(context, listen: false);
    gpsProvider.currentPosition = const LatLng(41.73187, 2.26860);
  }

  void loadMap(BuildContext context) async {
    CurrentMap currentMap = Provider.of<CurrentMap>(context, listen: false);
    currentMap.changeRoutes(
      await CalculateRoutes().calculateRoute([], const LatLng(0, 0))
    );
    currentMap.updateCurrentPositionReturnIfRecalculateNeeded(
      const LatLng(41.73187, 2.26860)
    );
    currentMap.tryStop();
    setState(() {
      loading = false;
    });
  }

  void tryStop(BuildContext context) {
    CurrentMap currentMap = Provider.of<CurrentMap>(context, listen: false);
    currentMap.tryStop();
  }

  bool loading = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((timeStamp) {
      initGps(context);
      loadMap(context);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(appBar: AppBar(title: const Text("Home Page")),
      body: Center(
        child: Stack(
          alignment: AlignmentDirectional.bottomEnd,
          children: [
            if (!loading) const MapComponent(),
            Column(
              children: [
                ElevatedButton(
                  child: const Text('Try Stop'),
                  onPressed: () {
                    tryStop(context);
                  }
                ),
                ElevatedButton(
                  child: const Text('Parada de Servicio'),
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (context) => const StopPage(stopType: StopType.service,)),
                    );
                  }
                ),
                ElevatedButton(
                  child: const Text('Descanso'),
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (context) => const StopPage(stopType: StopType.rest,)),
                    );
                  }
                ),
                if (!loading) const GpsControllerWidget()
              ],
            )
          ],
        )
      )
    );
  }
}
