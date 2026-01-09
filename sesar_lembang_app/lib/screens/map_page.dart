import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapPage extends StatelessWidget {
  const MapPage({super.key});

  // Koordinat contoh, ganti dengan koordinat sensor sebenarnya
  static final LatLng lembang = LatLng(-6.8190, 107.6170);
  static final LatLng parongpong = LatLng(-6.8285, 107.5950);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050816),
      appBar: AppBar(
        backgroundColor: const Color(0xFF050816),
        elevation: 0,
        title: const Text('Peta Sensor'),
      ),
      body: FlutterMap(
        options: MapOptions(
          initialCenter: lembang,
          initialZoom: 13,
          maxZoom: 18,
          minZoom: 10,
        ),
        children: [
          // tile dasar OpenStreetMap
          TileLayer(
            urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            userAgentPackageName: 'com.example.sesar_lembang_app',
          ),
          // marker sensor
          MarkerLayer(
            markers: [
              Marker(
                point: lembang,
                width: 80,
                height: 80,
                child: _SensorMarkerWidget(
                  label: 'Lembang',
                  color: Colors.lightBlueAccent,
                ),
              ),
              Marker(
                point: parongpong,
                width: 80,
                height: 80,
                child: _SensorMarkerWidget(
                  label: 'Parongpong',
                  color: Colors.pinkAccent,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SensorMarkerWidget extends StatelessWidget {
  final String label;
  final Color color;

  const _SensorMarkerWidget({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.7),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            label,
            style: const TextStyle(fontSize: 10, color: Colors.white),
          ),
        ),
        const SizedBox(height: 4),
        Icon(Icons.location_on, color: color, size: 32),
      ],
    );
  }
}
