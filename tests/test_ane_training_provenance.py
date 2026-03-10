"""
Test suite for UATP 7.3 Apple Silicon Training Provenance

Tests:
- All 5 payload validations (KernelExecution, HardwareProfile, CompileArtifact, TrainingTelemetry, ANETrainingSession)
- ANE kernel types (kFwdAttn, kFwdFFN, kFFNBwd, kSdpaBwd1, kSdpaBwd2, kQKVb)
- Metal GPU kernel types (metal_gemm, metal_attention, mps_conv2d)
- MLX kernel types (mlx_matmul, mlx_softmax, mlx_rope)
- Hardware profile with ANE, GPU/Metal, and MLX capabilities
- MIL, MLX, and Metal compile artifacts
- Telemetry with ANE and GPU metrics
- UATP 7.3 envelope version detection
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.capsule_schema import (
    ANETrainingSessionCapsule,
    ANETrainingSessionPayload,
    CapsuleStatus,
    CapsuleType,
    CompileArtifactCapsule,
    CompileArtifactPayload,
    DatasetReference,
    HardwareProfileCapsule,
    HardwareProfilePayload,
    HybridComputeAttribution,
    KernelExecutionCapsule,
    KernelExecutionPayload,
    MILFusionOptimization,
    TrainingTelemetryCapsule,
    TrainingTelemetryPayload,
    Verification,
)
from src.security.attestation import AttestationType
from src.utils.uatp_envelope import (
    create_ane_context,
    create_kernel_trace_context,
    detect_capsule_version,
    wrap_in_uatp_envelope,
)

# --- Test Fixtures ---


def create_verification() -> Verification:
    """Create a test verification object."""
    return Verification(
        signature=f"ed25519:{'0' * 128}",
        merkle_root=f"sha256:{'0' * 64}",
    )


def create_capsule_id() -> str:
    """Create a valid test capsule ID."""
    return f"caps_2026_03_03_{'a' * 16}"


# --- HybridComputeAttribution Tests ---


class TestHybridComputeAttribution:
    """Test HybridComputeAttribution payload validation."""

    def test_valid_ane_attribution(self):
        """Test valid ANE-dominant compute attribution."""
        attr = HybridComputeAttribution(
            compute_unit="ane",
            ane_percentage=88.5,
            cpu_percentage=11.5,
            gpu_percentage=0.0,
            dispatch_reason="Forward pass optimized for ANE",
        )
        assert attr.compute_unit == "ane"
        assert attr.ane_percentage == 88.5
        assert attr.cpu_percentage == 11.5

    def test_valid_hybrid_attribution(self):
        """Test valid hybrid compute attribution."""
        attr = HybridComputeAttribution(
            compute_unit="hybrid",
            ane_percentage=65.0,
            cpu_percentage=35.0,
        )
        assert attr.compute_unit == "hybrid"

    def test_invalid_percentage_over_100(self):
        """Test that percentage over 100 fails validation."""
        with pytest.raises(ValidationError):
            HybridComputeAttribution(
                compute_unit="ane",
                ane_percentage=110.0,  # Invalid
                cpu_percentage=5.0,
            )

    def test_invalid_negative_percentage(self):
        """Test that negative percentage fails validation."""
        with pytest.raises(ValidationError):
            HybridComputeAttribution(
                compute_unit="cpu",
                ane_percentage=-10.0,  # Invalid
                cpu_percentage=110.0,
            )


# --- MILFusionOptimization Tests ---


class TestMILFusionOptimization:
    """Test MILFusionOptimization payload validation."""

    def test_valid_fusion_optimization(self):
        """Test valid MIL fusion optimization."""
        fusion = MILFusionOptimization(
            fusion_name="attention_fused_qkv",
            source_ops=["linear_q", "linear_k", "linear_v"],
            target_op="fused_qkv_projection",
            speedup_factor=2.5,
            memory_reduction_bytes=1048576,  # 1MB
        )
        assert fusion.fusion_name == "attention_fused_qkv"
        assert len(fusion.source_ops) == 3
        assert fusion.speedup_factor == 2.5

    def test_minimal_fusion(self):
        """Test minimal fusion optimization (required fields only)."""
        fusion = MILFusionOptimization(
            fusion_name="matmul_add_fusion",
            source_ops=["matmul", "add"],
            target_op="fused_matmul_bias",
        )
        assert fusion.speedup_factor is None
        assert fusion.memory_reduction_bytes is None

    def test_invalid_speedup_factor(self):
        """Test that speedup factor less than 1.0 fails."""
        with pytest.raises(ValidationError):
            MILFusionOptimization(
                fusion_name="bad_fusion",
                source_ops=["op1"],
                target_op="op2",
                speedup_factor=0.5,  # Invalid: must be >= 1.0
            )


# --- KernelExecutionPayload Tests ---


class TestKernelExecutionPayload:
    """Test KernelExecutionPayload for all 6 kernel types."""

    @pytest.mark.parametrize(
        "kernel_type",
        [
            "kFwdAttn",  # Forward attention
            "kFwdFFN",  # Forward feed-forward network
            "kFFNBwd",  # Backward FFN
            "kSdpaBwd1",  # SDPA backward pass 1
            "kSdpaBwd2",  # SDPA backward pass 2
            "kQKVb",  # QKV backward
        ],
    )
    def test_all_kernel_types(self, kernel_type):
        """Test all 6 ANE kernel types."""
        payload = KernelExecutionPayload(
            session_id="ane_20260303_test123",
            kernel_type=kernel_type,
            step_index=42,
            dispatch_index=0,
            execution_time_us=150,
            iosurface_format="[1,C,1,S]",
            input_shape=[1, 512, 768],
            output_shape=[1, 512, 768],
        )
        assert payload.kernel_type == kernel_type
        assert payload.execution_time_us == 150

    def test_kernel_with_compute_attribution(self):
        """Test kernel execution with hybrid compute attribution."""
        payload = KernelExecutionPayload(
            session_id="ane_20260303_test123",
            kernel_type="kFwdAttn",
            step_index=0,
            dispatch_index=0,
            execution_time_us=200,
            compute_attribution=HybridComputeAttribution(
                compute_unit="ane",
                ane_percentage=95.0,
                cpu_percentage=5.0,
            ),
            ane_program_hash="sha256:" + "a" * 56,
        )
        assert payload.compute_attribution.ane_percentage == 95.0

    def test_invalid_step_index(self):
        """Test that negative step index fails."""
        with pytest.raises(ValidationError):
            KernelExecutionPayload(
                session_id="ane_test",
                kernel_type="kFwdAttn",
                step_index=-1,  # Invalid
                dispatch_index=0,
                execution_time_us=100,
            )


# --- Metal/MLX Kernel Tests ---


class TestMetalMLXKernelExecution:
    """Test kernel execution for Metal GPU and MLX accelerators."""

    @pytest.mark.parametrize(
        "kernel_type,accelerator",
        [
            ("metal_gemm", "metal"),
            ("metal_attention", "metal"),
            ("mps_conv2d", "mps"),
            ("mps_matmul", "mps"),
        ],
    )
    def test_metal_kernel_types(self, kernel_type, accelerator):
        """Test Metal and MPS kernel types."""
        payload = KernelExecutionPayload(
            session_id="metal_20260303_test",
            accelerator_type=accelerator,
            kernel_type=kernel_type,
            step_index=0,
            dispatch_index=0,
            execution_time_us=250,
            metal_buffer_mode="private",
            metal_shader_hash="sha256:" + "m" * 56,
            input_shape=[1, 512, 768],
            output_shape=[1, 512, 768],
        )
        assert payload.accelerator_type == accelerator
        assert payload.kernel_type == kernel_type
        assert payload.metal_buffer_mode == "private"

    @pytest.mark.parametrize(
        "kernel_type",
        [
            "mlx_matmul",
            "mlx_softmax",
            "mlx_rope",
            "mlx_rms_norm",
            "mlx_attention",
        ],
    )
    def test_mlx_kernel_types(self, kernel_type):
        """Test MLX kernel types."""
        payload = KernelExecutionPayload(
            session_id="mlx_20260303_test",
            accelerator_type="mlx",
            kernel_type=kernel_type,
            step_index=100,
            dispatch_index=0,
            execution_time_us=180,
            mlx_graph_hash="sha256:" + "x" * 56,
            compute_attribution=HybridComputeAttribution(
                compute_unit="gpu",
                gpu_percentage=100.0,
                ane_percentage=0.0,
                cpu_percentage=0.0,
            ),
        )
        assert payload.accelerator_type == "mlx"
        assert payload.kernel_type == kernel_type
        assert payload.mlx_graph_hash is not None

    def test_metal_buffer_modes(self):
        """Test all Metal buffer allocation modes."""
        for mode in ["shared", "private", "managed"]:
            payload = KernelExecutionPayload(
                session_id="metal_buffer_test",
                accelerator_type="metal",
                kernel_type="metal_gemm",
                step_index=0,
                dispatch_index=0,
                execution_time_us=200,
                metal_buffer_mode=mode,
            )
            assert payload.metal_buffer_mode == mode

    def test_cpu_fallback_kernel(self):
        """Test CPU fallback execution tracking."""
        payload = KernelExecutionPayload(
            session_id="cpu_fallback_test",
            accelerator_type="cpu",
            kernel_type="softmax_fallback",
            step_index=50,
            dispatch_index=2,
            execution_time_us=1500,  # CPU is slower
            compute_attribution=HybridComputeAttribution(
                compute_unit="cpu",
                cpu_percentage=100.0,
                ane_percentage=0.0,
                gpu_percentage=0.0,
                dispatch_reason="Operation unsupported on accelerator",
            ),
        )
        assert payload.accelerator_type == "cpu"
        assert payload.compute_attribution.cpu_percentage == 100.0


# --- HardwareProfilePayload Tests ---


class TestHardwareProfilePayload:
    """Test HardwareProfilePayload with private API disclosure."""

    def test_m4_pro_profile(self):
        """Test M4 Pro hardware profile."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Pro",
            ane_available=True,
            ane_version="17.0",
            ane_tops=38.0,
            ane_compile_limit=119,
            memory_bandwidth_gbps=273.0,
            unified_memory_gb=48.0,
            private_apis_used=["_ANEClient", "_ANECompiler", "_ANEModel"],
            device_id_hash="sha256:" + "d" * 56,
            os_version="15.2",
            coreml_version="8.0",
        )
        assert payload.chip_identifier == "M4"
        assert payload.ane_tops == 38.0
        assert "_ANEClient" in payload.private_apis_used
        assert len(payload.private_apis_used) == 3

    def test_iphone_a17_profile(self):
        """Test iPhone A17 Pro hardware profile."""
        payload = HardwareProfilePayload(
            device_class="iphone",
            chip_identifier="A17",
            chip_variant="Pro",
            ane_available=True,
            ane_tops=35.0,
            private_apis_used=["_ANEClient"],
            device_id_hash="sha256:" + "e" * 56,
        )
        assert payload.device_class == "iphone"
        assert payload.ane_available is True

    def test_profile_without_ane(self):
        """Test profile for device without ANE."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="Intel",
            ane_available=False,
            private_apis_used=[],
            device_id_hash="sha256:" + "f" * 56,
        )
        assert payload.ane_available is False
        assert payload.ane_tops is None


# --- GPU/Metal Hardware Profile Tests ---


class TestGPUHardwareProfile:
    """Test hardware profiles with GPU/Metal capabilities."""

    def test_m4_max_gpu_profile(self):
        """Test M4 Max with full GPU capabilities."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Max",
            ane_available=True,
            ane_tops=38.0,
            ane_compile_limit=119,
            gpu_core_count=40,
            gpu_tflops=14.0,
            metal_version="3.2",
            metal_family="apple9",
            mps_available=True,
            mlx_version="0.20.0",
            frameworks_used=["mlx", "pytorch_mps", "coreml"],
            unified_memory_gb=128.0,
            memory_bandwidth_gbps=546.0,
            private_apis_used=["_ANEClient"],
            device_id_hash="sha256:" + "g" * 56,
        )
        assert payload.gpu_core_count == 40
        assert payload.gpu_tflops == 14.0
        assert payload.metal_version == "3.2"
        assert payload.mlx_version == "0.20.0"
        assert "mlx" in payload.frameworks_used

    def test_m3_pro_profile(self):
        """Test M3 Pro hardware profile."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M3",
            chip_variant="Pro",
            ane_available=True,
            ane_tops=35.0,
            gpu_core_count=18,
            gpu_tflops=8.0,
            metal_version="3.1",
            metal_family="apple8",
            mps_available=True,
            mlx_version="0.18.0",
            frameworks_used=["mlx"],
            unified_memory_gb=36.0,
            device_id_hash="sha256:" + "p" * 56,
        )
        assert payload.chip_identifier == "M3"
        assert payload.gpu_core_count == 18
        assert payload.metal_family == "apple8"

    def test_gpu_only_training_profile(self):
        """Test profile optimized for GPU-only training (no ANE)."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Pro",
            ane_available=True,  # Available but not used
            ane_tops=38.0,
            gpu_core_count=20,
            gpu_tflops=10.0,
            metal_version="3.2",
            mps_available=True,
            mlx_version="0.20.0",
            frameworks_used=["mlx"],  # Only MLX, no ANE
            device_id_hash="sha256:" + "q" * 56,
        )
        assert "mlx" in payload.frameworks_used
        assert "coreml" not in payload.frameworks_used  # Not using ANE

    def test_pytorch_mps_profile(self):
        """Test profile for PyTorch MPS backend."""
        payload = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M2",
            ane_available=True,
            gpu_core_count=10,
            gpu_tflops=4.0,
            metal_version="3.0",
            mps_available=True,
            frameworks_used=["pytorch_mps"],
            device_id_hash="sha256:" + "r" * 56,
        )
        assert "pytorch_mps" in payload.frameworks_used
        assert payload.mps_available is True


