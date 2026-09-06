class SearchRequest {
  const SearchRequest({
    required this.query,
    required this.userId,
    this.topK = 5,
    this.minSimilarity = 0.2,
  });

  final String query;
  final String userId;
  final int topK;
  final double minSimilarity;

  Map<String, dynamic> toJson() {
    return {
      'query': query,
      'user_id': userId,
      'top_k': topK,
      'min_similarity': minSimilarity,
    };
  }
}

class SearchResponse {
  const SearchResponse({
    required this.query,
    required this.totalResults,
    required this.results,
  });

  factory SearchResponse.fromJson(Map<String, dynamic> json) {
    final rawResults = json['results'] as List<dynamic>? ?? const [];
    return SearchResponse(
      query: json['query'] as String? ?? '',
      totalResults: json['total_results'] as int? ?? rawResults.length,
      results: rawResults
          .whereType<Map<String, dynamic>>()
          .map(ChunkSearchResult.fromJson)
          .toList(),
    );
  }

  final String query;
  final int totalResults;
  final List<ChunkSearchResult> results;
}

class ChunkSearchResult {
  const ChunkSearchResult({
    required this.chunkId,
    required this.memoryId,
    required this.originalFilename,
    required this.content,
    required this.chunkIndex,
    required this.similarityScore,
    this.pageNumber,
    this.chunkMetadata = const {},
  });

  factory ChunkSearchResult.fromJson(Map<String, dynamic> json) {
    return ChunkSearchResult(
      chunkId: json['chunk_id'] as String? ?? '',
      memoryId: json['memory_id'] as String? ?? '',
      originalFilename: json['original_filename'] as String? ?? 'Unknown document',
      content: json['content'] as String? ?? '',
      pageNumber: json['page_number'] as int?,
      chunkIndex: json['chunk_index'] as int? ?? 0,
      similarityScore: (json['similarity_score'] as num?)?.toDouble() ?? 0,
      chunkMetadata: (json['chunk_metadata'] as Map<String, dynamic>?) ?? const {},
    );
  }

  final String chunkId;
  final String memoryId;
  final String originalFilename;
  final String content;
  final int? pageNumber;
  final int chunkIndex;
  final double similarityScore;
  final Map<String, dynamic> chunkMetadata;
}
