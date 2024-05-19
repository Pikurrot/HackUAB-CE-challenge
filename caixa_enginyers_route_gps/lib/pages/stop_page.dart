

import 'package:caixa_enginyers_route_gps/pages/map_page.dart';
import 'package:flutter/material.dart';

enum StopType {
  service,
  rest,
}

class StopPage extends StatelessWidget {
  const StopPage({super.key, required this.stopType});

  final StopType stopType;

  @override
  Widget build(BuildContext context) {
    StopType changeType = switch (stopType) {
      StopType.service => StopType.rest,
      StopType.rest => StopType.service
    };
    String changeTypeString = switch (changeType) {
      StopType.service => "Parada de Servicio",
      StopType.rest => "Descanso"
    };

    return Scaffold(appBar: AppBar(title: const Text("Home Page")),
      body: Center(
        child: Column(
          children: [
            ElevatedButton(
              child: Text("Resumir"),
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => const MapPage()),
                  );
              },
            ),
            ElevatedButton(
              child: Text(changeTypeString),
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => StopPage(stopType: changeType,)),
                  );
              },
            ),
          ],
        )
      )
    );
  }
}