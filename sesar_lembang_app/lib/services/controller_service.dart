import 'dart:async';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

class SensorController extends ChangeNotifier {
  Map<String, dynamic>? latest;
  Map<String, dynamic>? aftershock;
  bool isOnline = false;

  String _lastStatus = 'NORMAL';
  Timer? _timer;

  void start() {
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

      // TODO: di sini nanti panggil showQuakeNotification(...)
      if (_lastStatus == 'NORMAL' &&
          (status == 'ALERT' || status == 'WARNING')) {
        // showQuakeNotification('Peringatan Gempa', 'Magnitude ...');
      }

      _lastStatus = status;
      latest = data;
      isOnline = true;
      notifyListeners();
    } catch (_) {
      isOnline = false;
      notifyListeners();
    }
  }

  Future<void> _loadAftershock() async {
    try {
      aftershock = await ApiService.getAftershock();
      notifyListeners();
    } catch (_) {}
  }

  Future<bool> sendCommand(String cmd) async {
    return ApiService.sendControl(cmd);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
