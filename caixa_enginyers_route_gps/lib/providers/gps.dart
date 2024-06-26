import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';

typedef GPSProviderChangeCallback = void Function(LatLng currentPos);

class GPSProvider extends ChangeNotifier {
  LatLng _currentPosition = const LatLng(0, 0);
  bool initialized = false;

  GPSProvider();

  LatLng get currentPosition  => _currentPosition;

  set currentPosition(LatLng p) => _currentPosition = p;

  void update(LatLng position) {
    initialized = true;
    _currentPosition = position;
    onChange?.call(_currentPosition);
    notifyListeners();
  }

  GPSProviderChangeCallback? onChange;
}