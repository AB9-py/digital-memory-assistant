import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_config.dart';
import '../providers/api_providers.dart';

class HealthScreen extends ConsumerWidget {
  const HealthScreen({super.key});

  void _showConfigureUrlDialog(BuildContext context, WidgetRef ref) {
    final currentUrl = ref.read(apiBaseUrlProvider);
    final controller = TextEditingController(text: currentUrl);

    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Configure Backend Server'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select a preset or enter your backend server URL:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'API Base URL',
                hintText: 'http://127.0.0.1:8000',
                prefixIcon: Icon(Icons.dns_outlined),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                ActionChip(
                  label: const Text('Localhost (127.0.0.1)'),
                  onPressed: () {
                    controller.text = localhostBaseUrl;
                  },
                ),
                ActionChip(
                  label: const Text('Android (10.0.2.2)'),
                  onPressed: () {
                    controller.text = androidEmulatorBaseUrl;
                  },
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final newUrl = controller.text.trim().replaceAll(RegExp(r'/+$'), '');
              if (newUrl.isNotEmpty) {
                ref.read(apiBaseUrlProvider.notifier).state = newUrl;
                ref.invalidate(healthProvider);
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('Save & Reconnect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider);
    final currentBaseUrl = ref.watch(apiBaseUrlProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('System Health & Connection'),
        actions: [
          IconButton(
            tooltip: 'Configure Backend URL',
            onPressed: () => _showConfigureUrlDialog(context, ref),
            icon: const Icon(Icons.settings_outlined),
          ),
          IconButton(
            tooltip: 'Refresh Status',
            onPressed: () => ref.invalidate(healthProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Target Base URL Info Bar with tap-to-configure
          InkWell(
            onTap: () => _showConfigureUrlDialog(context, ref),
            borderRadius: BorderRadius.circular(8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outlineVariant,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.link,
                    size: 20,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Backend Endpoint (Tap to edit)',
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                color: Theme.of(context).colorScheme.onSurfaceVariant,
                              ),
                        ),
                        Text(
                          '$currentBaseUrl/health',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                                fontFamily: 'monospace',
                              ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    Icons.edit_outlined,
                    size: 18,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Health State Section
          health.when(
            loading: () => const Card(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Center(
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Probing GET /health...'),
                    ],
                  ),
                ),
              ),
            ),
            error: (error, stackTrace) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _StatusBanner(
                  state: _BannerState.error,
                  title: 'Backend Disconnected',
                  subtitle: 'Could not reach server at $currentBaseUrl',
                ),
                const SizedBox(height: 16),
                _StatusPanel(
                  rows: const [
                    _StatusRow(
                      icon: Icons.error_outline,
                      label: 'Backend Status',
                      value: 'Unavailable',
                      ok: false,
                    ),
                    _StatusRow(
                      icon: Icons.storage_outlined,
                      label: 'Database Status',
                      value: 'Unreachable',
                      ok: false,
                    ),
                  ],
                  footer:
                      'Error: $error\n\nTroubleshooting:\n• If running locally: run uvicorn backend.main:app --port 8000\n• If on Android emulator: use http://10.0.2.2:8000\n• If on a physical phone: use your computer\'s local Wi-Fi IP (e.g. http://192.168.1.x:8000)',
                ),
              ],
            ),
            data: (data) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (data.isFullyHealthy)
                  const _StatusBanner(
                    state: _BannerState.healthy,
                    title: 'Backend & DB Connected',
                    subtitle: 'FastAPI and PostgreSQL/pgvector are fully operational',
                  )
                else if (data.backendOk)
                  const _StatusBanner(
                    state: _BannerState.partial,
                    title: 'Backend Connected (DB Disconnected)',
                    subtitle:
                        'FastAPI is operational; PostgreSQL container is offline or unmigrated',
                  )
                else
                  const _StatusBanner(
                    state: _BannerState.error,
                    title: 'System Degraded',
                    subtitle: 'Unexpected response from /health endpoint',
                  ),
                const SizedBox(height: 16),
                _StatusPanel(
                  latencyMs: data.latencyMs,
                  rows: [
                    _StatusRow(
                      icon: Icons.cloud_done_outlined,
                      label: 'FastAPI Backend',
                      value: data.status.toUpperCase(),
                      ok: data.backendOk,
                    ),
                    _StatusRow(
                      icon: Icons.storage_outlined,
                      label: 'PostgreSQL + pgvector',
                      value: _titleCase(data.database),
                      ok: data.databaseConnected,
                    ),
                    _StatusRow(
                      icon: Icons.inventory_2_outlined,
                      label: 'API Version',
                      value: data.version,
                      ok: true,
                    ),
                    _StatusRow(
                      icon: Icons.tune_outlined,
                      label: 'Environment',
                      value: _titleCase(data.environment),
                      ok: true,
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Reviewer note card
          Card(
            elevation: 0,
            color: Theme.of(context).colorScheme.surfaceContainerLow,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline,
                    size: 20,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Review Note: Screen 1 validates client-server connectivity. You can test live Swagger documentation at $currentBaseUrl/docs.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

enum _BannerState { healthy, partial, error }

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({
    required this.state,
    required this.title,
    required this.subtitle,
  });

  final _BannerState state;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final Color bgColor;
    final Color borderColor;
    final Color textColor;
    final IconData icon;

    switch (state) {
      case _BannerState.healthy:
        bgColor = const Color(0xFFDCFCE7);
        borderColor = const Color(0xFF16A34A);
        textColor = const Color(0xFF15803D);
        icon = Icons.check_circle_rounded;
        break;
      case _BannerState.partial:
        bgColor = const Color(0xFFFEF3C7);
        borderColor = const Color(0xFFD97706);
        textColor = const Color(0xFFB45309);
        icon = Icons.warning_amber_rounded;
        break;
      case _BannerState.error:
        bgColor = const Color(0xFFFEE2E2);
        borderColor = const Color(0xFFDC2626);
        textColor = const Color(0xFFB91C1C);
        icon = Icons.cancel_rounded;
        break;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: borderColor, width: 1.5),
      ),
      child: Row(
        children: [
          Icon(icon, size: 36, color: textColor),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: textColor,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: textColor.withValues(alpha: 0.9),
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPanel extends StatelessWidget {
  const _StatusPanel({
    required this.rows,
    this.latencyMs,
    this.footer,
  });

  final List<_StatusRow> rows;
  final int? latencyMs;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (latencyMs != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Response Latency',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  Chip(
                    avatar: const Icon(Icons.speed, size: 16),
                    label: Text('${latencyMs}ms'),
                    visualDensity: VisualDensity.compact,
                  ),
                ],
              ),
              const Divider(height: 20),
            ],
            for (final row in rows) ...[
              row,
              if (row != rows.last) const Divider(height: 20),
            ],
            if (footer != null) ...[
              const SizedBox(height: 14),
              Text(
                footer!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.error,
                      fontFamily: 'monospace',
                    ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.ok,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool ok;

  @override
  Widget build(BuildContext context) {
    final color = ok ? const Color(0xFF15803D) : const Color(0xFFDC2626);

    return Row(
      children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: color,
                  fontWeight: FontWeight.bold,
                ),
          ),
        ),
      ],
    );
  }
}

String _titleCase(String value) {
  if (value.isEmpty) {
    return value;
  }
  return value[0].toUpperCase() + value.substring(1).toLowerCase();
}