# --- CompileArtifactPayload Tests ---


class TestCompileArtifactPayload:
    """Test CompileArtifactPayload with fusion optimizations."""

    def test_artifact_with_fusions(self):
        """Test compile artifact with multiple fusion optimizations."""
        payload = CompileArtifactPayload(
            artifact_id="art_test123",
            session_id="ane_20260303_test",
            mil_program_hash="sha256:" + "a" * 56,
            weight_blob_hash="sha256:" + "b" * 56,
            compiled_model_hash="sha256:" + "c" * 56,
            fusion_optimizations=[
                MILFusionOptimization(
                    fusion_name="attention_fusion",
                    source_ops=["q_proj", "k_proj", "v_proj"],
                    target_op="qkv_fused",
                    speedup_factor=1.8,
                ),
                MILFusionOptimization(
                    fusion_name="ffn_fusion",
                    source_ops=["linear1", "gelu", "linear2"],
                    target_op="ffn_fused",
                    speedup_factor=1.5,
                    memory_reduction_bytes=524288,
                ),
            ],
            compile_time_ms=3500,
            target_device="M4",
            coreml_spec_version=8,
            mlmodel_size_bytes=104857600,  # 100MB
            storage_uri="s3://models/compiled/test.mlmodelc",
            created_at=datetime.now(timezone.utc),
        )
        assert len(payload.fusion_optimizations) == 2
        assert payload.fusion_optimizations[0].fusion_name == "attention_fusion"

    def test_minimal_artifact(self):
        """Test minimal compile artifact."""
        payload = CompileArtifactPayload(
            artifact_id="art_minimal",
            session_id="ane_test",
            mil_program_hash="sha256:" + "x" * 56,
            created_at=datetime.now(timezone.utc),
        )
        assert len(payload.fusion_optimizations) == 0


