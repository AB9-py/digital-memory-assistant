class MemoryItem {
  const MemoryItem({
    required this.id,
    required this.userId,
    required this.originalFilename,
    required this.fileType,
    required this.filePath,
    required this.fileSizeBytes,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.metaInfo = const {},
  });

  factory MemoryItem.fromJson(Map<String, dynamic> json) {
    return MemoryItem(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      originalFilename: json['original_filename'] as String? ?? 'Untitled document',
      fileType: json['file_type'] as String? ?? 'UNKNOWN',
      filePath: json['file_path'] as String? ?? '',
      fileSizeBytes: json['file_size_bytes'] as int? ?? 0,
      status: json['status'] as String? ?? 'unknown',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      metaInfo: (json['meta_info'] as Map<String, dynamic>?) ?? const {},
    );
  }

  final String id;
  final String userId;
  final String originalFilename;
  final String fileType;
  final String filePath;
  final int fileSizeBytes;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final Map<String, dynamic> metaInfo;

  String get formattedFileSize {
    if (fileSizeBytes <= 0) return '0 B';
    if (fileSizeBytes < 1024) return '$fileSizeBytes B';
    if (fileSizeBytes < 1024 * 1024) {
      return '${(fileSizeBytes / 1024).toStringAsFixed(1)} KB';
    }
    return '${(fileSizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  bool get isPdf =>
      fileType.toUpperCase() == 'PDF' ||
      originalFilename.toLowerCase().endsWith('.pdf');

  bool get isImage =>
      fileType.toUpperCase() == 'IMAGE' ||
      originalFilename.toLowerCase().endsWith('.png') ||
      originalFilename.toLowerCase().endsWith('.jpg') ||
      originalFilename.toLowerCase().endsWith('.jpeg');

  bool get isDocx =>
      fileType.toUpperCase() == 'DOCX' ||
      originalFilename.toLowerCase().endsWith('.docx');

  bool get isProcessed => status.toLowerCase() == 'processed';
  bool get isProcessing => status.toLowerCase() == 'processing';
  bool get isFailed => status.toLowerCase() == 'failed' || status.toLowerCase() == 'rejected';
}

class MemoryListResponse {
  const MemoryListResponse({
    required this.total,
    required this.items,
  });

  factory MemoryListResponse.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? const [];
    return MemoryListResponse(
      total: json['total'] as int? ?? rawItems.length,
      items: rawItems
          .whereType<Map<String, dynamic>>()
          .map(MemoryItem.fromJson)
          .toList(),
    );
  }

  final int total;
  final List<MemoryItem> items;
}
