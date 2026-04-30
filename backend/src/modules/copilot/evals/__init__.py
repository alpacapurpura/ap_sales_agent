"""Copilot eval gate framework — D-3 (CONTRACT PR-3 PI-2 S2).

Package layout::

    evals/
    ├── golden_dataset.py       JSONL loader + Pydantic schemas
    ├── runner.py               CLI harness + eval orchestration
    └── scorers/
        ├── base.py             Protocol Scorer
        ├── classifier.py       exact-match tier scorer
        └── summarizer.py       ROUGE-L + cosine similarity scorer
"""