# --- MLX and Metal Compile Artifact Tests ---


class TestMLXMetalArtifacts:
    """Test compile artifacts for MLX graphs and Metal shaders."""

    def test_mlx_compiled_graph(self):
        """Test MLX compiled graph artifact."""
        payload = CompileArtifactPayload(
            artifact_id="art_mlx_001",
            session_id="mlx_training_test",
            artifact_format="mlx",
            mlx_graph_hash="sha256:" + "l" * 56,
            mlx_version="0.20.0",
            mlx_simplifications=[
                "fuse_matmul_bias",
                "constant_folding",
                "dead_code_elimination",
            ],
            target_accelerator="gpu",
            compile_time_ms=1200,
            created_at=datetime.now(timezone.utc),
        )
        assert payload.artifact_format == "mlx"
        assert payload.mlx_graph_hash is not None
        assert payload.mlx_version == "0.20.0"
        assert len(payload.mlx_simplifications) == 3
        assert payload.target_accelerator == "gpu"

    def test_metal_shader_library(self):
        """Test Metal shader library artifact."""
        payload = CompileArtifactPayload(
            artifact_id="art_metal_001",
            session_id="metal_training_test",
            artifact_format="metal",
            metal_library_hash="sha256:" + "s" * 56,
            target_accelerator="gpu",
            compile_time_ms=500,
            created_at=datetime.now(timezone.utc),
        )
        assert payload.artifact_format == "metal"
        assert payload.metal_library_hash is not None
        assert payload.mil_program_hash is None

    def test_safetensors_artifact(self):
        """Test safetensors format artifact (MLX native)."""
        payload = CompileArtifactPayload(
            artifact_id="art_safetensors_001",
            session_id="mlx_test",
            artifact_format="safetensors",
            mlx_graph_hash="sha256:" + "t" * 56,
            mlx_version="0.20.0",
            mlmodel_size_bytes=2147483648,  # 2GB
            storage_uri="s3://models/llama3-8b-mlx/model.safetensors",
            created_at=datetime.now(timezone.utc),
        )
        assert payload.artifact_format == "safetensors"
        assert payload.mlmodel_size_bytes == 2147483648

    def test_gguf_artifact(self):
        """Test GGUF format artifact (quantized)."""
        payload = CompileArtifactPayload(
            artifact_id="art_gguf_001",
            session_id="quantization_test",
            artifact_format="gguf",
            weight_blob_hash="sha256:" + "u" * 56,
            compiled_model_hash="sha256:" + "v" * 56,
            target_accelerator="cpu",  # Quantized for CPU inference
            mlmodel_size_bytes=4294967296,  # 4GB
            created_at=datetime.now(timezone.utc),
        )
        assert payload.artifact_format == "gguf"
        assert payload.target_accelerator == "cpu"

    def test_hybrid_mil_mlx_artifact(self):
        """Test artifact with both MIL and MLX hashes (hybrid pipeline)."""
        payload = CompileArtifactPayload(
            artifact_id="art_hybrid_001",
            session_id="hybrid_test",
            artifact_format="mil",  # Primary format
            mil_program_hash="sha256:" + "w" * 56,
            mlx_graph_hash="sha256:" + "x" * 56,  # Also has MLX version
            target_accelerator="ane",  # ANE with MLX fallback
            fusion_optimizations=[
                MILFusionOptimization(
                    fusion_name="attention_fusion",
                    source_ops=["q", "k", "v"],
                    target_op="qkv_fused",
                    speedup_factor=2.0,
                )
            ],
            created_at=datetime.now(timezone.utc),
        )
        assert payload.mil_program_hash is not None
        assert payload.mlx_graph_hash is not None


