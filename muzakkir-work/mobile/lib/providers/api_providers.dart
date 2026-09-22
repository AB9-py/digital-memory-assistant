import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../models/health_status.dart';
import '../models/search_models.dart';

const demoUserId = '00000000-0000-0000-0000-000000000001';

final dioProvider = Provider<Dio>((ref) => apiClient);

final healthProvider = FutureProvider.autoDispose<HealthStatus>((ref) async {
  final dio = ref.watch(dioProvider);
  final stopwatch = Stopwatch()..start();
  final response = await dio.get<Map<String, dynamic>>('/health');
  stopwatch.stop();
  return HealthStatus.fromJson(
    response.data ?? const <String, dynamic>{},
    latencyMs: stopwatch.elapsedMilliseconds,
  );
});

final searchControllerProvider =
    AsyncNotifierProvider<SearchController, SearchResponse?>(SearchController.new);

class SearchController extends AsyncNotifier<SearchResponse?> {
  @override
  Future<SearchResponse?> build() async => null;

  Future<void> search({
    required String query,
    String userId = demoUserId,
    int topK = 5,
    double minSimilarity = 0.2,
  }) async {
    final trimmedQuery = query.trim();
    if (trimmedQuery.isEmpty) {
      state = const AsyncData(null);
      return;
    }

    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final dio = ref.read(dioProvider);
      final payload = SearchRequest(
        query: trimmedQuery,
        userId: userId,
        topK: topK,
        minSimilarity: minSimilarity,
      );
      final response = await dio.post<Map<String, dynamic>>(
        '/api/v1/memories/search',
        data: payload.toJson(),
      );
      return SearchResponse.fromJson(response.data ?? const <String, dynamic>{});
    });
  }
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------

class UploadResult {
  final String memoryId;
  final String filename;
  final String status;

  const UploadResult({
    required this.memoryId,
    required this.filename,
    required this.status,
  });
}

final uploadControllerProvider =
    AsyncNotifierProvider<UploadController, UploadResult?>(UploadController.new);

class UploadController extends AsyncNotifier<UploadResult?> {
  @override
  Future<UploadResult?> build() async => null;

  void reset() => state = const AsyncData(null);

  Future<void> upload({
    required PlatformFile file,
    String userId = demoUserId,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final dio = ref.read(dioProvider);
      final FormData formData;
      final path = file.path;
      if (path != null) {
        formData = FormData.fromMap({
          'file': await MultipartFile.fromFile(path, filename: file.name),
        });
      } else {
        // Web fallback — bytes are always available on web
        formData = FormData.fromMap({
          'file': MultipartFile.fromBytes(file.bytes!, filename: file.name),
        });
      }
      final response = await dio.post<Map<String, dynamic>>(
        '/api/v1/memories/upload',
        queryParameters: {'user_id': userId},
        data: formData,
        options: Options(
          receiveTimeout: const Duration(seconds: 60),
          sendTimeout: const Duration(seconds: 30),
        ),
      );
      final data = response.data!;
      return UploadResult(
        memoryId: data['id'] as String,
        filename: data['original_filename'] as String,
        status: data['status'] as String,
      );
    });
  }
}
