import 'package:dio/dio.dart';

import 'api_config.dart';

final apiClient = Dio(
  BaseOptions(
    baseUrl: defaultApiBaseUrl(),
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
    sendTimeout: const Duration(seconds: 10),
    headers: {'Content-Type': 'application/json'},
  ),
);
