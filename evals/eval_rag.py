"""
RAGAS evaluation for the RAG agent.

Metrics scored per question:
  - Faithfulness      : is the answer grounded in retrieved chunks?
  - Answer Relevancy  : does the answer address the question?
  - Context Precision : are retrieved chunks relevant to the question?
  - Context Recall    : do chunks cover what the ground truth requires?

Run:
    uv run python evals/eval_rag.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.rag_agent import rag_agent, search_docs
from evals.rag_dataset import SAMPLES

from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def get_rag_response(question: str) -> tuple[str, list[str]]:
    """Call search_docs + rag_agent, return (answer, context_chunks)."""
    raw = search_docs.invoke(question)
    contexts = [
        chunk.split("\n", 1)[-1].strip()
        for chunk in raw.split("\n\n---\n\n")
    ]
    result = rag_agent.invoke({"messages": [{"role": "user", "content": question}]})
    answer = result["messages"][-1].content
    return answer, contexts


def build_dataset() -> EvaluationDataset:
    samples = []
    print(f"Collecting responses for {len(SAMPLES)} questions...\n")

    for i, entry in enumerate(SAMPLES, 1):
        question = entry["question"]
        ground_truth = entry["ground_truth"]
        print(f"  [{i}/{len(SAMPLES)}] {question}")

        answer, contexts = get_rag_response(question)

        samples.append(
            SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=contexts,
                reference=ground_truth,
            )
        )

    print()
    return EvaluationDataset(samples=samples)


def run_eval():
    api_key = os.getenv("OPENAI_API_KEY")
    llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key))

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    dataset = build_dataset()

    print("Running RAGAS evaluation...\n")
    results = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=embeddings)

    df = results.to_pandas()
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    available = [c for c in metric_cols if c in df.columns]

    print("\n── Per-question scores ─────────────────────────────────────────────")
    print(df[["user_input"] + available].to_string(index=False))

    print("\n── Averages ────────────────────────────────────────────────────────")
    averages = df[available].mean()
    print(averages.to_string())

    output_path = (
        Path(__file__).parent / "results"
        / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "samples": df[["user_input"] + available].to_dict(orient="records"),
                "averages": averages.to_dict(),
            },
            f,
            indent=2,
        )

    print(f"\nSaved → {output_path}")
    _print_history_table(output_path)
    return results


def _print_history_table(latest_path: Path) -> None:
    results_dir = latest_path.parent
    files = sorted(results_dir.glob("eval_*.json"))

    rows = []
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        avg = data.get("averages", {})
        # timestamp from filename: eval_YYYYMMDD_HHMMSS.json → HH:MM
        ts = f.stem.split("_", 1)[1]  # 20260421_201153
        hhmm = ts[9:11] + ":" + ts[11:13]
        rows.append({
            "run": hhmm,
            "faithfulness": avg.get("faithfulness"),
            "answer_relevancy": avg.get("answer_relevancy"),
            "context_precision": avg.get("context_precision"),
            "context_recall": avg.get("context_recall"),
        })

    print("\n── All runs comparison ─────────────────────────────────────────────")
    header = f"{'Run':<6}  {'Faithfulness':>13}  {'Ans Relevancy':>14}  {'Ctx Precision':>14}  {'Ctx Recall':>11}"
    print(header)
    print("─" * len(header))
    for i, r in enumerate(rows):
        marker = " ◄" if i == len(rows) - 1 else ""
        print(
            f"{r['run']:<6}  "
            f"{r['faithfulness']:>13.3f}  "
            f"{r['answer_relevancy']:>14.3f}  "
            f"{r['context_precision']:>14.3f}  "
            f"{r['context_recall']:>11.3f}"
            f"{marker}"
        )


if __name__ == "__main__":
    run_eval()
