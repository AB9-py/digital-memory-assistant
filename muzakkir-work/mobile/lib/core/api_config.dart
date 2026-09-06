import 'api_platform.dart';

const _configuredBaseUrl = String.fromEnvironment('API_BASE_URL');

String defaultApiBaseUrl() {
  if (_configuredBaseUrl.isNotEmpty) {
    return _configuredBaseUrl;
  }

  if (isAndroidPlatform()) {
    return 'http://10.0.2.2:8000';
  }

  return 'http://127.0.0.1:8000';
}
