"""Contracts for semantic extraction and processing-budget routing."""

from .core_bridge import (
    CORE_SHADOW_RESULT_SCHEMA_VERSION,
    CoreShadowResult,
    run_core_shadow,
)
from .conversation_accumulation import (
    CONVERSATION_ACCUMULATION_SCHEMA_VERSION,
    ConversationAccumulation,
    load_conversation_accumulation,
    parse_conversation_accumulation,
)
from .processing_plan import (
    PROCESSING_PLAN_SCHEMA_VERSION,
    ProcessingPlan,
    build_processing_plan,
    parse_processing_plan,
)
from .baseline import extract_semantic_packet
from .benchmark import (
    PLM_BENCHMARK_SCHEMA_VERSION,
    PLMBenchmark,
    PLMBenchmarkCase,
    load_plm_benchmark,
    parse_plm_benchmark,
)
from .evaluation import evaluate_plm_extractor
from .review_store import PLMReviewStore
from .accumulation_review_store import (
    ACCUMULATION_REVIEW_SCHEMA_VERSION,
    AccumulationReviewStore,
    review_overlay,
    validate_expected,
)
from .intent_model import (
    INTENT_MODEL_SCHEMA_VERSION,
    IntentModel,
    IntentPrediction,
    load_intent_corpus,
)
from .adapter import (
    DEFAULT_INTENT_MODEL_PATH,
    RouteResult,
    route,
)
from .executor import (
    DEFAULT_MODEL_TIERS,
    DEFAULT_REASONING_ALLOWANCE,
    MAX_REQUEST_TOKENS,
    RequestBudget,
    looks_like_reasoning_model,
    resolve_request_budget,
    select_model,
)
from .runtime import (
    INSTRUCTION,
    ExecutionResult,
    build_system_prompt,
    lmstudio_available_models,
    lmstudio_chat_fn,
    route_and_execute,
)
from .direct import DirectAnswer, direct_response
from .collection_store import (
    COLLECTION_STAGING_SCHEMA,
    apply_reviews,
    approved_corpus_examples,
    ingest as ingest_collection,
    load_campaign_inputs,
    load_corpus_inputs,
)
from .tools import (
    DEFAULT_TOOL_REGISTRY,
    ToolResult,
    calculator,
    run_tools,
    safe_eval,
)
from .server import handle as handle_request, make_handler, serve
from .intent_deployment import (
    GATE_REPORT_SCHEMA_VERSION as INTENT_GATE_REPORT_SCHEMA_VERSION,
    evaluate_intent_gate,
    evaluate_intent_kfold,
    promote_intent_model,
    rollback_intent_model,
    run_intent_deployment_gate,
)
from .sealed_fixture import (
    PLM_SEALED_FIXTURE_SCHEMA_VERSION,
    PLMSealedFixture,
    parse_plm_sealed_fixture,
)
from .semantic_packet import (
    SEMANTIC_PACKET_SCHEMA_VERSION,
    SemanticPacket,
    parse_semantic_packet,
    request_digest,
)

__all__ = [
    "CORE_SHADOW_RESULT_SCHEMA_VERSION",
    "CONVERSATION_ACCUMULATION_SCHEMA_VERSION",
    "PROCESSING_PLAN_SCHEMA_VERSION",
    "SEMANTIC_PACKET_SCHEMA_VERSION",
    "ProcessingPlan",
    "CoreShadowResult",
    "ConversationAccumulation",
    "PLM_BENCHMARK_SCHEMA_VERSION",
    "PLMBenchmark",
    "PLMBenchmarkCase",
    "PLMReviewStore",
    "ACCUMULATION_REVIEW_SCHEMA_VERSION",
    "AccumulationReviewStore",
    "review_overlay",
    "validate_expected",
    "INTENT_MODEL_SCHEMA_VERSION",
    "IntentModel",
    "IntentPrediction",
    "load_intent_corpus",
    "DEFAULT_INTENT_MODEL_PATH",
    "RouteResult",
    "route",
    "DEFAULT_REASONING_ALLOWANCE",
    "MAX_REQUEST_TOKENS",
    "RequestBudget",
    "looks_like_reasoning_model",
    "resolve_request_budget",
    "DEFAULT_MODEL_TIERS",
    "select_model",
    "INSTRUCTION",
    "ExecutionResult",
    "build_system_prompt",
    "lmstudio_available_models",
    "lmstudio_chat_fn",
    "route_and_execute",
    "DEFAULT_TOOL_REGISTRY",
    "ToolResult",
    "calculator",
    "run_tools",
    "safe_eval",
    "DirectAnswer",
    "direct_response",
    "COLLECTION_STAGING_SCHEMA",
    "apply_reviews",
    "approved_corpus_examples",
    "ingest_collection",
    "load_campaign_inputs",
    "load_corpus_inputs",
    "handle_request",
    "make_handler",
    "serve",
    "INTENT_GATE_REPORT_SCHEMA_VERSION",
    "evaluate_intent_gate",
    "evaluate_intent_kfold",
    "promote_intent_model",
    "rollback_intent_model",
    "run_intent_deployment_gate",
    "PLM_SEALED_FIXTURE_SCHEMA_VERSION",
    "PLMSealedFixture",
    "SemanticPacket",
    "build_processing_plan",
    "evaluate_plm_extractor",
    "extract_semantic_packet",
    "load_plm_benchmark",
    "load_conversation_accumulation",
    "parse_processing_plan",
    "parse_conversation_accumulation",
    "parse_plm_benchmark",
    "parse_semantic_packet",
    "parse_plm_sealed_fixture",
    "request_digest",
    "run_core_shadow",
]
