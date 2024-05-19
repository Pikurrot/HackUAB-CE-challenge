

import 'dart:collection';
import 'dart:developer';

import 'package:caixa_enginyers_route_gps/utils/routes_types.dart';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';


class CurrentMap extends ChangeNotifier {
  static const double pathNodeLimit = 20; // meters
  static const double stopLimit = 20; // meters
  List<Stop> stopList = [];
  List<List<LatLng>> pathList = [];
  int lastVisitedStop = -1;
  int lastVisitedPathNode = 0;

  LatLng currentPosition = const LatLng(0.0, 0.0);

  UnmodifiableListView<LatLng> get visitedPath {
    try {
      List<List<LatLng>> visitedStops = pathList.take(lastVisitedStop+1).toList();
      visitedStops.last = visitedStops.last.take(lastVisitedPathNode+1).toList();
      return UnmodifiableListView(visitedStops.expand((path) => path).toList());
    } catch (err) {
      (err);
      return UnmodifiableListView([]);
    }
  }

  UnmodifiableListView<LatLng> get notVisitedPath {
    try {
      List<List<LatLng>> nonVisitedStops = pathList.skip(lastVisitedStop).toList();
      nonVisitedStops.first = nonVisitedStops.first.skip(lastVisitedPathNode).toList();
      return UnmodifiableListView(nonVisitedStops.expand((path) => path).toList());
    } catch (err) {
      return UnmodifiableListView([]);
    }
  }

  UnmodifiableListView<Stop> get visitedTown {
    try {
      List<Stop> nonVisitedStops = stopList.take(lastVisitedStop+1).toList();
      return UnmodifiableListView(nonVisitedStops);
    } catch (err) {
      return UnmodifiableListView([]);
    }
  }

  UnmodifiableListView<Stop> get nonVisitedTown {
    try {
      List<Stop> nonVisitedStops = stopList.skip(lastVisitedStop+1).toList();
      return UnmodifiableListView(nonVisitedStops);
    } catch (err) {
      return UnmodifiableListView([]);
    }
  }

  void changeRoutes(MapRoute newRoute) {
    stopList = newRoute.stopList;
    pathList = newRoute.pathList;

    notifyListeners();
  }

  bool updateCurrentPositionReturnIfRecalculateNeeded(LatLng nextPosition) {
    // if (currentPosition == nextPosition) return false;
    currentPosition = nextPosition;
    double minDist = double.infinity;
    int chosenPathNode = 0;
    List<LatLng> list = pathList[(lastVisitedStop == -1) ? 0 : (lastVisitedStop == pathList.length) ? pathList.length-1 : lastVisitedStop];
    for (var i = 0; i < list.length; i++) {
      double dist = const Distance().calculator.distance(nextPosition, list[i]);
      if (dist < minDist) {
        minDist = dist;
        chosenPathNode = i;
      }
    }
    bool returnValue;
    if (minDist > pathNodeLimit) {
      log("NOOOOOOOOOOO ${minDist}");
      returnValue = true;
    } // distance is too large a new path is needed
    else {
      if (chosenPathNode != lastVisitedPathNode) {
        lastVisitedPathNode = chosenPathNode;
      }
      returnValue = false;
    }
    notifyListeners();
    log("update Position");
    log("currentPostion $nextPosition");
    log("Last visited stop $lastVisitedStop");
    log("Last visited pathnode $lastVisitedPathNode");

    return returnValue;
  }

  bool tryStop() {
    double dist = const Distance().calculator.distance(currentPosition, stopList[lastVisitedStop+1].position);

    log("Try the stop");
    log("currentPos $currentPosition, neededPos ${stopList[lastVisitedStop+1].position}");
    log("distance $dist");

    bool result = false;
    if (dist > stopLimit) {
      log("NOOOOOOO");
    } else {
      lastVisitedStop += 1;
      lastVisitedPathNode = 0;
      notifyListeners();
      result = true;
    }
    log("Last visited stop $lastVisitedStop");
    log("Last visited pathnode $lastVisitedPathNode");
    return result;
  }
}