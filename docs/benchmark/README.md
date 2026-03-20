# RAG Benchmark

当前仓库提供一套轻量检索评测入口，用于建立自己的知识库 benchmark。

## 数据集格式

参考 `retrieval_eval.sample.json`：

```json
{
  "cases": [
    {
      "query": "问题文本",
      "expected_refs": [
        {"doc_id": "文档ID", "chunk_id": "切片ID"}
      ]
    }
  ]
}
```

## 运行方式

```bash
python manage.py evaluate_retrieval --base-id 1 --dataset docs/benchmark/retrieval_eval.sample.json --top-k 5
```

## 当前指标

- `hit_rate`: top-k 中是否至少命中一个标准引用
- `mrr`: 第一个正确引用的倒数排名
- `avg_recall_at_k`: top-k 对标准引用集合的平均召回率
- `avg_precision_at_k`: top-k 返回引用中正确引用的平均占比

## 建议使用方式

- 先为常见问答构造 20-50 条小规模数据集
- 每次调整切分、embedding、pgvector 参数、hybrid retrieval 或 rerank 后都跑一遍
- 将报告保存在 `reports/` 或单独的 benchmark 目录，逐步形成版本对比
