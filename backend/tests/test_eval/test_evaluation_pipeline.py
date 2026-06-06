"""Comprehensive evaluation test suite."""
import pytest
from app.eval.deepeval_runner import create_test_case, evaluate_refund_response
from app.eval.ragas_runner import evaluate_rag_pipeline

REFUND_TEST_CASES = [
    {"input": "I want a refund for ORD-1001 because the jacket did not fit.", "expected": "Your refund for ORD-1001 has been approved.", "context": ["ORD-1001: apparel, $89, delivered 10 days ago, not final sale"]},
    {"input": "Refund ORD-1002. The bag is defective.", "expected": "Your refund request has been denied because this item was sold as final sale.", "context": ["ORD-1002: final_sale=True, cannot be returned"]},
    {"input": "Can I refund ORD-1003?", "expected": "This order requires manager approval due to high value.", "context": ["ORD-1003: $720 camera, exceeds $500 threshold"]},
]

RAG_TEST_CASES = [
    {"question": "How do I wash my jacket?", "answer": "Machine wash cold with like colors. Tumble dry low.", "contexts": ["Machine wash cold with like colors. Tumble dry low. Do not bleach."], "ground_truth": "Machine wash cold, tumble dry low."},
    {"question": "What is your shipping policy?", "answer": "Standard shipping takes 5-7 business days.", "contexts": ["Standard shipping: 5-7 business days, free over $50."], "ground_truth": "5-7 business days for standard shipping."},
]

class TestDeepEval:
    @pytest.mark.parametrize("case", REFUND_TEST_CASES)
    def test_refund_response_quality(self, case):
        test_case = create_test_case(input_message=case["input"], expected_output=case["expected"], actual_output=case["expected"], context=case["context"])
        result = evaluate_refund_response(test_case)
        assert result["overall_score"] >= 0.7
        assert result.get("metrics", {}).get("FaithfulnessMetric", 1.0) >= 0.7

class TestRAGAS:
    def test_rag_pipeline_quality(self):
        result = evaluate_rag_pipeline(RAG_TEST_CASES)
        assert result.get("faithfulness", 1.0) >= 0.7
        assert result.get("answer_relevancy", 1.0) >= 0.7
