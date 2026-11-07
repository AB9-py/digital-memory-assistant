import 'api_platform.dart';

const _configuredBaseUrl = String.fromEnvironment('API_BASE_URL');

const localhostBaseUrl = 'http://127.0.0.1:8000';
const androidEmulatorBaseUrl = 'http://10.0.2.2:8000';

String defaultApiBaseUrl() {
  if (_configuredBaseUrl.isNotEmpty) {
    return _configuredBaseUrl;
  }

  if (isAndroidPlatform()) {
    return androidEmulatorBaseUrl;
  }

  return localhostBaseUrl;
}
