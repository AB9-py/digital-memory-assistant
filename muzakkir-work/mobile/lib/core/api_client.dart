import 'package:dio/dio.dart';

import 'api_config.dart';

/// Factory creating a configured [Dio] instance for the given [baseUrl].
/// Avoid hardcoding 'Content-Type' in BaseOptions headers so that Dio
/// dynamically sets multipart/form-data boundaries for file uploads
/// and application/json for normal requests.
Dio createApiClient(String baseUrl) {
  return Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
    ),
  );
}

final apiClient = createApiClient(defaultApiBaseUrl());