# --- TrainingTelemetryPayload Tests ---


class TestTrainingTelemetryPayload:
    """Test TrainingTelemetryPayload with compute attribution."""

    def test_telemetry_with_attribution(self):
        """Test telemetry with hybrid compute attribution."""
        payload = TrainingTelemetryPayload(
            session_id="ane_20260303_test",
            measurement_window_seconds=60,
            steps_in_window=645,
            avg_ms_per_step=9.3,
            avg_ane_utilization=11.2,
            peak_ane_utilization=45.0,
            tflops_achieved=3.2,
            memory_used_gb=12.5,
            thermal_state="nominal",
            power_consumption_watts=25.0,
            compute_attribution=HybridComputeAttribution(
                compute_unit="hybrid",
                ane_percentage=65.0,
                cpu_percentage=35.0,
            ),
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.avg_ms_per_step == 9.3
        assert payload.avg_ane_utilization == 11.2
        assert payload.compute_attribution.ane_percentage == 65.0

    def test_invalid_utilization(self):
        """Test that utilization over 100 fails."""
        with pytest.raises(ValidationError):
            TrainingTelemetryPayload(
                session_id="test",
                measurement_window_seconds=60,
                steps_in_window=100,
                avg_ms_per_step=10.0,
                avg_ane_utilization=150.0,  # Invalid
                timestamp=datetime.now(timezone.utc),
            )


# --- GPU/Metal Telemetry Tests ---


class TestGPUTelemetry:
    """Test telemetry with GPU/Metal metrics."""

    def test_gpu_dominant_telemetry(self):
        """Test telemetry for GPU-dominant training (MLX)."""
        payload = TrainingTelemetryPayload(
            session_id="mlx_20260303_test",
            measurement_window_seconds=60,
            steps_in_window=1000,
            avg_ms_per_step=5.2,  # MLX is faster
            avg_ane_utilization=0.0,  # Not using ANE
            avg_gpu_utilization=85.0,
            peak_gpu_utilization=98.0,
            gpu_memory_used_gb=24.5,
            gpu_memory_allocated_gb=32.0,
            tflops_achieved=8.5,
            gpu_tflops=8.5,
            ane_tflops=0.0,
            primary_accelerator="gpu",
            memory_used_gb=26.0,
            thermal_state="nominal",
            compute_attribution=HybridComputeAttribution(
                compute_unit="gpu",
                gpu_percentage=100.0,
                ane_percentage=0.0,
                cpu_percentage=0.0,
            ),
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.primary_accelerator == "gpu"
        assert payload.avg_gpu_utilization == 85.0
        assert payload.gpu_memory_used_gb == 24.5
        assert payload.compute_attribution.gpu_percentage == 100.0

    def test_hybrid_ane_gpu_telemetry(self):
        """Test telemetry for hybrid ANE+GPU training."""
        payload = TrainingTelemetryPayload(
            session_id="hybrid_20260303_test",
            measurement_window_seconds=60,
            steps_in_window=500,
            avg_ms_per_step=7.5,
            avg_ane_utilization=45.0,
            peak_ane_utilization=65.0,
            avg_gpu_utilization=35.0,
            peak_gpu_utilization=55.0,
            gpu_memory_used_gb=16.0,
            tflops_achieved=6.5,
            gpu_tflops=3.0,
            ane_tflops=3.5,
            primary_accelerator="ane",  # ANE is primary
            compute_attribution=HybridComputeAttribution(
                compute_unit="hybrid",
                ane_percentage=55.0,
                gpu_percentage=35.0,
                cpu_percentage=10.0,
            ),
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.primary_accelerator == "ane"
        assert payload.avg_ane_utilization == 45.0
        assert payload.avg_gpu_utilization == 35.0
        assert payload.ane_tflops == 3.5
        assert payload.gpu_tflops == 3.0

    def test_metal_command_buffer_throughput(self):
        """Test Metal-specific telemetry metrics."""
        payload = TrainingTelemetryPayload(
            session_id="metal_perf_test",
            measurement_window_seconds=60,
            steps_in_window=800,
            avg_ms_per_step=6.0,
            avg_gpu_utilization=90.0,
            peak_gpu_utilization=99.0,
            metal_command_buffers_per_second=15000.0,
            gpu_tflops=10.0,
            primary_accelerator="gpu",
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.metal_command_buffers_per_second == 15000.0

    def test_memory_pressure_telemetry(self):
        """Test telemetry under memory pressure."""
        payload = TrainingTelemetryPayload(
            session_id="memory_test",
            measurement_window_seconds=60,
            steps_in_window=200,
            avg_ms_per_step=15.0,  # Slower due to memory pressure
            avg_gpu_utilization=60.0,
            gpu_memory_used_gb=62.0,
            gpu_memory_allocated_gb=64.0,  # Near limit
            memory_used_gb=63.0,
            thermal_state="serious",  # Throttling
            timestamp=datetime.now(timezone.utc),
        )
        assert payload.gpu_memory_used_gb == 62.0
        assert payload.thermal_state == "serious"


# --- ANETrainingSessionPayload Tests ---


class TestANETrainingSessionPayload:
    """Test ANETrainingSessionPayload with full provenance."""

    def test_full_session_payload(self):
        """Test complete ANE training session payload."""
        payload = ANETrainingSessionPayload(
            session_id="ane_20260303_test123",
            model_id="llama3_8b_ane",
            model_name="LLaMA 3 8B ANE Fine-tune",
            hardware_profile_id="hw_20260303_m4pro",
            started_at=datetime.now(timezone.utc),
            status="completed",
            total_steps=1000,
            completed_steps=1000,
            kernel_execution_count=6000,  # 6 kernels * 1000 steps
            compile_artifact_ids=["art_001", "art_002"],
            final_loss=0.85,
            avg_ms_per_step=9.3,
            avg_ane_utilization=11.2,
            total_ane_time_seconds=5580.0,  # 93 minutes
            total_cpu_time_seconds=3720.0,  # 62 minutes
            hyperparameters={
                "learning_rate": 1e-5,
                "batch_size": 4,
                "gradient_accumulation": 8,
            },
            dataset_refs=[
                DatasetReference(
                    dataset_id="ds_alpaca",
                    dataset_name="Alpaca",
                    version="1.0",
                )
            ],
            private_apis_used=["_ANEClient", "_ANECompiler"],
            dmca_1201f_claim=True,
            research_purpose="Academic research on on-device training efficiency",
        )
        assert payload.session_id == "ane_20260303_test123"
        assert payload.dmca_1201f_claim is True
        assert payload.kernel_execution_count == 6000
        assert len(payload.private_apis_used) == 2

    def test_running_session(self):
        """Test in-progress ANE training session."""
        payload = ANETrainingSessionPayload(
            session_id="ane_running",
            model_id="test_model",
            hardware_profile_id="hw_test",
            started_at=datetime.now(timezone.utc),
            status="running",
            completed_steps=500,
            total_steps=1000,
        )
        assert payload.status == "running"
        assert payload.completed_at is None


# --- Capsule Creation Tests ---


class TestCapsuleCreation:
    """Test UATP 7.3 capsule creation."""

    def test_kernel_execution_capsule(self):
        """Test creating a KernelExecutionCapsule."""
        capsule = KernelExecutionCapsule(
            capsule_id=create_capsule_id(),
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.KERNEL_EXECUTION,
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            kernel_execution=KernelExecutionPayload(
                session_id="ane_test",
                kernel_type="kFwdAttn",
                step_index=0,
                dispatch_index=0,
                execution_time_us=150,
            ),
        )
        assert capsule.capsule_type == CapsuleType.KERNEL_EXECUTION
        assert capsule.version == "7.3"

    def test_hardware_profile_capsule(self):
        """Test creating a HardwareProfileCapsule."""
        capsule = HardwareProfileCapsule(
            capsule_id=create_capsule_id(),
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.HARDWARE_PROFILE,
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            hardware_profile=HardwareProfilePayload(
                device_class="mac",
                chip_identifier="M4",
                ane_available=True,
                private_apis_used=["_ANEClient"],
                device_id_hash="sha256:" + "d" * 56,
            ),
        )
        assert capsule.capsule_type == CapsuleType.HARDWARE_PROFILE

    def test_compile_artifact_capsule(self):
        """Test creating a CompileArtifactCapsule."""
        capsule = CompileArtifactCapsule(
            capsule_id=create_capsule_id(),
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.COMPILE_ARTIFACT,
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            compile_artifact=CompileArtifactPayload(
                artifact_id="art_test",
                session_id="ane_test",
                mil_program_hash="sha256:" + "a" * 56,
                created_at=datetime.now(timezone.utc),
            ),
        )
        assert capsule.capsule_type == CapsuleType.COMPILE_ARTIFACT

    def test_training_telemetry_capsule(self):
        """Test creating a TrainingTelemetryCapsule."""
        capsule = TrainingTelemetryCapsule(
            capsule_id=create_capsule_id(),
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.TRAINING_TELEMETRY,
            status=CapsuleStatus.DRAFT,
            verification=create_verification(),
            training_telemetry=TrainingTelemetryPayload(
                session_id="ane_test",
                measurement_window_seconds=60,
                steps_in_window=100,
                avg_ms_per_step=9.3,
                avg_ane_utilization=11.2,
                timestamp=datetime.now(timezone.utc),
            ),
        )
        assert capsule.capsule_type == CapsuleType.TRAINING_TELEMETRY

    def test_ane_training_session_capsule(self):
        """Test creating an ANETrainingSessionCapsule."""
        capsule = ANETrainingSessionCapsule(
            capsule_id=create_capsule_id(),
            version="7.3",
            timestamp=datetime.now(timezone.utc),
            capsule_type=CapsuleType.ANE_TRAINING_SESSION,
            status=CapsuleStatus.SEALED,
            verification=create_verification(),
            ane_training_session=ANETrainingSessionPayload(
                session_id="ane_complete",
                model_id="test_model",
                hardware_profile_id="hw_test",
                started_at=datetime.now(timezone.utc),
                status="completed",
            ),
        )
        assert capsule.capsule_type == CapsuleType.ANE_TRAINING_SESSION
        assert capsule.status == CapsuleStatus.SEALED


# --- UATP Envelope Tests ---


class TestUATPEnvelope:
    """Test UATP 7.3 envelope functionality."""

    def test_detect_version_73(self):
        """Test that envelope with ane_context is detected as 7.3."""
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="kernel_execution",
            ane_context={
                "session_id": "ane_test",
                "chip_identifier": "M4",
            },
        )
        version = detect_capsule_version(envelope)
        assert version == "7.3"

    def test_detect_version_73_with_kernel_trace(self):
        """Test that envelope with kernel_trace is detected as 7.3."""
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="kernel_execution",
            kernel_trace={
                "session_id": "ane_test",
                "step_index": 0,
                "kernel_executions": [],
            },
        )
        version = detect_capsule_version(envelope)
        assert version == "7.3"

    def test_detect_version_72_without_73_features(self):
        """Test that envelope with only 7.2 features is detected as 7.2."""
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="training_provenance",
            training_context={
                "model_id": "test_model",
            },
        )
        version = detect_capsule_version(envelope)
        assert version == "7.2"

    def test_create_ane_context(self):
        """Test create_ane_context helper."""
        context = create_ane_context(
            session_id="ane_test123",
            hardware_profile_id="hw_m4pro",
            chip_identifier="M4",
            ane_available=True,
            ane_tops=38.0,
            private_apis_used=["_ANEClient", "_ANECompiler"],
            dmca_1201f_claim=True,
        )
        assert context["session_id"] == "ane_test123"
        assert context["chip_identifier"] == "M4"
        assert context["ane_tops"] == 38.0
        assert context["dmca_1201f_claim"] is True
        assert "timestamp" in context

    def test_create_kernel_trace_context(self):
        """Test create_kernel_trace_context helper."""
        context = create_kernel_trace_context(
            session_id="ane_test123",
            step_index=42,
            kernel_executions=[
                {"kernel_type": "kFwdAttn", "execution_time_us": 150},
                {"kernel_type": "kFwdFFN", "execution_time_us": 200},
            ],
            total_execution_time_us=350,
            ane_percentage=88.5,
            cpu_percentage=11.5,
        )
        assert context["session_id"] == "ane_test123"
        assert context["step_index"] == 42
        assert context["kernel_count"] == 2
        assert context["ane_percentage"] == 88.5


# --- Hardware Attestation Tests ---


class TestANEAttestation:
    """Test ANE attestation type support."""

    def test_ane_attestation_type_exists(self):
        """Test that APPLE_NEURAL_ENGINE attestation type exists."""
        assert hasattr(AttestationType, "APPLE_NEURAL_ENGINE")
        assert AttestationType.APPLE_NEURAL_ENGINE.value == "apple_neural_engine"


# --- Integration Tests ---


class TestANEProvanceIntegration:
    """Integration tests for complete ANE provenance flow."""

    def test_complete_training_session_flow(self):
        """Test complete training session with all components."""
        # 1. Create hardware profile
        hw_profile = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Pro",
            ane_available=True,
            ane_tops=38.0,
            ane_compile_limit=119,
            private_apis_used=["_ANEClient", "_ANECompiler"],
            device_id_hash="sha256:" + "h" * 56,
        )

        # 2. Create ANE training session
        session_payload = ANETrainingSessionPayload(
            session_id="ane_integration_test",
            model_id="test_llama3_ane",
            model_name="Integration Test Model",
            hardware_profile_id="hw_integration_test",
            started_at=datetime.now(timezone.utc),
            status="running",
            total_steps=100,
            dmca_1201f_claim=True,
            research_purpose="Integration testing",
        )

        # 3. Create kernel executions for one step (6 kernels)
        kernel_types = [
            "kFwdAttn",
            "kFwdFFN",
            "kFFNBwd",
            "kSdpaBwd1",
            "kSdpaBwd2",
            "kQKVb",
        ]
        kernels = []
        for i, kt in enumerate(kernel_types):
            kernel = KernelExecutionPayload(
                session_id="ane_integration_test",
                kernel_type=kt,
                step_index=0,
                dispatch_index=i,
                execution_time_us=150 + (i * 10),
                iosurface_format="[1,C,1,S]",
                compute_attribution=HybridComputeAttribution(
                    compute_unit="ane",
                    ane_percentage=90.0,
                    cpu_percentage=10.0,
                ),
            )
            kernels.append(kernel)

        assert len(kernels) == 6
        total_time = sum(k.execution_time_us for k in kernels)
        assert total_time == 150 + 160 + 170 + 180 + 190 + 200  # 1050 us

        # 4. Create compile artifact
        artifact = CompileArtifactPayload(
            artifact_id="art_integration_test",
            session_id="ane_integration_test",
            mil_program_hash="sha256:" + "i" * 56,
            fusion_optimizations=[
                MILFusionOptimization(
                    fusion_name="test_fusion",
                    source_ops=["op1", "op2"],
                    target_op="fused_op",
                    speedup_factor=1.5,
                ),
            ],
            created_at=datetime.now(timezone.utc),
        )

        # 5. Create telemetry
        telemetry = TrainingTelemetryPayload(
            session_id="ane_integration_test",
            measurement_window_seconds=60,
            steps_in_window=100,
            avg_ms_per_step=9.3,
            avg_ane_utilization=11.2,
            tflops_achieved=3.2,
            timestamp=datetime.now(timezone.utc),
        )

        # Verify all components
        assert hw_profile.ane_available is True
        assert session_payload.dmca_1201f_claim is True
        assert len(kernels) == 6
        assert len(artifact.fusion_optimizations) == 1
        assert telemetry.avg_ms_per_step == 9.3

    def test_mlx_gpu_training_flow(self):
        """Test complete MLX GPU training session flow."""
        # 1. Create hardware profile with GPU capabilities
        hw_profile = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Max",
            ane_available=True,
            ane_tops=38.0,
            gpu_core_count=40,
            gpu_tflops=14.0,
            metal_version="3.2",
            metal_family="apple9",
            mps_available=True,
            mlx_version="0.20.0",
            frameworks_used=["mlx"],
            unified_memory_gb=128.0,
            device_id_hash="sha256:" + "j" * 56,
        )

        # 2. Create MLX training session
        session_payload = ANETrainingSessionPayload(
            session_id="mlx_integration_test",
            model_id="qwen_7b_mlx",
            model_name="Qwen 3.5 7B (MLX Fine-tune)",
            hardware_profile_id="hw_mlx_test",
            started_at=datetime.now(timezone.utc),
            status="running",
            total_steps=1000,
        )

        # 3. Create MLX kernel executions
        mlx_kernels = ["mlx_matmul", "mlx_attention", "mlx_rope", "mlx_rms_norm"]
        kernels = []
        for i, kt in enumerate(mlx_kernels):
            kernel = KernelExecutionPayload(
                session_id="mlx_integration_test",
                accelerator_type="mlx",
                kernel_type=kt,
                step_index=0,
                dispatch_index=i,
                execution_time_us=100 + (i * 20),
                mlx_graph_hash="sha256:" + "k" * 56,
                compute_attribution=HybridComputeAttribution(
                    compute_unit="gpu",
                    gpu_percentage=100.0,
                    ane_percentage=0.0,
                    cpu_percentage=0.0,
                ),
            )
            kernels.append(kernel)

        # 4. Create MLX artifact
        artifact = CompileArtifactPayload(
            artifact_id="art_mlx_integration",
            session_id="mlx_integration_test",
            artifact_format="mlx",
            mlx_graph_hash="sha256:" + "l" * 56,
            mlx_version="0.20.0",
            mlx_simplifications=["fuse_matmul_bias", "constant_folding"],
            target_accelerator="gpu",
            created_at=datetime.now(timezone.utc),
        )

        # 5. Create GPU telemetry
        telemetry = TrainingTelemetryPayload(
            session_id="mlx_integration_test",
            measurement_window_seconds=60,
            steps_in_window=200,
            avg_ms_per_step=5.0,
            avg_gpu_utilization=85.0,
            peak_gpu_utilization=95.0,
            gpu_memory_used_gb=24.0,
            gpu_tflops=12.0,
            primary_accelerator="gpu",
            timestamp=datetime.now(timezone.utc),
        )

        # Verify MLX flow
        assert hw_profile.mlx_version == "0.20.0"
        assert "mlx" in hw_profile.frameworks_used
        assert all(k.accelerator_type == "mlx" for k in kernels)
        assert artifact.artifact_format == "mlx"
        assert telemetry.primary_accelerator == "gpu"

    def test_hybrid_ane_mlx_training_flow(self):
        """Test hybrid training using both ANE and MLX."""
        # Hardware with both ANE and GPU
        hw_profile = HardwareProfilePayload(
            device_class="mac",
            chip_identifier="M4",
            chip_variant="Pro",
            ane_available=True,
            ane_tops=38.0,
            gpu_core_count=20,
            gpu_tflops=10.0,
            metal_version="3.2",
            mlx_version="0.20.0",
            frameworks_used=["mlx", "coreml"],  # Both frameworks
            device_id_hash="sha256:" + "h" * 56,
        )

        # Create kernels from both accelerators
        ane_kernels = []
        mlx_kernels = []

        # ANE handles attention
        for i, kt in enumerate(["kFwdAttn", "kSdpaBwd1", "kSdpaBwd2"]):
            kernel = KernelExecutionPayload(
                session_id="hybrid_test",
                accelerator_type="ane",
                kernel_type=kt,
                step_index=0,
                dispatch_index=i,
                execution_time_us=150,
                ane_program_hash="sha256:" + "a" * 56,
            )
            ane_kernels.append(kernel)

        # MLX handles FFN
        for i, kt in enumerate(["mlx_matmul", "mlx_rms_norm"]):
            kernel = KernelExecutionPayload(
                session_id="hybrid_test",
                accelerator_type="mlx",
                kernel_type=kt,
                step_index=0,
                dispatch_index=i + 3,
                execution_time_us=120,
                mlx_graph_hash="sha256:" + "m" * 56,
            )
            mlx_kernels.append(kernel)

        # Telemetry shows hybrid usage
        telemetry = TrainingTelemetryPayload(
            session_id="hybrid_test",
            measurement_window_seconds=60,
            steps_in_window=300,
            avg_ms_per_step=8.0,
            avg_ane_utilization=40.0,
            avg_gpu_utilization=45.0,
            gpu_tflops=4.5,
            ane_tflops=5.0,
            primary_accelerator="ane",
            compute_attribution=HybridComputeAttribution(
                compute_unit="hybrid",
                ane_percentage=50.0,
                gpu_percentage=45.0,
                cpu_percentage=5.0,
            ),
            timestamp=datetime.now(timezone.utc),
        )

        # Verify hybrid setup
        assert "mlx" in hw_profile.frameworks_used
        assert "coreml" in hw_profile.frameworks_used
        assert len(ane_kernels) == 3
        assert len(mlx_kernels) == 2
        assert telemetry.compute_attribution.compute_unit == "hybrid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
