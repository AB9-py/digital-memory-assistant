class HealthStatus {
  const HealthStatus({
    required this.status,
    required this.database,
    required this.version,
    required this.environment,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      status: json['status'] as String? ?? 'unknown',
      database: json['database'] as String? ?? 'unknown',
      version: json['version'] as String? ?? 'unknown',
      environment: json['environment'] as String? ?? 'unknown',
    );
  }

  final String status;
  final String database;
  final String version;
  final String environment;

  bool get backendOk => status.toLowerCase() == 'ok';
  bool get databaseConnected => database.toLowerCase() == 'connected';
}
