import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://192.168.1.36:5000';
  // ini ip laptop Tio biar bisa connect ke API

  static Future<Map<String, dynamic>> getLatest() async {
    final res = await http.get(Uri.parse('$baseUrl/api/latest'));
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load latest');
  }

  static Future<List<dynamic>> getHistory() async {
    final res = await http.get(Uri.parse('$baseUrl/api/history'));
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as List<dynamic>;
    }
    throw Exception('Failed to load history');
  }

  static Future<Map<String, dynamic>> getAftershock() async {
    final res = await http.get(Uri.parse('$baseUrl/api/aftershock'));
    if (res.statusCode == 200) {
      return jsonDecode(res.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load aftershock');
  }

  static Future<bool> sendControl(String command) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/control'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'command': command}),
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      return data['status'] == 'success';
    }
    return false;
  }
}
