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

```bash
python manage.py evaluate_qa_citations --base-id 1 --dataset docs/benchmark/qa_citation_eval.sample.json --top-k 4
```

```bash
python manage.py evaluate_review_cycles --base-id 1 --dataset docs/benchmark/review_eval.sample.json --output reports/review-on.json
```

```bash
python manage.py compare_benchmark_reports --baseline reports/dense.json --candidate reports/hybrid.json
```

## 当前指标

- `hit_rate`: top-k 中是否至少命中一个标准引用
- `mrr`: 第一个正确引用的倒数排名
- `avg_recall_at_k`: top-k 对标准引用集合的平均召回率
- `avg_precision_at_k`: top-k 返回引用中正确引用的平均占比
- `citation_hit_rate`: QA 返回的 citations 是否命中标准引用
- `citation_marker_rate`: 回答文本是否显式使用 `[1]` 这类 citation 标记
- `avg_valid_marker_rate`: 回答中 citation 标记是否落在有效引用范围内
- `avg_citation_recall`: QA 返回 citations 对标准引用集合的平均召回率
- `avg_citation_precision`: QA 返回 citations 中正确引用的平均占比
- `review_trigger_rate`: 有多少案例触发了 review
- `review_execution_rate`: 有多少案例真的执行了 review cycle
- `avg_score_delta`: review 前后 overall 平均变化
- `avg_groundedness_delta`: review 前后 groundedness 平均变化
- `avg_learner_fit_delta`: review 前后 learner_fit 平均变化
- `review_accept_rate`: 执行过 review 的案例里，有多少最终被采纳

## 建议使用方式

- 先为常见问答构造 20-50 条小规模数据集
- 每次调整切分、embedding、pgvector 参数、hybrid retrieval 或 rerank 后都跑一遍
- 将报告保存在 `reports/` 或单独的 benchmark 目录，逐步形成版本对比
- 新版报告会自动记录 `vector_backend / hybrid_retrieval / rerank_enabled / embedding_model`
- 可用 `compare_benchmark_reports` 直接对比两份 JSON 报告的 summary 指标差异
- 可先跑一份 `REVIEW_ENABLED=false` 的 review 报告，再跑一份 `REVIEW_ENABLED=true` 的报告，直接比较反思是否带来稳定提升

## 当前实验开关

- `HYBRID_RETRIEVAL=true|false`
- `RERANK_ENABLED=true|false`
- `true` 时启用 dense 向量召回 + lexical 召回 + RRF 融合
- `RERANK_ENABLED=true` 时启用轻量 query-aware rerank
- 建议分别运行 pure dense / hybrid / hybrid+rereank 三组评测报告，直接比较指标差异

## 进一步阅读

- [2026评测与反思设计.md](D:/code/classweaver-microagents/docs/benchmark/2026评测与反思设计.md)
