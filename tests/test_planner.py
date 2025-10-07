"""Tests for ExperimentPlanner."""

from servesmith.models.experiment import ExperimentRequest, VLLMArgs
from servesmith.models.formats import ModelFormat
from servesmith.models.resource import Resource
from servesmith.planner.planner import ExperimentPlanner


def test_planner_basic():
    request = ExperimentRequest(
        source_model_name="Qwen/Qwen2.5-0.5B-Instruct",
        test_data_path="s3://bucket/data.json",
        output_s3_path="s3://bucket/out/",
        resources=[Resource(instance_type="g4dn.xlarge")],
        concurrencies=[1, 4],
    )
    planner = ExperimentPlanner()
    runs = planner.plan(request, "test-001")
    assert len(runs) == 2  # 1 resource × 2 concurrencies × 1 everything else


def test_planner_skips_invalid_tp():
    """TP=4 on g4dn.xlarge (1 GPU) should be skipped."""
    request = ExperimentRequest(
        source_model_name="test-model",
        test_data_path="s3://b/d.json",
        output_s3_path="s3://b/o/",
        resources=[Resource(instance_type="g4dn.xlarge")],  # 1 GPU
        concurrencies=[1],
        target_model_format_args={
            ModelFormat.VLLM_LATEST: VLLMArgs(tensor_parallel_size=[1, 2, 4])
        },
    )
    planner = ExperimentPlanner()
    runs = planner.plan(request, "test-002")
    # Only TP=1 should survive (g4dn.xlarge has 1 GPU)
    assert len(runs) == 1
    assert runs[0].tensor_parallel == 1


def test_planner_multi_config_sweep():
    """Full sweep across multiple dimensions."""
    request = ExperimentRequest(
        source_model_name="test-model",
        test_data_path="s3://b/d.json",
        output_s3_path="s3://b/o/",
        resources=[Resource(instance_type="g5.xlarge"), Resource(instance_type="g4dn.xlarge")],
        concurrencies=[1, 4],
        target_model_format_args={
            ModelFormat.VLLM_LATEST: VLLMArgs(
                target_precision=["float16"],
                quantization=[None, "awq"],
            )
        },
    )
    planner = ExperimentPlanner()
    runs = planner.plan(request, "test-003")
    # 2 resources × 2 concurrencies × 2 quantizations = 8
    assert len(runs) == 8


def test_planner_empty_concurrencies():
    request = ExperimentRequest(
        source_model_name="test",
        test_data_path="s3://b/d.json",
        output_s3_path="s3://b/o/",
        resources=[Resource(instance_type="g4dn.xlarge")],
        concurrencies=[],
    )
    planner = ExperimentPlanner()
    runs = planner.plan(request, "test-004")
    assert len(runs) == 0
