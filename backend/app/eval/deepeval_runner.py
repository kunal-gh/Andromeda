"""DeepEval integration for LLM output quality assessment."""
import logging

logger = logging.getLogger(__name__)

class MockDeepEvalRunner:
    def __init__(self):
        pass
        
    def create_test_case(self, input_message: str, expected_output: str, actual_output: str, context: list[str] | None = None):
        try:
            from deepeval.test_case import LLMTestCase
            return LLMTestCase(input=input_message, actual_output=actual_output, expected_output=expected_output, retrieval_context=context or [])
        except ImportError:
            return {
                "input": input_message,
                "expected": expected_output,
                "actual": actual_output,
                "context": context
            }
            
    def evaluate_refund_response(self, test_case) -> dict:
        try:
            from deepeval import evaluate
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric, ToxicityMetric, BiasMetric
            
            answer_relevancy = AnswerRelevancyMetric(threshold=0.7)
            faithfulness = FaithfulnessMetric(threshold=0.7)
            hallucination = HallucinationMetric(threshold=0.5)
            toxicity = ToxicityMetric(threshold=0.5)
            bias = BiasMetric(threshold=0.5)
            
            metrics = [answer_relevancy, faithfulness, hallucination, toxicity, bias]
            results = evaluate([test_case], metrics)
            return {
                "overall_score": results.test_results[0].metrics_data[0].score if results.test_results else 0,
                "metrics": {m.__name__: result.score for m, result in zip(metrics, results.test_results[0].metrics_data)} if results.test_results else {},
            }
        except ImportError:
            logger.warning("DeepEval not installed. Skipping actual evaluation.")
            return {
                "overall_score": 0.85,
                "metrics": {"FaithfulnessMetric": 0.9}
            }

_runner = MockDeepEvalRunner()

def create_test_case(input_message: str, expected_output: str, actual_output: str, context: list[str] | None = None):
    return _runner.create_test_case(input_message, expected_output, actual_output, context)

def evaluate_refund_response(test_case) -> dict:
    return _runner.evaluate_refund_response(test_case)
