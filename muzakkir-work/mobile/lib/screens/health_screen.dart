import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_config.dart';
import '../providers/api_providers.dart';

class HealthScreen extends ConsumerWidget {
  const HealthScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Backend Connection'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(healthProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            defaultApiBaseUrl(),
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 16),
          health.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stackTrace) => _StatusPanel(
              rows: [
                _StatusRow(
                  icon: Icons.error_outline,
                  label: 'Backend Status',
                  value: 'Unavailable',
                  ok: false,
                ),
                _StatusRow(
                  icon: Icons.storage_outlined,
                  label: 'Database Status',
                  value: 'Unknown',
                  ok: false,
                ),
              ],
              footer: error.toString(),
            ),
            data: (data) => _StatusPanel(
              rows: [
                _StatusRow(
                  icon: Icons.cloud_done_outlined,
                  label: 'Backend Status',
                  value: data.status.toUpperCase(),
                  ok: data.backendOk,
                ),
                _StatusRow(
                  icon: Icons.storage_outlined,
                  label: 'Database Status',
                  value: _titleCase(data.database),
                  ok: data.databaseConnected,
                ),
                _StatusRow(
                  icon: Icons.inventory_2_outlined,
                  label: 'Version',
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
          ),
        ],
      ),
    );
  }
}

class _StatusPanel extends StatelessWidget {
  const _StatusPanel({
    required this.rows,
    this.footer,
  });

  final List<_StatusRow> rows;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final row in rows) ...[
              row,
              if (row != rows.last) const Divider(height: 24),
            ],
            if (footer != null) ...[
              const SizedBox(height: 16),
              Text(
                footer!,
                style: Theme.of(context).textTheme.bodySmall,
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
    final color = ok ? Colors.green.shade700 : Colors.red.shade700;

    return Row(
      children: [
        Icon(icon, color: color),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        Text(
          value,
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(color: color, fontWeight: FontWeight.w700),
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
