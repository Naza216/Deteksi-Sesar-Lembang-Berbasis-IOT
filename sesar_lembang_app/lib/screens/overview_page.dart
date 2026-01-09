import 'dart:async';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../main.dart';

class OverviewPage extends StatefulWidget {
  const OverviewPage({super.key});

  @override
  State<OverviewPage> createState() => _OverviewPageState();
}

class _OverviewPageState extends State<OverviewPage> {
  Map<String, dynamic>? latest;
  Map<String, dynamic>? aftershock;
  bool isOnline = false;
  String _lastStatus = 'NORMAL';
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadAll();
    _timer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _loadLatestOnly(),
    );
  }

  Future<void> _loadAll() async {
    await Future.wait([_loadLatestOnly(), _loadAftershock()]);
  }

  Future<void> _loadLatestOnly() async {
    try {
      final data = await ApiService.getLatest();
      final status = (data['status'] ?? 'NORMAL') as String;

      if (_lastStatus == 'NORMAL' &&
          (status == 'ALERT' || status == 'WARNING')) {
        final mag = (data['magnitude_g'] ?? 0.0) as num;
        await showQuakeNotification(
          'Peringatan Gempa Terdeteksi',
          'Magnitude ${mag.toStringAsFixed(2)} g di sensor Lembang (status $status).',
        );
      }

      _lastStatus = status;

      setState(() {
        latest = data;
        isOnline = true;
      });
    } catch (_) {
      setState(() => isOnline = false);
    }
  }

  Future<void> _loadAftershock() async {
    try {
      final data = await ApiService.getAftershock();
      setState(() => aftershock = data);
    } catch (_) {}
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  BoxDecoration _glassDecoration() {
    return BoxDecoration(
      borderRadius: BorderRadius.circular(18),
      gradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          const Color(0xFF020617).withOpacity(0.9),
          const Color(0xFF020617).withOpacity(0.98),
        ],
      ),
      border: Border.all(
        color: const Color(0xFF1F2937).withOpacity(0.9),
        width: 1,
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withOpacity(0.65),
          offset: const Offset(0, 18),
          blurRadius: 40,
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final status = (latest?['status'] ?? 'NORMAL') as String;
    final magnitude = (latest?['magnitude_g'] ?? 0.0) as num;
    final depthKm = latest?['kedalaman']?.toString() ?? '-';
    final coord = (latest?['koordinat'] ?? '-') as String;

    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      appBar: AppBar(
        title: const Text(
          'DASHBOARD  MONITORING',
          style: TextStyle(
            letterSpacing: 4,
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            onPressed: () {
              // halaman riwayat notifikasi
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadAll,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ringkasan status sistem
              Container(
                decoration: _glassDecoration(),
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 14,
                ),
                margin: const EdgeInsets.only(bottom: 16),
                child: Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: const LinearGradient(
                          colors: [Color(0xFF38BDF8), Color(0xFF0EA5E9)],
                        ),
                      ),
                      child: const Icon(
                        Icons.wifi_tethering,
                        size: 18,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            isOnline ? 'SISTEM TERHUBUNG' : 'SISTEM OFFLINE',
                            style: TextStyle(
                              fontSize: 12,
                              letterSpacing: 2,
                              color: isOnline
                                  ? const Color(0xFF22C55E)
                                  : const Color(0xFFF97373),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Magnitude ${magnitude.toStringAsFixed(2)} g • Kedalaman $depthKm • $coord',
                            style: const TextStyle(
                              fontSize: 11,
                              color: Color(0xFF9CA3AF),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    _StatusChip(status: status),
                  ],
                ),
              ),

              _MapSection(
                decoration: _glassDecoration(),
                sensors: const [
                  _SensorMarker(name: 'Lembang', color: Colors.lightBlueAccent),
                  _SensorMarker(name: 'Parongpong', color: Colors.pinkAccent),
                ],
              ),
              const SizedBox(height: 24),

              const _SectionLabel(text: 'GRAFIK'),
              const SizedBox(height: 12),
              _EventDonutCard(
                decoration: _glassDecoration(),
                total: 20,
                lembang: 12,
                parongpong: 8,
              ),
              const SizedBox(height: 24),

              const _SectionLabel(text: 'JUMLAH SENSOR'),
              const SizedBox(height: 12),
              _SensorListTile(
                decoration: _glassDecoration(),
                name: 'Lembang',
                location: 'Gunung Batu',
                isOnline: isOnline,
                status: status,
                magnitude: magnitude.toStringAsFixed(2),
                onTap: () {
                  // detail sensor
                },
              ),
              const SizedBox(height: 8),
              _SensorListTile(
                decoration: _glassDecoration(),
                name: 'Parongpong',
                location: 'Cihideung',
                isOnline: true,
                status: 'NORMAL',
                magnitude: '0.98',
              ),
              const SizedBox(height: 24),

              Row(
                children: [
                  Expanded(
                    child: _ControlButton(
                      label: 'Test ON',
                      color: Colors.greenAccent,
                      onTap: () {
                        ApiService.sendControl('TEST_ON');
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ControlButton(
                      label: 'Test OFF',
                      color: Colors.blueAccent,
                      onTap: () {
                        ApiService.sendControl('TEST_OFF');
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ControlButton(
                      label: 'Shutdown',
                      color: Colors.redAccent,
                      onTap: () {
                        showDialog(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            title: const Text('Konfirmasi Shutdown'),
                            content: const Text(
                              'Matikan sistem peringatan gempa sekarang?',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.of(ctx).pop(),
                                child: const Text('Batal'),
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.of(ctx).pop();
                                  ApiService.sendControl('SHUTDOWN');
                                },
                                child: const Text('Ya'),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// ----------------- WIDGET KOMPONEN -----------------

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        color: Color(0xFF9CA3AF),
        letterSpacing: 3,
        fontSize: 11,
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip({required this.status});

  Color get _color {
    switch (status.toUpperCase()) {
      case 'WARNING':
        return const Color(0xFFF97316);
      case 'ALERT':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF22C55E);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: _color.withOpacity(0.7)),
        color: _color.withOpacity(0.08),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          color: _color,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}

class _MapSection extends StatelessWidget {
  final List<_SensorMarker> sensors;
  final BoxDecoration decoration;
  const _MapSection({required this.sensors, required this.decoration});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      decoration: decoration,
      padding: const EdgeInsets.all(16),
      child: Stack(
        children: [
          Align(
            alignment: Alignment.center,
            child: Container(height: 2, color: Colors.grey[800]),
          ),
          Align(
            alignment: const Alignment(-0.3, 0.3),
            child: _MapPin(label: sensors[0].name, color: sensors[0].color),
          ),
          Align(
            alignment: const Alignment(0.4, -0.2),
            child: _MapPin(label: sensors[1].name, color: sensors[1].color),
          ),
        ],
      ),
    );
  }
}

class _SensorMarker {
  final String name;
  final Color color;
  const _SensorMarker({required this.name, required this.color});
}

class _MapPin extends StatelessWidget {
  final String label;
  final Color color;
  const _MapPin({required this.label, required this.color});

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
          child: Text(label, style: const TextStyle(fontSize: 10)),
        ),
        const SizedBox(height: 6),
        Icon(Icons.location_on, color: color, size: 28),
      ],
    );
  }
}

class _EventDonutCard extends StatelessWidget {
  final int total;
  final int lembang;
  final int parongpong;
  final BoxDecoration decoration;

  const _EventDonutCard({
    required this.total,
    required this.lembang,
    required this.parongpong,
    required this.decoration,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: decoration,
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          SizedBox(
            height: 120,
            width: 120,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: lembang / total,
                  strokeWidth: 10,
                  backgroundColor: Colors.pinkAccent,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Colors.lightBlueAccent,
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'TOTAL',
                      style: TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                    Text(
                      '$total',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 24),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _LegendRow(
                  color: Colors.lightBlueAccent,
                  label: 'Lembang',
                  value: '$lembang Evt',
                ),
                const SizedBox(height: 8),
                _LegendRow(
                  color: Colors.pinkAccent,
                  label: 'Parongpong',
                  value: '$parongpong Evt',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LegendRow extends StatelessWidget {
  final Color color;
  final String label;
  final String value;

  const _LegendRow({
    required this.color,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(child: Text(label, style: const TextStyle(fontSize: 14))),
        Text(value, style: const TextStyle(fontSize: 14, color: Colors.grey)),
      ],
    );
  }
}

class _SensorListTile extends StatelessWidget {
  final String name;
  final String location;
  final bool isOnline;
  final dynamic magnitude;
  final String status;
  final VoidCallback? onTap;
  final BoxDecoration decoration;

  const _SensorListTile({
    required this.name,
    required this.location,
    required this.isOnline,
    required this.status,
    required this.magnitude,
    required this.decoration,
    this.onTap,
  });

  Color get _statusColor {
    switch (status.toUpperCase()) {
      case 'WARNING':
        return Colors.redAccent;
      case 'ALERT':
        return Colors.orangeAccent;
      default:
        return Colors.greenAccent;
    }
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: decoration,
        child: Row(
          children: [
            Icon(Icons.sensors, color: _statusColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    location,
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  isOnline ? 'ONLINE' : 'OFFLINE',
                  style: TextStyle(
                    color: isOnline ? Colors.greenAccent : Colors.redAccent,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$magnitude g',
                  style: TextStyle(color: _statusColor, fontSize: 12),
                ),
              ],
            ),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }
}

class _ControlButton extends StatelessWidget {
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ControlButton({
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          gradient: LinearGradient(
            colors: [color.withOpacity(0.25), color.withOpacity(0.05)],
          ),
          border: Border.all(color: color.withOpacity(0.65)),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.4),
              blurRadius: 18,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w600,
            fontSize: 13,
            letterSpacing: 0.3,
          ),
        ),
      ),
    );
  }
}
