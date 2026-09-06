class HealthStatus {
  const HealthStatus({
    required this.status,
    required this.database,
    required this.version,
    required this.environment,
    this.latencyMs,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json, {int? latencyMs}) {
    return HealthStatus(
      status: json['status'] as String? ?? 'unknown',
      database: json['database'] as String? ?? 'unknown',
      version: json['version'] as String? ?? 'unknown',
      environment: json['environment'] as String? ?? 'unknown',
      latencyMs: latencyMs,
    );
  }

  final String status;
  final String database;
  final String version;
  final String environment;
  final int? latencyMs;

  bool get backendOk => status.toLowerCase() == 'ok';
  bool get databaseConnected => database.toLowerCase() == 'connected';
  bool get isFullyHealthy => backendOk && databaseConnected;
}
