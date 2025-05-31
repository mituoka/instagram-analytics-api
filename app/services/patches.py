# """
# テキスト分析サービスのパフォーマンス最適化パッチ
# 大規模データセット処理の効率化とキャッシュ戦略の改善を実装
# """

# from typing import List, Dict, Any
# from collections import Counter
# import os
# import concurrent.futures
# import logging

# logger = logging.getLogger("app")


# def dynamic_cache_ttl(data_size: int) -> int:
#     """
#     データ量に応じて動的にキャッシュ時間を決定

#     Args:
#         data_size: データの量（件数）

#     Returns:
#         int: キャッシュ保持時間（秒）
#     """
#     if data_size > 5000:
#         return 7200  # 2時間
#     elif data_size > 1000:
#         return 3600  # 1時間
#     else:
#         return 1800  # 30分


# def get_optimal_workers():
#     """
#     システムに最適な並列ワーカー数を決定

#     Returns:
#         int: 最適なワーカー数
#     """
#     return min(os.cpu_count() or 4, 16)


# def process_texts_in_batches(texts: List[str], process_func, batch_size: int = 50):
#     """
#     テキスト処理を効率的に行うバッチ処理関数

#     Args:
#         texts: 処理するテキストのリスト
#         process_func: テキスト処理関数
#         batch_size: バッチサイズ

#     Returns:
#         List: 処理結果
#     """
#     if not texts:
#         return []

#     results = []
#     max_workers = get_optimal_workers()

#     # テキストをバッチに分割
#     def chunks(lst, n):
#         for i in range(0, len(lst), n):
#             yield lst[i : i + n]

#     if len(texts) < 100:
#         # 少量データの場合は直接並列処理
#         with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#             futures = [executor.submit(process_func, text) for text in texts if text]
#             for future in concurrent.futures.as_completed(futures):
#                 try:
#                     result = future.result()
#                     if result:
#                         results.extend(result)
#                 except Exception as e:
#                     logger.warning(f"Error in batch text processing: {str(e)}")
#     else:
#         # 大量データの場合はバッチ処理で効率化
#         batches = list(chunks(texts, batch_size))

#         for batch in batches:
#             with concurrent.futures.ThreadPoolExecutor(
#                 max_workers=max_workers
#             ) as executor:
#                 futures = [
#                     executor.submit(process_func, text) for text in batch if text
#                 ]
#                 for future in concurrent.futures.as_completed(futures):
#                     try:
#                         result = future.result()
#                         if result:
#                             results.extend(result)
#                     except Exception as e:
#                         logger.warning(f"Error in batch text processing: {str(e)}")

#     return results


# def extract_keywords(nouns: List[str], limit: int = 20) -> List[Dict[str, Any]]:
#     """
#     名詞リストからキーワードを抽出・集計

#     Args:
#         nouns: 抽出された名詞のリスト
#         limit: 返すキーワードの最大数

#     Returns:
#         List[Dict]: キーワードと出現回数のリスト
#     """
#     counter = Counter(nouns)
#     top_keywords = counter.most_common(limit)
#     return [{"word": word, "count": count} for word, count in top_keywords]
