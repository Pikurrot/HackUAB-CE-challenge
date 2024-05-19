

import 'package:caixa_enginyers_route_gps/pages/map_page.dart';
import 'package:flutter/material.dart';

enum StopType {
  service,
  rest,
}

class StopPage extends StatelessWidget {
  const StopPage({super.key, required this.stopType, required this.isClose});

  final StopType stopType;
  final bool isClose;

  @override
  Widget build(BuildContext context) {
    StopType changeType = switch (stopType) {
      StopType.service => StopType.rest,
      StopType.rest => StopType.service
    };
    String changeTypeString = switch (changeType) {
      StopType.service => isClose ? "Parada de Servicio" : "Deshabilitada la parada de servicio",
      StopType.rest => "Descanso"
    };

    return Scaffold(appBar: AppBar(title: const Text("Home Page")),
      body: Center(
        child: Column(
          children: [
            ElevatedButton(
              child: const Text("Continuar viaje"),
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => const MapPage()),
                  );
              },
            ),
            ElevatedButton(
              onPressed: (isClose) ? () {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => StopPage(stopType: changeType, isClose: isClose)),
                );
              } : null,
              child: Text(changeTypeString),
            ),
          ],
        )
      )
    );
  }
}