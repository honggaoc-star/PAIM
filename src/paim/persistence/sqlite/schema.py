"""SQLAlchemy Core metadata for the PAIM integrity and Increment 2 schema."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

records = Table(
    "records",
    metadata,
    Column("record_id", String(36), primary_key=True),
    Column("family", Text, nullable=False),
    Column("scope", Text, nullable=False),
    UniqueConstraint("record_id", "family", "scope", name="uq_record_identity_scope"),
)

record_versions = Table(
    "record_versions",
    metadata,
    Column("version_id", String(36), primary_key=True),
    Column("record_id", String(36), ForeignKey("records.record_id"), nullable=False),
    Column("content_json", Text, nullable=False),
    Column("finalized", Boolean, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    Column("creator", Text, nullable=False),
    CheckConstraint(
        "effective_to_us IS NULL OR effective_to_us > effective_from_us",
        name="ck_version_effective_interval",
    ),
)
Index(
    "ix_versions_scope_time",
    record_versions.c.record_id,
    record_versions.c.effective_from_us,
    record_versions.c.effective_to_us,
    record_versions.c.recorded_at_us,
)
Index(
    "ix_versions_reconstruction_cutoff",
    record_versions.c.recorded_at_us,
    record_versions.c.effective_from_us,
    record_versions.c.record_id,
)

status_events = Table(
    "status_events",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column(
        "target_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("prior_status", Text, nullable=False),
    Column("new_status", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("actor", Text, nullable=False),
    Column("basis", Text, nullable=False),
)
Index(
    "ix_status_target_time",
    status_events.c.target_version_id,
    status_events.c.effective_at_us,
    status_events.c.recorded_at_us,
)

version_relationships = Table(
    "version_relationships",
    metadata,
    Column("relationship_id", String(36), primary_key=True),
    Column(
        "source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "target_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("relationship_type", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("reason", Text, nullable=False),
    CheckConstraint(
        "source_version_id <> target_version_id", name="ck_relationship_distinct_versions"
    ),
)
Index(
    "ix_relationship_source_target",
    version_relationships.c.source_version_id,
    version_relationships.c.target_version_id,
)

idempotency_facts = Table(
    "idempotency_facts",
    metadata,
    Column("scope", Text, primary_key=True),
    Column("idempotency_key", Text, primary_key=True),
    Column("digest", String(64), nullable=False),
    Column("command_id", String(36), nullable=False),
    Column("outcome_json", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
)

audit_facts = Table(
    "audit_facts",
    metadata,
    Column("audit_id", String(36), primary_key=True),
    Column("principal_id", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("actor_resolution", Text, nullable=False),
    Column("operation", Text, nullable=False),
    Column("result", Text, nullable=False),
    Column("command_id", String(36), nullable=False),
    Column("idempotency_scope", Text, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("correlation_id", Text, nullable=True),
    Column("causation_id", Text, nullable=True),
    Column("target_record_id", String(36), ForeignKey("records.record_id"), nullable=False),
    Column("affected_version_ids_json", Text, nullable=False),
    Column("expected_precondition", Text, nullable=False),
    Column("observed_precondition", Text, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("reason_outcomes_json", Text, nullable=False),
    Column("request_digest", String(64), nullable=False),
    CheckConstraint(
        "(actor_resolution = 'provided' AND actor_id IS NOT NULL) OR "
        "(actor_resolution IN ('unresolved', 'not_applicable') AND actor_id IS NULL)",
        name="ck_audit_actor_resolution",
    ),
)

paim_cases = Table(
    "paim_cases",
    metadata,
    Column("case_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

paim_case_versions = Table(
    "paim_case_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("initial_lifecycle_state", Text, nullable=False),
    CheckConstraint("initial_lifecycle_state = 'open'", name="ck_case_initial_state_open"),
)
Index("ix_case_versions_case", paim_case_versions.c.case_id)

paim_case_links = Table(
    "paim_case_links",
    metadata,
    Column("link_id", String(36), primary_key=True),
    Column("source_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("target_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("relationship_type", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("actor_id", String(36), nullable=False),
    Column("reason", Text, nullable=False),
    CheckConstraint("source_case_id <> target_case_id", name="ck_case_link_distinct_cases"),
)
Index(
    "ix_case_links_cases_time",
    paim_case_links.c.source_case_id,
    paim_case_links.c.target_case_id,
    paim_case_links.c.effective_at_us,
)

managed_configurations = Table(
    "managed_configurations",
    metadata,
    Column("configuration_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("owning_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
)
Index("ix_configurations_owning_case", managed_configurations.c.owning_case_id)

managed_configuration_versions = Table(
    "managed_configuration_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column("maturity", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    CheckConstraint("maturity IN ('draft', 'finalized')", name="ck_configuration_maturity"),
    CheckConstraint(
        "purpose IN ('candidate', 'proposed', 'experimental', 'alternative', 'fallback')",
        name="ck_configuration_purpose",
    ),
)
Index("ix_configuration_versions_identity", managed_configuration_versions.c.configuration_id)

paim_actors = Table(
    "paim_actors",
    metadata,
    Column("actor_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

paim_actor_versions = Table(
    "paim_actor_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)
Index("ix_actor_versions_identity", paim_actor_versions.c.actor_id)

role_assignments = Table(
    "role_assignments",
    metadata,
    Column("assignment_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

role_assignment_versions = Table(
    "role_assignment_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "assignment_id",
        String(36),
        ForeignKey("role_assignments.assignment_id"),
        nullable=False,
    ),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("role", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("case_context_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column("accountable", Boolean, nullable=False),
    Column("compatibility_key", Text, nullable=False),
    Column("delegation_effect", Text, nullable=False),
    Column(
        "delegated_from_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "target_type IN ('organization', 'business_unit', 'case', 'configuration', "
        "'decision', 'intervention', 'authority_domain', "
        "'dependency_candidate_set', 'shared_dependency')",
        name="ck_role_target_type",
    ),
    CheckConstraint(
        "(target_type IN ('organization', 'business_unit') AND case_context_id IS NULL) OR "
        "(target_type = 'case' AND case_context_id = target_id) OR "
        "(target_type = 'configuration' AND case_context_id IS NOT NULL) OR "
        "(target_type IN ('decision', 'intervention', 'authority_domain', "
        "'dependency_candidate_set', 'shared_dependency'))",
        name="ck_role_case_context",
    ),
    CheckConstraint(
        "delegation_effect IN ('none', 'supplement', 'transfer', 'retain')",
        name="ck_role_delegation_effect",
    ),
    CheckConstraint(
        "(delegation_effect = 'none' AND delegated_from_version_id IS NULL) OR "
        "(delegation_effect <> 'none' AND delegated_from_version_id IS NOT NULL)",
        name="ck_role_delegation_source",
    ),
)
Index(
    "ix_role_assignments_resolution",
    role_assignment_versions.c.role,
    role_assignment_versions.c.target_type,
    role_assignment_versions.c.target_id,
    role_assignment_versions.c.case_context_id,
)

governing_configuration_designations = Table(
    "governing_configuration_designations",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_governing_accountability_exactly_one",
    ),
)
Index("ix_governing_designation_case", governing_configuration_designations.c.case_id)

configuration_determinations = Table(
    "configuration_determinations",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("determination_kind", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "determination_kind IN ('materiality', 'identity_continuity')",
        name="ck_determination_kind",
    ),
    CheckConstraint(
        "(determination_kind = 'materiality' AND outcome IN ('material', 'non_material')) OR "
        "(determination_kind = 'identity_continuity' AND "
        "outcome IN ('same_identity', 'new_identity'))",
        name="ck_determination_outcome",
    ),
    CheckConstraint("length(trim(rationale)) > 0", name="ck_determination_rationale"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_determination_accountability_exactly_one",
    ),
)
Index(
    "ix_determination_configuration_kind",
    configuration_determinations.c.configuration_version_id,
    configuration_determinations.c.determination_kind,
)

evidence_records = Table(
    "evidence_records",
    metadata,
    Column("evidence_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

evidence_versions = Table(
    "evidence_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("evidence_id", String(36), ForeignKey("evidence_records.evidence_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("classification", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    Column("observed_at_us", BigInteger, nullable=True),
    Column("attention", Text, nullable=False),
    CheckConstraint(
        "classification IN ('observed', 'supported_inference', "
        "'estimate', 'assumption', 'unknown')",
        name="ck_evidence_classification",
    ),
    CheckConstraint(
        "attention IN ('current', 'refresh_required', 'stale')",
        name="ck_evidence_attention",
    ),
)
Index(
    "ix_evidence_versions_context",
    evidence_versions.c.evidence_id,
    evidence_versions.c.configuration_version_id,
)

authority_records = Table(
    "authority_records",
    metadata,
    Column("authority_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

authority_record_versions = Table(
    "authority_record_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "authority_id", String(36), ForeignKey("authority_records.authority_id"), nullable=False
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("category", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("requirement", Text, nullable=False),
)
Index(
    "ix_authority_versions_context",
    authority_record_versions.c.authority_id,
    authority_record_versions.c.configuration_version_id,
)

authority_gaps = Table(
    "authority_gaps",
    metadata,
    Column("gap_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

authority_gap_versions = Table(
    "authority_gap_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("gap_id", String(36), ForeignKey("authority_gaps.gap_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("question_id", Text, nullable=False),
    Column("question", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
)
Index(
    "ix_authority_gaps_context",
    authority_gap_versions.c.case_id,
    authority_gap_versions.c.configuration_version_id,
)

exact_evidence_links = Table(
    "exact_evidence_links",
    metadata,
    Column(
        "source_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
    Column("link_role", Text, primary_key=True),
)

affected_use_references = Table(
    "affected_use_references",
    metadata,
    Column(
        "source_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column("use_reference", Text, primary_key=True),
)

evidence_applicability_records = Table(
    "evidence_applicability_records",
    metadata,
    Column("applicability_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

evidence_applicability_versions = Table(
    "evidence_applicability_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "applicability_id",
        String(36),
        ForeignKey("evidence_applicability_records.applicability_id"),
        nullable=False,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        nullable=False,
    ),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column(
        "target_version_id", String(36), ForeignKey("record_versions.version_id"), nullable=True
    ),
    Column("purpose", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=True,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("outcome", Text, nullable=False),
    Column("conditions_json", Text, nullable=False),
    Column("limitations_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("assessor_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "target_type IN ('managed_configuration_version', 'value_input_version', "
        "'risk_input_version', 'authority_record_version', 'authority_gap')",
        name="ck_applicability_target_type",
    ),
    CheckConstraint(
        "outcome IN ('APPLICABLE', 'CONDITIONALLY_APPLICABLE', 'PARTIALLY_APPLICABLE', "
        "'NOT_APPLICABLE', 'INDETERMINATE')",
        name="ck_applicability_outcome",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_applicability_accountability_exactly_one",
    ),
)
Index(
    "ix_applicability_exact_context",
    evidence_applicability_versions.c.evidence_version_id,
    evidence_applicability_versions.c.target_type,
    evidence_applicability_versions.c.target_id,
    evidence_applicability_versions.c.target_version_id,
    evidence_applicability_versions.c.purpose,
    evidence_applicability_versions.c.assessed_scope,
)

analytical_inputs = Table(
    "analytical_inputs",
    metadata,
    Column("input_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("lane", Text, nullable=False),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_analytical_input_lane"),
)

analytical_input_versions = Table(
    "analytical_input_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("input_id", String(36), ForeignKey("analytical_inputs.input_id"), nullable=False),
    Column("lane", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("purpose", Text, nullable=False),
    Column("finding", Text, nullable=False),
    Column("boundary", Text, nullable=False),
    Column("uncertainties_json", Text, nullable=False),
    Column("implication", Text, nullable=False),
    Column("provenance_json", Text, nullable=False),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_analytical_input_version_lane"),
)
Index(
    "ix_analytical_inputs_selection_context",
    analytical_input_versions.c.lane,
    analytical_input_versions.c.configuration_version_id,
    analytical_input_versions.c.purpose,
)

candidate_dispositions = Table(
    "candidate_dispositions",
    metadata,
    Column("disposition_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

candidate_disposition_versions = Table(
    "candidate_disposition_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "disposition_id",
        String(36),
        ForeignKey("candidate_dispositions.disposition_id"),
        nullable=False,
    ),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("disposition", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_candidate_disposition_lane"),
    CheckConstraint(
        "disposition IN ('NON_SELECTED', 'DISSENTING', 'REJECTED_FOR_USE', "
        "'WITHDRAWN', 'SUPERSEDED')",
        name="ck_candidate_disposition_outcome",
    ),
)
Index(
    "ix_candidate_disposition_context",
    candidate_disposition_versions.c.input_version_id,
    candidate_disposition_versions.c.use_context,
    candidate_disposition_versions.c.purpose,
)

lane_fitness_records = Table(
    "lane_fitness_records",
    metadata,
    Column("fitness_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

lane_fitness_versions = Table(
    "lane_fitness_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("fitness_id", String(36), ForeignKey("lane_fitness_records.fitness_id"), nullable=False),
    Column("lane", Text, nullable=False),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("indeterminate_treatment", Text, nullable=True),
    Column("decision_limiting", Boolean, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_lane_fitness_lane"),
    CheckConstraint("outcome IN ('SUPPORTABLE', 'BLOCKED')", name="ck_lane_fitness_outcome"),
    CheckConstraint("length(trim(rationale)) > 0", name="ck_lane_fitness_rationale"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_lane_fitness_accountability_exactly_one",
    ),
)
Index(
    "ix_lane_fitness_context",
    lane_fitness_versions.c.lane,
    lane_fitness_versions.c.configuration_version_id,
    lane_fitness_versions.c.use_context,
    lane_fitness_versions.c.purpose,
)

material_evidence_basis = Table(
    "material_evidence_basis",
    metadata,
    Column(
        "fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "applicability_version_id",
        String(36),
        ForeignKey("evidence_applicability_versions.version_id"),
        primary_key=True,
    ),
    Column("role", Text, nullable=False),
    Column("required_support", Boolean, nullable=False),
    Column("claimed_scope", Text, nullable=False),
)

input_acceptance_records = Table(
    "input_acceptance_records",
    metadata,
    Column("acceptance_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

input_acceptance_versions = Table(
    "input_acceptance_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "acceptance_id",
        String(36),
        ForeignKey("input_acceptance_records.acceptance_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column(
        "input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column(
        "fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    CheckConstraint("lane IN ('VALUE', 'RISK')", name="ck_input_acceptance_lane"),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_input_acceptance_accountability_exactly_one",
    ),
)
Index(
    "ix_input_acceptance_selection_context",
    input_acceptance_versions.c.lane,
    input_acceptance_versions.c.configuration_version_id,
    input_acceptance_versions.c.use_context,
    input_acceptance_versions.c.purpose,
)

# Increment 4 authoritative Integration, Boundary, Decision, and authorization families.
integration_records = Table(
    "integration_records",
    metadata,
    Column("integration_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)

integration_versions = Table(
    "integration_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("use_context", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column(
        "value_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_acceptance_version_id",
        String(36),
        ForeignKey("input_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_acceptance_version_id",
        String(36),
        ForeignKey("input_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_fitness_version_id",
        String(36),
        ForeignKey("lane_fitness_versions.version_id"),
        nullable=False,
    ),
    Column("integrator_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('draft','ready','in_progress','completed','decision_pending',"
        "'superseded','withdrawn')",
        name="ck_integration_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_integration_accountability",
    ),
)
Index(
    "ix_integration_context_time",
    integration_versions.c.case_id,
    integration_versions.c.configuration_version_id,
    integration_versions.c.use_context,
    integration_versions.c.purpose,
)

integration_material_applicability = Table(
    "integration_material_applicability",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "applicability_version_id",
        String(36),
        ForeignKey("evidence_applicability_versions.version_id"),
        primary_key=True,
    ),
)
integration_authority_records = Table(
    "integration_authority_records",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "authority_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        primary_key=True,
    ),
)
integration_authority_gaps = Table(
    "integration_authority_gaps",
    metadata,
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

uncertainty_classification_records = Table(
    "uncertainty_classification_records",
    metadata,
    Column("classification_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
uncertainty_classification_versions = Table(
    "uncertainty_classification_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "classification_id",
        String(36),
        ForeignKey("uncertainty_classification_records.classification_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column("proposed_decision_context", Text, nullable=False),
    Column("proposed_operating_state", Text, nullable=False),
    Column("source_reference", Text, nullable=False),
    Column(
        "source_input_version_id",
        String(36),
        ForeignKey("analytical_input_versions.version_id"),
        nullable=True,
    ),
    Column(
        "source_evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        nullable=True,
    ),
    Column("classification", Text, nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "classification IN ('ACCEPTED_UNCERTAINTY','DECISION_LIMITING_UNCERTAINTY')",
        name="ck_uncertainty_classification",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_uncertainty_accountability",
    ),
)
Index(
    "ix_uncertainty_decision_context",
    uncertainty_classification_versions.c.integration_version_id,
    uncertainty_classification_versions.c.proposed_decision_context,
    uncertainty_classification_versions.c.proposed_operating_state,
)

boundary_snapshot_records = Table(
    "boundary_snapshot_records",
    metadata,
    Column("snapshot_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_snapshot_versions = Table(
    "boundary_snapshot_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "snapshot_id",
        String(36),
        ForeignKey("boundary_snapshot_records.snapshot_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('draft','finalized','superseded','withdrawn')",
        name="ck_boundary_snapshot_status",
    ),
)
Index(
    "ix_boundary_context",
    boundary_snapshot_versions.c.case_id,
    boundary_snapshot_versions.c.configuration_version_id,
    boundary_snapshot_versions.c.integration_version_id,
)

boundary_clause_records = Table(
    "boundary_clause_records",
    metadata,
    Column("clause_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_clause_versions = Table(
    "boundary_clause_versions",
    metadata,
    Column(
        "clause_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column(
        "clause_id", String(36), ForeignKey("boundary_clause_records.clause_id"), nullable=False
    ),
    Column(
        "snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("clause_type", Text, nullable=False),
    Column("effect", Text, nullable=False),
    Column("target_reference", Text, nullable=True),
    Column("structured_reference", Text, nullable=True),
    Column("operator", Text, nullable=True),
    Column("structured_value", Text, nullable=True),
    Column("unit", Text, nullable=True),
    Column("narrative", Text, nullable=False),
    Column("verification_mode", Text, nullable=False),
    CheckConstraint(
        "effect IN ('permitted','excluded','required','limited','conditional','indeterminate')",
        name="ck_boundary_clause_effect",
    ),
    CheckConstraint(
        "verification_mode IN ('mechanically_testable','human_determination_required',"
        "'external_determination_required','indeterminate')",
        name="ck_boundary_clause_verification",
    ),
    CheckConstraint(
        "verification_mode <> 'mechanically_testable' OR "
        "(operator IS NOT NULL AND structured_value IS NOT NULL)",
        name="ck_boundary_mechanical_structure",
    ),
)
Index(
    "ix_boundary_clause_snapshot",
    boundary_clause_versions.c.snapshot_version_id,
    boundary_clause_versions.c.clause_type,
    boundary_clause_versions.c.target_reference,
)

boundary_determination_records = Table(
    "boundary_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
boundary_determination_versions = Table(
    "boundary_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("boundary_determination_records.determination_id"),
        nullable=False,
    ),
    Column(
        "snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "clause_id", String(36), ForeignKey("boundary_clause_records.clause_id"), nullable=False
    ),
    Column(
        "clause_version_id",
        String(36),
        ForeignKey("boundary_clause_versions.clause_version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    CheckConstraint(
        "outcome IN ('PASS','BREACH','INDETERMINATE')", name="ck_boundary_determination_outcome"
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_boundary_determination_accountability",
    ),
)
Index(
    "ix_boundary_determination_context",
    boundary_determination_versions.c.snapshot_version_id,
    boundary_determination_versions.c.clause_version_id,
)
boundary_determination_evidence = Table(
    "boundary_determination_evidence",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("boundary_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

decision_records = Table(
    "decision_records",
    metadata,
    Column("decision_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_versions = Table(
    "decision_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("decision_id", String(36), ForeignKey("decision_records.decision_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "integration_id",
        String(36),
        ForeignKey("integration_records.integration_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("integration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_id",
        String(36),
        ForeignKey("boundary_snapshot_records.snapshot_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("proposed_action", Text, nullable=False),
    Column("operating_state", Text, nullable=False),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('proposed','pending_authorization','authorized','superseded',"
        "'withdrawn','expired')",
        name="ck_decision_status",
    ),
)
Index(
    "ix_decision_current_context",
    decision_versions.c.case_id,
    decision_versions.c.configuration_version_id,
)

decision_uncertainty_links = Table(
    "decision_uncertainty_links",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "classification_version_id",
        String(36),
        ForeignKey("uncertainty_classification_versions.version_id"),
        primary_key=True,
    ),
    Column("classification", Text, nullable=False),
)
decision_authority_records = Table(
    "decision_authority_records",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "authority_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        primary_key=True,
    ),
)
decision_authority_gaps = Table(
    "decision_authority_gaps",
    metadata,
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

bounded_proceed_records = Table(
    "bounded_proceed_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
bounded_proceed_versions = Table(
    "bounded_proceed_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("bounded_proceed_records.determination_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "unresolved_gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        nullable=False,
    ),
    Column("blocked_broader_decision", Text, nullable=False),
    Column("narrower_scope", Text, nullable=False),
    Column("operating_state", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("authority_mechanism", Text, nullable=True),
    Column(
        "authority_record_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "(authority_assignment_version_id IS NOT NULL AND authority_mechanism IS NULL) OR "
        "(authority_assignment_version_id IS NULL AND authority_mechanism IS NOT NULL)",
        name="ck_bounded_proceed_authority",
    ),
    CheckConstraint(
        "authority_record_version_id IS NOT NULL OR authority_mechanism IS NOT NULL",
        name="ck_bounded_proceed_authority_source",
    ),
)
bounded_proceed_delegations = Table(
    "bounded_proceed_delegations",
    metadata,
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)
bounded_proceed_boundary_clauses = Table(
    "bounded_proceed_boundary_clauses",
    metadata,
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "clause_version_id",
        String(36),
        ForeignKey("boundary_clause_versions.clause_version_id"),
        primary_key=True,
    ),
)

decision_authorization_basis_records = Table(
    "decision_authorization_basis_records",
    metadata,
    Column("basis_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_authorization_basis_versions = Table(
    "decision_authorization_basis_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "basis_id",
        String(36),
        ForeignKey("decision_authorization_basis_records.basis_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column("decision_authority_identity", Text, nullable=False),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("authority_mechanism", Text, nullable=True),
    Column(
        "authority_record_version_id",
        String(36),
        ForeignKey("authority_record_versions.version_id"),
        nullable=True,
    ),
    Column("authorized_scope", Text, nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("operating_state_coverage_json", Text, nullable=False),
    Column("decision_type", Text, nullable=False),
    Column("organizational_unit", Text, nullable=True),
    Column("authorization_event_id", String(36), nullable=False, unique=True),
    Column(
        "authorization_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False
    ),
    Column("authorization_effective_at_us", BigInteger, nullable=False),
    Column(
        "bounded_proceed_version_id",
        String(36),
        ForeignKey("bounded_proceed_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "(authority_assignment_version_id IS NOT NULL AND authority_mechanism IS NULL) OR "
        "(authority_assignment_version_id IS NULL AND authority_mechanism IS NOT NULL)",
        name="ck_decision_authorization_authority",
    ),
    CheckConstraint(
        "authority_record_version_id IS NOT NULL OR authority_mechanism IS NOT NULL",
        name="ck_decision_authorization_source",
    ),
)
Index(
    "ix_authorization_decision",
    decision_authorization_basis_versions.c.decision_version_id,
    decision_authorization_basis_versions.c.authorization_effective_at_us,
)
decision_authorization_delegations = Table(
    "decision_authorization_delegations",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)
decision_authorization_gaps = Table(
    "decision_authorization_gaps",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "gap_version_id",
        String(36),
        ForeignKey("authority_gap_versions.version_id"),
        primary_key=True,
    ),
)

# Increment 5 authoritative Intervention, activation, and Learning families.
decision_preauthorized_activation_mechanisms = Table(
    "decision_preauthorized_activation_mechanisms",
    metadata,
    Column("mechanism_version_id", String(36), primary_key=True),
    Column("mechanism_id", String(36), nullable=False),
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    CheckConstraint(
        "effective_to_us IS NULL OR effective_to_us > effective_from_us",
        name="ck_activation_mechanism_effective",
    ),
)
Index(
    "ix_activation_mechanism_basis",
    decision_preauthorized_activation_mechanisms.c.basis_version_id,
    decision_preauthorized_activation_mechanisms.c.mechanism_id,
)

intervention_records = Table(
    "intervention_records",
    metadata,
    Column("intervention_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
intervention_versions = Table(
    "intervention_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    CheckConstraint(
        "status IN ('PROPOSED','PLANNED','IN_PROGRESS','BLOCKED','PARTIALLY_COMPLETED',"
        "'COMPLETED','FAILED','CANCELLED','SUPERSEDED')",
        name="ck_intervention_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_intervention_accountability",
    ),
)
Index(
    "ix_intervention_context",
    intervention_versions.c.case_id,
    intervention_versions.c.decision_version_id,
    intervention_versions.c.configuration_version_id,
)

obligation_set_records = Table(
    "obligation_set_records",
    metadata,
    Column("obligation_set_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
obligation_set_versions = Table(
    "obligation_set_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "obligation_set_id",
        String(36),
        ForeignKey("obligation_set_records.obligation_set_id"),
        nullable=False,
    ),
    Column("decision_id", String(36), ForeignKey("decision_records.decision_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
)
Index(
    "ix_obligation_set_context_time",
    obligation_set_versions.c.decision_version_id,
    obligation_set_versions.c.configuration_version_id,
)

obligation_records = Table(
    "obligation_records",
    metadata,
    Column("obligation_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
obligation_versions = Table(
    "obligation_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "obligation_id",
        String(36),
        ForeignKey("obligation_records.obligation_id"),
        nullable=False,
    ),
    Column(
        "obligation_set_version_id",
        String(36),
        ForeignKey("obligation_set_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column("requirement_type", Text, nullable=False),
    Column("post_operation_permitted", Boolean, nullable=False),
    Column("post_operation_timing_conditions_json", Text, nullable=False),
    CheckConstraint(
        "requirement_type IN ('REQUIRED_BEFORE_OPERATION','REQUIRED_AFTER_OPERATION','OPTIONAL')",
        name="ck_obligation_requirement_type",
    ),
)
Index(
    "ix_obligation_set_type",
    obligation_versions.c.obligation_set_version_id,
    obligation_versions.c.requirement_type,
)

completion_result_records = Table(
    "completion_result_records",
    metadata,
    Column("result_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_result_versions = Table(
    "completion_result_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "result_id",
        String(36),
        ForeignKey("completion_result_records.result_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("performer_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)
Index(
    "ix_completion_result_obligation",
    completion_result_versions.c.obligation_version_id,
)
completion_result_criteria = Table(
    "completion_result_criteria",
    metadata,
    Column(
        "result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column("criterion", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    CheckConstraint(
        "outcome IN ('MET','NOT_MET','INDETERMINATE')", name="ck_completion_criterion_outcome"
    ),
)
completion_result_evidence = Table(
    "completion_result_evidence",
    metadata,
    Column(
        "result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

completion_acceptor_mechanism_records = Table(
    "completion_acceptor_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_acceptor_mechanism_versions = Table(
    "completion_acceptor_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("completion_acceptor_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "accountable_actor_id",
        String(36),
        ForeignKey("paim_actors.actor_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
)
Index(
    "ix_completion_acceptor_mechanism_context",
    completion_acceptor_mechanism_versions.c.intervention_id,
    completion_acceptor_mechanism_versions.c.decision_version_id,
    completion_acceptor_mechanism_versions.c.configuration_id,
    completion_acceptor_mechanism_versions.c.case_id,
)

completion_acceptance_records = Table(
    "completion_acceptance_records",
    metadata,
    Column("acceptance_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
completion_acceptance_versions = Table(
    "completion_acceptance_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "acceptance_id",
        String(36),
        ForeignKey("completion_acceptance_records.acceptance_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "accountable_mechanism_version_id",
        String(36),
        ForeignKey("completion_acceptor_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint("outcome IN ('ACCEPTED','REJECTED')", name="ck_completion_acceptance_outcome"),
    CheckConstraint(
        "status IN ('CURRENT','WITHDRAWN','SUPERSEDED')",
        name="ck_completion_acceptance_status",
    ),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND "
        "accountable_mechanism_version_id IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND "
        "accountable_mechanism_version_id IS NOT NULL)",
        name="ck_completion_acceptance_accountability",
    ),
)
Index(
    "ix_completion_acceptance_obligation",
    completion_acceptance_versions.c.obligation_version_id,
)
completion_acceptance_delegations = Table(
    "completion_acceptance_delegations",
    metadata,
    Column(
        "acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

intervention_replacement_records = Table(
    "intervention_replacement_records",
    metadata,
    Column("replacement_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
intervention_replacement_versions = Table(
    "intervention_replacement_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "replacement_id",
        String(36),
        ForeignKey("intervention_replacement_records.replacement_id"),
        nullable=False,
    ),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "replacement_intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column("substantive_change", Boolean, nullable=False),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "predecessor_intervention_version_id <> replacement_intervention_version_id",
        name="ck_replacement_distinct_interventions",
    ),
)
Index(
    "ix_replacement_obligation",
    intervention_replacement_versions.c.obligation_version_id,
)

continued_validity_mechanism_records = Table(
    "continued_validity_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
continued_validity_mechanism_versions = Table(
    "continued_validity_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("continued_validity_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column(
        "successor_obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "intervention_id",
        String(36),
        ForeignKey("intervention_records.intervention_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "accountable_actor_id",
        String(36),
        ForeignKey("paim_actors.actor_id"),
        nullable=False,
    ),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
)
Index(
    "ix_continued_validity_mechanism_context",
    continued_validity_mechanism_versions.c.successor_obligation_version_id,
    continued_validity_mechanism_versions.c.decision_version_id,
    continued_validity_mechanism_versions.c.configuration_version_id,
)

continued_validity_records = Table(
    "continued_validity_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
continued_validity_versions = Table(
    "continued_validity_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("continued_validity_records.determination_id"),
        nullable=False,
    ),
    Column(
        "successor_obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        nullable=False,
    ),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "accountable_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "accountable_mechanism_version_id",
        String(36),
        ForeignKey("continued_validity_mechanism_versions.version_id"),
        nullable=True,
    ),
    Column("all_coverage_established", Boolean, nullable=False),
    CheckConstraint(
        "(accountable_assignment_version_id IS NOT NULL AND "
        "accountable_mechanism_version_id IS NULL) OR "
        "(accountable_assignment_version_id IS NULL AND "
        "accountable_mechanism_version_id IS NOT NULL)",
        name="ck_continued_validity_accountability",
    ),
)
Index(
    "ix_continued_validity_obligation",
    continued_validity_versions.c.successor_obligation_version_id,
)
continued_validity_delegations = Table(
    "continued_validity_delegations",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("continued_validity_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

prerequisite_evaluation_basis_records = Table(
    "prerequisite_evaluation_basis_records",
    metadata,
    Column("basis_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prerequisite_evaluation_basis_versions = Table(
    "prerequisite_evaluation_basis_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "basis_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_records.basis_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "obligation_set_version_id",
        String(36),
        ForeignKey("obligation_set_versions.version_id"),
        nullable=False,
    ),
    Column("aggregate_result", Text, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint(
        "aggregate_result IN ('SATISFIED','NOT_REQUIRED','NOT_ESTABLISHED','INCOMPLETE',"
        "'BLOCKED','CONFLICT')",
        name="ck_prerequisite_basis_result",
    ),
)
prerequisite_evaluation_basis_items = Table(
    "prerequisite_evaluation_basis_items",
    metadata,
    Column(
        "basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "obligation_version_id",
        String(36),
        ForeignKey("obligation_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=True,
    ),
    Column(
        "completion_result_version_id",
        String(36),
        ForeignKey("completion_result_versions.version_id"),
        nullable=True,
    ),
    Column(
        "completion_acceptance_version_id",
        String(36),
        ForeignKey("completion_acceptance_versions.version_id"),
        nullable=True,
    ),
    Column(
        "replacement_version_id",
        String(36),
        ForeignKey("intervention_replacement_versions.version_id"),
        nullable=True,
    ),
    Column(
        "reuse_determination_version_id",
        String(36),
        ForeignKey("continued_validity_versions.version_id"),
        nullable=True,
    ),
    Column("result", Text, nullable=False),
    Column("diagnostics_json", Text, nullable=False),
    CheckConstraint(
        "result IN ('SATISFIED','NOT_ESTABLISHED','INCOMPLETE','BLOCKED','CONFLICT')",
        name="ck_prerequisite_item_result",
    ),
)

activation_authorization_records = Table(
    "activation_authorization_records",
    metadata,
    Column("authorization_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
activation_authorization_versions = Table(
    "activation_authorization_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "authorization_id",
        String(36),
        ForeignKey("activation_authorization_records.authorization_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("operating_state", Text, nullable=False),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prerequisite_basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_kind", Text, nullable=False),
    Column("authority_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=True),
    Column(
        "authority_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("decision_preauthorized_activation_mechanisms.mechanism_version_id"),
        nullable=True,
    ),
    Column(
        "decision_authorization_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_scope", Text, nullable=False),
    Column("authority_limits_json", Text, nullable=False),
    Column("authority_effective_from_us", BigInteger, nullable=False),
    Column("authority_effective_to_us", BigInteger, nullable=True),
    Column("activation_effective_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "authority_kind IN ('DECISION_AUTHORITY','ORGANIZATIONAL_MECHANISM')",
        name="ck_activation_authority_kind",
    ),
    CheckConstraint(
        "(authority_kind = 'DECISION_AUTHORITY' AND authority_actor_id IS NOT NULL "
        "AND authority_assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(authority_kind = 'ORGANIZATIONAL_MECHANISM' AND authority_actor_id IS NULL "
        "AND authority_assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_activation_authority_path",
    ),
)
Index(
    "ix_activation_authorization_context",
    activation_authorization_versions.c.decision_version_id,
    activation_authorization_versions.c.configuration_version_id,
    activation_authorization_versions.c.activation_effective_at_us,
)
activation_authorization_delegations = Table(
    "activation_authorization_delegations",
    metadata,
    Column(
        "authorization_version_id",
        String(36),
        ForeignKey("activation_authorization_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

target_activation_events = Table(
    "target_activation_events",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prerequisite_basis_version_id",
        String(36),
        ForeignKey("prerequisite_evaluation_basis_versions.version_id"),
        nullable=False,
    ),
    Column(
        "activation_authorization_version_id",
        String(36),
        ForeignKey("activation_authorization_versions.version_id"),
        nullable=False,
    ),
    Column("operating_state", Text, nullable=False),
    Column("lifecycle_event_id", String(36), ForeignKey("status_events.event_id"), nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
)
Index(
    "ix_target_activation_history",
    target_activation_events.c.case_id,
    target_activation_events.c.effective_at_us,
    target_activation_events.c.recorded_at_us,
)

learning_item_records = Table(
    "learning_item_records",
    metadata,
    Column("learning_item_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
learning_item_versions = Table(
    "learning_item_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "learning_item_id",
        String(36),
        ForeignKey("learning_item_records.learning_item_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_id",
        String(36),
        ForeignKey("managed_configurations.configuration_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "uncertainty_version_id",
        String(36),
        ForeignKey("uncertainty_classification_versions.version_id"),
        nullable=False,
    ),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_mechanism", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "status IN ('PROPOSED','ACTIVE','AWAITING_EVIDENCE','COMPLETED','INCONCLUSIVE',"
        "'CANCELLED','SUPERSEDED')",
        name="ck_learning_item_status",
    ),
    CheckConstraint(
        "(owner_assignment_version_id IS NOT NULL AND accountable_mechanism IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND accountable_mechanism IS NOT NULL)",
        name="ck_learning_item_accountability",
    ),
)
Index(
    "ix_learning_item_decision",
    learning_item_versions.c.case_id,
    learning_item_versions.c.decision_version_id,
)
learning_item_evidence = Table(
    "learning_item_evidence",
    metadata,
    Column(
        "learning_item_version_id",
        String(36),
        ForeignKey("learning_item_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "evidence_version_id",
        String(36),
        ForeignKey("evidence_versions.version_id"),
        primary_key=True,
    ),
)

# Increment 6 — Trigger, Reassessment, and restrictive Interim Disposition.
# Currentness and Trigger Coverage are intentionally derived from immutable facts.
reassessment_mechanism_records = Table(
    "reassessment_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_mechanism_versions = Table(
    "reassessment_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("reassessment_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column("function", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "intervention_version_id",
        String(36),
        ForeignKey("intervention_versions.version_id"),
        nullable=True,
    ),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("rule_version", Text, nullable=False),
    Column("authority_scope", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    CheckConstraint(
        "function IN ('Trigger Determiner','Reassessment Owner',"
        "'Reassessment Coordination Authority')",
        name="ck_reassessment_mechanism_function",
    ),
)
Index(
    "ix_reassessment_mechanism_context",
    reassessment_mechanism_versions.c.function,
    reassessment_mechanism_versions.c.case_id,
    reassessment_mechanism_versions.c.decision_version_id,
    reassessment_mechanism_versions.c.configuration_version_id,
)

trigger_records = Table(
    "trigger_records",
    metadata,
    Column("trigger_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_versions = Table(
    "trigger_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("trigger_id", String(36), ForeignKey("trigger_records.trigger_id"), nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("trigger_type", Text, nullable=False),
    Column("management_question", Text, nullable=False),
    Column("affected_scope_json", Text, nullable=False),
    Column("source_kind", Text, nullable=False),
    Column("source_family", Text, nullable=False),
    Column("source_record_id", Text, nullable=False),
    Column("source_version_id", Text, nullable=False),
    Column("source_system", Text, nullable=True),
    Column("source_actor", Text, nullable=True),
    Column("source_event_id", Text, nullable=False),
    Column("source_knowledge_at_us", BigInteger, nullable=False),
    Column("withdrawn", Boolean, nullable=False, default=False),
    CheckConstraint(
        "source_kind IN ('PAIM_RECORD','HUMAN_EXTERNAL')", name="ck_trigger_source_kind"
    ),
)
Index(
    "ix_trigger_case_source_question",
    trigger_versions.c.case_id,
    trigger_versions.c.source_event_id,
    trigger_versions.c.management_question,
)

trigger_determination_records = Table(
    "trigger_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_determination_versions = Table(
    "trigger_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("trigger_determination_records.determination_id"),
        nullable=False,
    ),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "outcome IN ('INFORMATIONAL','MONITOR','ANALYTICAL_REFRESH','REASSESSMENT_REQUIRED',"
        "'IMMEDIATE_DISPOSITION_AND_REASSESSMENT')",
        name="ck_trigger_determination_outcome",
    ),
    CheckConstraint(
        "(assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_trigger_determination_accountability",
    ),
)
Index("ix_trigger_determination_trigger", trigger_determination_versions.c.trigger_version_id)

reassessment_records = Table(
    "reassessment_records",
    metadata,
    Column("reassessment_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_versions = Table(
    "reassessment_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "reassessment_id",
        String(36),
        ForeignKey("reassessment_records.reassessment_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("purpose", Text, nullable=False),
    Column("affected_scope_json", Text, nullable=False),
    Column("owner_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "owner_assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "owner_mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    Column("initial_status", Text, nullable=False),
    CheckConstraint(
        "initial_status IN ('PROPOSED','OPEN','ANALYSIS_IN_PROGRESS','AWAITING_DECISION_AUTHORITY',"
        "'BLOCKED_CONFLICT','COMPLETED_CONFIRMED','COMPLETED_SUCCESSOR_DECISION','CANCELLED','SUPERSEDED')",
        name="ck_reassessment_status",
    ),
    CheckConstraint(
        "(initial_status = 'PROPOSED' AND owner_assignment_version_id IS NULL "
        "AND owner_mechanism_version_id IS NULL) OR "
        "(owner_assignment_version_id IS NOT NULL AND owner_mechanism_version_id IS NULL) OR "
        "(owner_assignment_version_id IS NULL AND owner_mechanism_version_id IS NOT NULL)",
        name="ck_reassessment_owner_accountability",
    ),
)
Index(
    "ix_reassessment_case_context",
    reassessment_versions.c.case_id,
    reassessment_versions.c.decision_version_id,
    reassessment_versions.c.configuration_version_id,
)

trigger_membership_records = Table(
    "trigger_membership_records",
    metadata,
    Column("membership_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
trigger_membership_versions = Table(
    "trigger_membership_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "membership_id",
        String(36),
        ForeignKey("trigger_membership_records.membership_id"),
        nullable=False,
    ),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
    ),
    Column("membership_scope", Text, nullable=False),
    Column("active", Boolean, nullable=False),
    UniqueConstraint(
        "trigger_version_id",
        "reassessment_version_id",
        name="uq_trigger_reassessment_membership",
    ),
)
trigger_set_members = Table(
    "trigger_set_members",
    metadata,
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "trigger_version_id", String(36), ForeignKey("trigger_versions.version_id"), nullable=False
    ),
    Column(
        "membership_version_id",
        String(36),
        ForeignKey("trigger_membership_versions.version_id"),
        nullable=False,
    ),
    UniqueConstraint(
        "reassessment_version_id",
        "trigger_version_id",
        name="uq_trigger_set_trigger",
    ),
)

reassessment_determination_records = Table(
    "reassessment_determination_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
reassessment_determination_versions = Table(
    "reassessment_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("reassessment_determination_records.determination_id"),
        nullable=False,
    ),
    Column("kind", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column(
        "target_reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "canonical_trigger_version_id",
        String(36),
        ForeignKey("trigger_versions.version_id"),
        nullable=True,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column("affected_scope_json", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("reassessment_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "kind IN ('GROUPING','DUPLICATE','COEXISTENCE','CANCELLATION','SUPERSESSION')",
        name="ck_reassessment_determination_kind",
    ),
    CheckConstraint(
        "outcome IN ('COMPATIBLE','INCOMPATIBLE','DUPLICATE','COEXISTENCE_AUTHORIZED',"
        "'CANCELLATION_AUTHORIZED','SUPERSESSION_AUTHORIZED')",
        name="ck_reassessment_determination_outcome",
    ),
    CheckConstraint(
        "(assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_reassessment_determination_accountability",
    ),
)
reassessment_determination_triggers = Table(
    "reassessment_determination_triggers",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("reassessment_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "trigger_version_id",
        String(36),
        ForeignKey("trigger_versions.version_id"),
        primary_key=True,
    ),
)
reassessment_determination_reassessments = Table(
    "reassessment_determination_reassessments",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("reassessment_determination_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
)

interim_disposition_records = Table(
    "interim_disposition_records",
    metadata,
    Column("disposition_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
interim_disposition_versions = Table(
    "interim_disposition_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "disposition_id",
        String(36),
        ForeignKey("interim_disposition_records.disposition_id"),
        nullable=False,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column("affected_scope_json", Text, nullable=False),
    Column("operating_state", Text, nullable=True),
    Column("allowed_actions_json", Text, nullable=False),
    Column("required_controls_json", Text, nullable=False),
    Column("prohibitions_json", Text, nullable=False),
    Column("conditions_json", Text, nullable=False),
    Column("suspend_scope", Boolean, nullable=False),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("authority_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("expiry_at_us", BigInteger, nullable=True),
)
Index(
    "ix_interim_disposition_context_time",
    interim_disposition_versions.c.case_id,
    interim_disposition_versions.c.decision_version_id,
    interim_disposition_versions.c.configuration_version_id,
    interim_disposition_versions.c.expiry_at_us,
)

decision_confirmation_records = Table(
    "decision_confirmation_records",
    metadata,
    Column("confirmation_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
decision_confirmation_versions = Table(
    "decision_confirmation_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "confirmation_id",
        String(36),
        ForeignKey("decision_confirmation_records.confirmation_id"),
        nullable=False,
    ),
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        nullable=False,
        unique=True,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "boundary_snapshot_version_id",
        String(36),
        ForeignKey("boundary_snapshot_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("decision_authorization_basis_versions.version_id"),
        nullable=False,
    ),
    Column("confirmer_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
)

reassessment_completion_outcomes = Table(
    "reassessment_completion_outcomes",
    metadata,
    Column(
        "reassessment_version_id",
        String(36),
        ForeignKey("reassessment_versions.version_id"),
        primary_key=True,
    ),
    Column("path", Text, nullable=False),
    Column(
        "confirmation_version_id",
        String(36),
        ForeignKey("decision_confirmation_versions.version_id"),
        nullable=True,
    ),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("decision_versions.version_id"),
        nullable=True,
    ),
    Column("completed_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "(path = 'CONFIRMED' AND confirmation_version_id IS NOT NULL "
        "AND successor_decision_version_id IS NULL) OR "
        "(path = 'SUCCESSOR_DECISION' AND confirmation_version_id IS NULL "
        "AND successor_decision_version_id IS NOT NULL)",
        name="ck_reassessment_exactly_one_completion",
    ),
)

# Increment 7 — authoritative Shared Dependency support records and immutable
# non-authoritative output manifests. Management Register concern entries are
# deliberately not persisted as authoritative editable rows.
shared_dependency_records = Table(
    "shared_dependency_records",
    metadata,
    Column("dependency_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
shared_dependency_versions = Table(
    "shared_dependency_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "dependency_id",
        String(36),
        ForeignKey("shared_dependency_records.dependency_id"),
        nullable=False,
    ),
    Column("dependency_kind", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("declared_scope", Text, nullable=False),
    Column("organizational_context", Text, nullable=True),
    Column("provenance_json", Text, nullable=False),
    Column("withdrawn", Boolean, nullable=False, default=False),
    CheckConstraint("length(trim(dependency_kind)) > 0", name="ck_shared_dependency_kind"),
    CheckConstraint("length(trim(declared_scope)) > 0", name="ck_shared_dependency_scope"),
)
Index(
    "ix_shared_dependency_kind_scope",
    shared_dependency_versions.c.dependency_kind,
    shared_dependency_versions.c.declared_scope,
)

dependency_candidate_set_records = Table(
    "dependency_candidate_set_records",
    metadata,
    Column("candidate_set_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
dependency_candidate_set_versions = Table(
    "dependency_candidate_set_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "candidate_set_id",
        String(36),
        ForeignKey("dependency_candidate_set_records.candidate_set_id"),
        nullable=False,
    ),
    Column("dependency_kind", Text, nullable=False),
    Column("equivalence_scope", Text, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("organizational_context", Text, nullable=True),
    Column("provenance_json", Text, nullable=False),
    Column("membership_checksum", String(64), nullable=False),
    Column("withdrawn", Boolean, nullable=False, default=False),
    UniqueConstraint("version_id", "membership_checksum", name="uq_candidate_set_checksum"),
    CheckConstraint("length(trim(equivalence_scope)) > 0", name="ck_candidate_set_scope"),
)
Index(
    "ix_candidate_set_kind_scope",
    dependency_candidate_set_versions.c.dependency_kind,
    dependency_candidate_set_versions.c.equivalence_scope,
)
dependency_candidate_set_members = Table(
    "dependency_candidate_set_members",
    metadata,
    Column(
        "candidate_set_version_id",
        String(36),
        ForeignKey("dependency_candidate_set_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column("source_family", Text, nullable=False),
    Column("source_record_id", String(36), ForeignKey("records.record_id"), nullable=False),
    Column(
        "source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("dependency_kind", Text, nullable=False),
    UniqueConstraint(
        "candidate_set_version_id",
        "source_family",
        "source_record_id",
        "source_version_id",
        name="uq_candidate_set_exact_member",
    ),
)
Index(
    "ix_candidate_member_source",
    dependency_candidate_set_members.c.source_record_id,
    dependency_candidate_set_members.c.source_version_id,
)

shared_dependency_mechanism_records = Table(
    "shared_dependency_mechanism_records",
    metadata,
    Column("mechanism_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
shared_dependency_mechanism_versions = Table(
    "shared_dependency_mechanism_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "mechanism_id",
        String(36),
        ForeignKey("shared_dependency_mechanism_records.mechanism_id"),
        nullable=False,
    ),
    Column("target_type", Text, nullable=False),
    Column("target_id", String(36), nullable=False),
    Column("accountable_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("rule_id", Text, nullable=False),
    Column("rule_version", Text, nullable=False),
    Column("authority_source", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    CheckConstraint(
        "target_type IN ('dependency_candidate_set','shared_dependency')",
        name="ck_dependency_mechanism_target_type",
    ),
)
Index(
    "ix_dependency_mechanism_target",
    shared_dependency_mechanism_versions.c.target_type,
    shared_dependency_mechanism_versions.c.target_id,
)

shared_dependency_equivalence_records = Table(
    "shared_dependency_equivalence_records",
    metadata,
    Column("determination_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
shared_dependency_equivalence_versions = Table(
    "shared_dependency_equivalence_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "determination_id",
        String(36),
        ForeignKey("shared_dependency_equivalence_records.determination_id"),
        nullable=False,
    ),
    Column(
        "candidate_set_version_id",
        String(36),
        ForeignKey("dependency_candidate_set_versions.version_id"),
        nullable=False,
    ),
    Column(
        "shared_dependency_version_id",
        String(36),
        ForeignKey("shared_dependency_versions.version_id"),
        nullable=True,
    ),
    Column("dependency_kind", Text, nullable=False),
    Column("equivalence_scope", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "mechanism_version_id",
        String(36),
        ForeignKey("shared_dependency_mechanism_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "outcome IN ('EQUIVALENT','NOT_EQUIVALENT','INDETERMINATE')",
        name="ck_dependency_equivalence_outcome",
    ),
    CheckConstraint(
        "(outcome = 'EQUIVALENT' AND shared_dependency_version_id IS NOT NULL) OR "
        "(outcome IN ('NOT_EQUIVALENT','INDETERMINATE') AND "
        "shared_dependency_version_id IS NULL)",
        name="ck_equivalence_dependency_required",
    ),
    CheckConstraint(
        "(assignment_version_id IS NOT NULL AND mechanism_version_id IS NULL) OR "
        "(assignment_version_id IS NULL AND mechanism_version_id IS NOT NULL)",
        name="ck_equivalence_accountability_exactly_one",
    ),
)
Index(
    "ix_equivalence_selection",
    shared_dependency_equivalence_versions.c.candidate_set_version_id,
    shared_dependency_equivalence_versions.c.dependency_kind,
    shared_dependency_equivalence_versions.c.equivalence_scope,
)
shared_dependency_equivalence_delegations = Table(
    "shared_dependency_equivalence_delegations",
    metadata,
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("shared_dependency_equivalence_versions.version_id"),
        primary_key=True,
    ),
    Column("ordinal", BigInteger, primary_key=True),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("role_assignment_versions.version_id"),
        nullable=False,
    ),
)

register_output_manifests = Table(
    "register_output_manifests",
    metadata,
    Column("manifest_id", String(36), primary_key=True),
    Column("output_kind", Text, nullable=False),
    Column("content_json", Text, nullable=False),
    Column("checksum", String(64), nullable=False, unique=True),
    Column("generated_at_us", BigInteger, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("known_at_us", BigInteger, nullable=False),
    Column("rule_id", Text, nullable=False),
    Column("rule_version", Text, nullable=False),
    Column("source_high_water_us", BigInteger, nullable=True),
    Column("processed_watermark_us", BigInteger, nullable=True),
    Column("consistency", Text, nullable=False),
    Column("access_context", Text, nullable=False),
    CheckConstraint("output_kind IN ('VIEW','REPORT','EXPORT')", name="ck_register_output_kind"),
    CheckConstraint(
        "consistency IN ('CURRENT','STALE','INCONSISTENT')",
        name="ck_register_output_consistency",
    ),
)
Index(
    "ix_register_manifest_context",
    register_output_manifests.c.effective_at_us,
    register_output_manifests.c.known_at_us,
    register_output_manifests.c.rule_version,
)
register_notification_intents = Table(
    "register_notification_intents",
    metadata,
    Column("intent_id", String(36), primary_key=True),
    Column(
        "manifest_id",
        String(36),
        ForeignKey("register_output_manifests.manifest_id"),
        nullable=False,
    ),
    Column("concern_key", Text, nullable=False),
    Column("concern_lifecycle", Text, nullable=False),
    Column("channel", Text, nullable=False),
    Column("recipient_scope", Text, nullable=False),
    Column("created_at_us", BigInteger, nullable=False),
    UniqueConstraint("manifest_id", "concern_key", "channel", name="uq_notification_intent"),
    CheckConstraint(
        "concern_lifecycle IN ('CURRENT_ATTENTION','CURRENT_CONFLICT')",
        name="ck_notification_attention_only",
    ),
)

# Increment 8 — local operational application support. These records govern
# software access, adapter handling, and local operations only. They do not
# establish PAIM substantive authority.
operational_principals = Table(
    "operational_principals",
    metadata,
    Column("principal_id", Text, primary_key=True),
    Column("created_at_us", BigInteger, nullable=False),
)
operational_principal_versions = Table(
    "operational_principal_versions",
    metadata,
    Column("version_id", String(36), primary_key=True),
    Column(
        "principal_id",
        Text,
        ForeignKey("operational_principals.principal_id"),
        nullable=False,
    ),
    Column("sequence", BigInteger, nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=True),
    Column("status", Text, nullable=False),
    Column("credential_salt", String(64), nullable=False),
    Column("credential_verifier", String(64), nullable=False),
    Column("credential_iterations", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("recorded_by", Text, nullable=False),
    UniqueConstraint("principal_id", "sequence", name="uq_operational_principal_sequence"),
    CheckConstraint(
        "status IN ('ENABLED','DISABLED','REVOKED')",
        name="ck_operational_principal_status",
    ),
    CheckConstraint("sequence > 0", name="ck_operational_principal_sequence"),
    CheckConstraint(
        "credential_iterations >= 100000",
        name="ck_operational_credential_iterations",
    ),
)
Index(
    "ix_operational_principal_current",
    operational_principal_versions.c.principal_id,
    operational_principal_versions.c.sequence,
)

software_access_grants = Table(
    "software_access_grants",
    metadata,
    Column("grant_id", String(36), primary_key=True),
    Column(
        "principal_id",
        Text,
        ForeignKey("operational_principals.principal_id"),
        nullable=False,
    ),
    Column("sequence", BigInteger, nullable=False),
    Column("permission", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("scope_type", Text, nullable=False),
    Column("scope_id", String(36), nullable=True),
    Column("effect", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column("recorded_by", Text, nullable=False),
    UniqueConstraint(
        "principal_id",
        "permission",
        "action",
        "scope_type",
        "scope_id",
        "sequence",
        name="uq_software_access_grant_sequence",
    ),
    CheckConstraint(
        "permission IN ('LOGIN','CASE_READ','CONFIGURATION_READ','COMMAND','EXPORT',"
        "'DELIVERY','OPERATIONAL_ADMIN')",
        name="ck_software_access_permission",
    ),
    CheckConstraint(
        "scope_type IN ('GLOBAL','CASE','CONFIGURATION')",
        name="ck_software_access_scope_type",
    ),
    CheckConstraint(
        "(scope_type = 'GLOBAL' AND scope_id IS NULL) OR "
        "(scope_type IN ('CASE','CONFIGURATION') AND scope_id IS NOT NULL)",
        name="ck_software_access_scope_identity",
    ),
    CheckConstraint("effect IN ('ALLOW','DENY')", name="ck_software_access_effect"),
    CheckConstraint("sequence > 0", name="ck_software_access_sequence"),
)
Index(
    "ix_software_access_resolution",
    software_access_grants.c.principal_id,
    software_access_grants.c.permission,
    software_access_grants.c.action,
    software_access_grants.c.scope_type,
    software_access_grants.c.scope_id,
    software_access_grants.c.sequence,
)

operational_audit_facts = Table(
    "operational_audit_facts",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column("category", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("principal_id", Text, nullable=True),
    Column("actor_id", String(36), nullable=True),
    Column("action", Text, nullable=False),
    Column("case_id", String(36), nullable=True),
    Column("configuration_id", String(36), nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("causation_id", Text, nullable=True),
    Column("reason_category", Text, nullable=False),
    Column("details_json", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "category IN ('AUTHENTICATION','ACTOR_RESOLUTION','ACCESS','COMMAND','ADMIN',"
        "'EXPORT','ADAPTER','DELIVERY','BACKUP','RESTORE','INTEGRITY','PROJECTION',"
        "'CONFIGURATION')",
        name="ck_operational_audit_category",
    ),
    CheckConstraint(
        "outcome IN ('SUCCESS','FAILURE','ALLOWED','DENIED','ACCEPTED','REPLAYED',"
        "'QUARANTINED','REJECTED','PENDING','DELIVERED','DEGRADED')",
        name="ck_operational_audit_outcome",
    ),
)
Index(
    "ix_operational_audit_time_category",
    operational_audit_facts.c.recorded_at_us,
    operational_audit_facts.c.category,
)

adapter_intakes = Table(
    "adapter_intakes",
    metadata,
    Column("intake_id", String(36), primary_key=True),
    Column("adapter_type", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("source_object_id", Text, nullable=False),
    Column("source_version", Text, nullable=True),
    Column("source_effective_at_us", BigInteger, nullable=False),
    Column("ingested_at_us", BigInteger, nullable=False),
    Column("payload_checksum", String(64), nullable=False),
    Column("target_case_id", String(36), nullable=True),
    Column("target_configuration_id", String(36), nullable=True),
    Column("management_context", Text, nullable=True),
    Column("replay_id", Text, nullable=False),
    Column("mapper_rule_id", Text, nullable=False),
    Column("mapper_rule_version", Text, nullable=False),
    Column("payload_reference", Text, nullable=True),
    Column("payload_json", Text, nullable=False),
    Column("unmapped_material_json", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("quarantine_reason", Text, nullable=True),
    Column("supersedes_intake_id", String(36), ForeignKey("adapter_intakes.intake_id")),
    CheckConstraint(
        "adapter_type IN ('VALUE','RISK','EVIDENCE','AUTHORITY','EXTERNAL_TRIGGER')",
        name="ck_adapter_intake_type",
    ),
    CheckConstraint(
        "status IN ('PROPOSED','QUARANTINED','REJECTED')",
        name="ck_adapter_intake_status",
    ),
    CheckConstraint(
        "(status = 'QUARANTINED' AND quarantine_reason IS NOT NULL) OR "
        "(status IN ('PROPOSED','REJECTED'))",
        name="ck_adapter_quarantine_reason",
    ),
)
Index(
    "ix_adapter_replay",
    adapter_intakes.c.adapter_type,
    adapter_intakes.c.source_system,
    adapter_intakes.c.replay_id,
)
Index(
    "ix_adapter_source_version",
    adapter_intakes.c.adapter_type,
    adapter_intakes.c.source_system,
    adapter_intakes.c.source_object_id,
    adapter_intakes.c.source_version,
)

notification_delivery_events = Table(
    "notification_delivery_events",
    metadata,
    Column("event_id", String(36), primary_key=True),
    Column(
        "intent_id",
        String(36),
        ForeignKey("register_notification_intents.intent_id"),
        nullable=False,
    ),
    Column("attempt_id", Text, nullable=False),
    Column("sequence", BigInteger, nullable=False),
    Column("status", Text, nullable=False),
    Column("spool_reference", Text, nullable=True),
    Column("reason", Text, nullable=True),
    Column("recorded_at_us", BigInteger, nullable=False),
    UniqueConstraint("attempt_id", "sequence", name="uq_delivery_attempt_sequence"),
    CheckConstraint(
        "status IN ('PENDING','DELIVERED','FAILED')",
        name="ck_delivery_status",
    ),
    CheckConstraint("sequence > 0", name="ck_delivery_sequence"),
)
Index(
    "ix_delivery_intent_status",
    notification_delivery_events.c.intent_id,
    notification_delivery_events.c.status,
    notification_delivery_events.c.recorded_at_us,
)
Index(
    "uq_delivery_one_success_per_intent",
    notification_delivery_events.c.intent_id,
    unique=True,
    sqlite_where=notification_delivery_events.c.status == "DELIVERED",
)

operational_register_rebuild_bases = Table(
    "operational_register_rebuild_bases",
    metadata,
    Column(
        "manifest_id",
        String(36),
        ForeignKey("register_output_manifests.manifest_id"),
        primary_key=True,
    ),
    Column("query_json", Text, nullable=False),
    Column("query_checksum", String(64), nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
)
Index(
    "ix_operational_rebuild_checksum",
    operational_register_rebuild_bases.c.query_checksum,
)

# Gate 8 Slice A is prospective-only. These additive projections bind new facts to
# an explicit semantic era and exact context without changing any legacy row.
semantic_contracts = Table(
    "semantic_contracts",
    metadata,
    Column("contract_key", Text, primary_key=True),
    Column("contract_id", Text, nullable=False),
    Column("contract_version", Text, nullable=False),
    Column("owner", Text, nullable=False),
    Column("interpretation_source", Text, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    UniqueConstraint("contract_id", "contract_version", name="uq_semantic_contract_version"),
)
semantic_contract_families = Table(
    "semantic_contract_families",
    metadata,
    Column("contract_key", Text, ForeignKey("semantic_contracts.contract_key"), primary_key=True),
    Column("record_family", Text, primary_key=True),
)
semantic_contract_adapters = Table(
    "semantic_contract_adapters",
    metadata,
    Column("adapter_key", Text, primary_key=True),
    Column(
        "source_contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False
    ),
    Column(
        "target_contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False
    ),
    Column("adapter_version", Text, nullable=False),
    Column("source_label", Text, nullable=False),
    Column("read_safe", Boolean, nullable=False),
)
semantic_contract_successors = Table(
    "semantic_contract_successors",
    metadata,
    Column(
        "predecessor_contract_key",
        Text,
        ForeignKey("semantic_contracts.contract_key"),
        primary_key=True,
    ),
    Column(
        "successor_contract_key",
        Text,
        ForeignKey("semantic_contracts.contract_key"),
        primary_key=True,
    ),
)
exact_context_sets = Table(
    "exact_context_sets",
    metadata,
    Column("context_digest", String(64), primary_key=True),
    Column("canonical_json", Text, nullable=False, unique=True),
    Column("recorded_at_us", BigInteger, nullable=False),
)
exact_context_members = Table(
    "exact_context_members",
    metadata,
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        primary_key=True,
    ),
    Column("slot", Text, primary_key=True),
    Column("member_kind", Text, nullable=False),
    Column("identity", Text, nullable=False),
    CheckConstraint(
        "member_kind IN ('RECORD','VERSION','LITERAL')", name="ck_exact_context_member_kind"
    ),
)
record_version_semantics = Table(
    "record_version_semantics",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("consumer_id", Text, nullable=False),
    Column(
        "adapter_key", Text, ForeignKey("semantic_contract_adapters.adapter_key"), nullable=True
    ),
)
status_event_semantics = Table(
    "status_event_semantics",
    metadata,
    Column("event_id", String(36), ForeignKey("status_events.event_id"), primary_key=True),
    Column("contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
)
version_relationship_semantics = Table(
    "version_relationship_semantics",
    metadata,
    Column(
        "relationship_id",
        String(36),
        ForeignKey("version_relationships.relationship_id"),
        primary_key=True,
    ),
    Column("contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
)
semantic_consumer_cutover_versions = Table(
    "semantic_consumer_cutover_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("consumer_id", Text, nullable=False),
    Column("contract_key", Text, ForeignKey("semantic_contracts.contract_key"), nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    UniqueConstraint("consumer_id", "effective_from_us", name="uq_semantic_consumer_cutover_time"),
)

practical_role_catalog = Table(
    "practical_role_catalog",
    metadata,
    Column("role_code", Text, primary_key=True),
    CheckConstraint(
        "role_code IN ('CASE_COORDINATOR','ASSESSOR','REVIEWER')", name="ck_practical_role_code"
    ),
)
responsibility_records = Table(
    "responsibility_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
responsibility_versions = Table(
    "responsibility_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("record_id", String(36), ForeignKey("responsibility_records.record_id"), nullable=False),
    Column("obligation_kind", Text, nullable=False),
    Column("owning_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("signature_digest", String(64), nullable=False),
)
Index("ix_responsibility_signature", responsibility_versions.c.signature_digest)
responsibility_practical_roles = Table(
    "responsibility_practical_roles",
    metadata,
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "role_code",
        Text,
        ForeignKey("practical_role_catalog.role_code"),
        nullable=False,
    ),
)
assignment_basis_records = Table(
    "assignment_basis_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
assignment_basis_versions = Table(
    "assignment_basis_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id", String(36), ForeignKey("assignment_basis_records.record_id"), nullable=False
    ),
    Column("assigning_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "basis_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("owning_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("allowed_obligation_kinds_json", Text, nullable=False),
    Column("allowed_case_ids_json", Text, nullable=False),
    Column("allowed_signature_digests_json", Text, nullable=False),
    Column("limits_json", Text, nullable=False),
    Column("max_active_assignments", BigInteger, nullable=False),
    Column("state", Text, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("assignment_basis_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "state IN ('ACTIVE','WITHDRAWN','SUPERSEDED')", name="ck_assignment_basis_state"
    ),
    CheckConstraint("max_active_assignments > 0", name="ck_assignment_basis_positive_limit"),
)
responsibility_assignment_records = Table(
    "responsibility_assignment_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
responsibility_assignment_versions = Table(
    "responsibility_assignment_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("responsibility_assignment_records.record_id"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column("signature_digest", String(64), nullable=False),
    Column("actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column(
        "assignment_basis_version_id",
        String(36),
        ForeignKey("assignment_basis_versions.version_id"),
        nullable=False,
    ),
    Column("state", Text, nullable=False),
    Column("effective_from_us", BigInteger, nullable=False),
    Column("effective_to_us", BigInteger, nullable=True),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "state IN ('ASSIGNED','WITHDRAWN','SUPERSEDED')", name="ck_responsibility_assignment_state"
    ),
)
Index(
    "ix_responsibility_assignment_resolution",
    responsibility_assignment_versions.c.signature_digest,
    responsibility_assignment_versions.c.effective_from_us,
    responsibility_assignment_versions.c.recorded_at_us,
)
case_work_records = Table(
    "case_work_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
case_work_versions = Table(
    "case_work_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column("record_id", String(36), ForeignKey("case_work_records.record_id"), nullable=False),
    Column("owning_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=True,
    ),
    Column("requester_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=False),
    Column("assignee_actor_id", String(36), ForeignKey("paim_actors.actor_id"), nullable=True),
    Column("state", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("prerequisites_json", Text, nullable=False),
    Column("expected_result_family", Text, nullable=False),
    Column("due_at_us", BigInteger, nullable=True),
    Column(
        "result_version_id", String(36), ForeignKey("record_versions.version_id"), nullable=True
    ),
    Column(
        "return_context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=True,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("case_work_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint(
        "state IN ('READY','WAITING','COMPLETED','CANCELLED','SUPERSEDED')",
        name="ck_case_work_state",
    ),
    CheckConstraint(
        "state <> 'COMPLETED' OR result_version_id IS NOT NULL", name="ck_completed_work_has_result"
    ),
)
case_work_result_links = Table(
    "case_work_result_links",
    metadata,
    Column(
        "work_version_id", String(36), ForeignKey("case_work_versions.version_id"), primary_key=True
    ),
    Column(
        "result_version_id", String(36), ForeignKey("record_versions.version_id"), nullable=False
    ),
    Column(
        "return_context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
)

# Gate 8 Slice B prospective Case continuity.  Legacy paim_case_versions and
# lifecycle status events remain unchanged; these projections exist only for
# Versions carrying the prospective continuity semantic contract.
case_continuity_status_records = Table(
    "case_continuity_status_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False, unique=True),
)
case_continuity_status_versions = Table(
    "case_continuity_status_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("case_continuity_status_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("status", Text, nullable=False),
    Column("prior_status", Text, nullable=True),
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("case_continuity_determination_versions.version_id"),
        nullable=True,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=True,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=True,
    ),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("case_continuity_status_versions.version_id"),
        nullable=True,
    ),
    Column("successor_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    CheckConstraint("status IN ('OPEN','CLOSED','SUPERSEDED')", name="ck_case_continuity_status"),
    CheckConstraint(
        "prior_status IS NULL OR prior_status IN ('OPEN','CLOSED')",
        name="ck_case_continuity_prior_status",
    ),
    CheckConstraint(
        "(predecessor_version_id IS NULL AND prior_status IS NULL AND "
        "determination_version_id IS NULL) OR "
        "(predecessor_version_id IS NOT NULL AND prior_status IS NOT NULL AND "
        "determination_version_id IS NOT NULL)",
        name="ck_case_continuity_transition_basis",
    ),
    CheckConstraint(
        "(status = 'SUPERSEDED' AND successor_case_id IS NOT NULL) OR "
        "(status <> 'SUPERSEDED' AND successor_case_id IS NULL)",
        name="ck_case_continuity_successor",
    ),
)
Index(
    "ix_case_continuity_status_selection",
    case_continuity_status_versions.c.case_id,
    case_continuity_status_versions.c.effective_at_us,
    case_continuity_status_versions.c.recorded_at_us,
)

case_continuity_determination_records = Table(
    "case_continuity_determination_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
case_continuity_determination_versions = Table(
    "case_continuity_determination_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("case_continuity_determination_records.record_id"),
        nullable=False,
    ),
    Column("kind", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("source_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "source_status_version_id",
        String(36),
        ForeignKey("case_continuity_status_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column(
        "candidate_configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=True,
    ),
    Column("successor_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=True),
    Column(
        "changed_basis_context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("guard_manifest_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("factors_json", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_basis_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "kind IN ('SAME_OR_NEW_CASE','CASE_CLOSURE','CASE_REOPENING','CASE_SUPERSESSION')",
        name="ck_case_continuity_determination_kind",
    ),
    CheckConstraint(
        "(kind = 'SAME_OR_NEW_CASE' AND outcome IN ('SAME_CASE','NEW_CASE_REQUIRED')) OR "
        "(kind = 'CASE_CLOSURE' AND outcome IN ('CLOSE','REMAIN_OPEN')) OR "
        "(kind = 'CASE_REOPENING' AND outcome IN "
        "('REOPEN_SAME_CASE','REMAIN_CLOSED','NEW_CASE_REQUIRED')) OR "
        "(kind = 'CASE_SUPERSESSION' AND outcome IN "
        "('SUPERSEDE_WITH_SUCCESSOR','DO_NOT_SUPERSEDE'))",
        name="ck_case_continuity_determination_outcome",
    ),
)
Index(
    "ix_case_continuity_determination_context",
    case_continuity_determination_versions.c.source_case_id,
    case_continuity_determination_versions.c.kind,
    case_continuity_determination_versions.c.effective_at_us,
    case_continuity_determination_versions.c.recorded_at_us,
)

case_continuity_relationships = Table(
    "case_continuity_relationships",
    metadata,
    Column("relationship_id", String(36), primary_key=True),
    Column("source_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("target_case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column("relationship_kind", Text, nullable=False),
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("case_continuity_determination_versions.version_id"),
        nullable=False,
    ),
    Column("effective_at_us", BigInteger, nullable=False),
    Column("recorded_at_us", BigInteger, nullable=False),
    CheckConstraint("source_case_id <> target_case_id", name="ck_case_continuity_distinct_cases"),
    CheckConstraint(
        "relationship_kind IN ('RELATED_NEW_CASE','SUPERSEDED_BY')",
        name="ck_case_continuity_relationship_kind",
    ),
)
Index(
    "ix_case_continuity_relationship_cases",
    case_continuity_relationships.c.source_case_id,
    case_continuity_relationships.c.target_case_id,
)

configuration_continuity_links = Table(
    "configuration_continuity_links",
    metadata,
    Column("relationship_id", String(36), primary_key=True),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "predecessor_configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "successor_configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "determination_version_id",
        String(36),
        ForeignKey("case_continuity_determination_versions.version_id"),
        nullable=False,
    ),
    Column("recorded_at_us", BigInteger, nullable=False),
    CheckConstraint(
        "predecessor_configuration_version_id <> successor_configuration_version_id",
        name="ck_configuration_continuity_distinct_versions",
    ),
)
Index(
    "ix_configuration_continuity_case",
    configuration_continuity_links.c.case_id,
    configuration_continuity_links.c.recorded_at_us,
)

# Gate 8 Slice C prospective assessment-review families. Legacy analytical
# inputs, Fitness, Acceptance/Selection, and freeze projections remain exact
# and are never migrated into these tables.
assessment_candidate_records = Table(
    "assessment_candidate_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
    Column("lane", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_assessment_candidate_lane"),
)
assessment_candidate_versions = Table(
    "assessment_candidate_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("assessment_candidate_records.record_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("information_basis_version_ids_json", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_assessment_candidate_version_lane"),
)
Index(
    "ix_assessment_candidate_context",
    assessment_candidate_versions.c.lane,
    assessment_candidate_versions.c.case_id,
    assessment_candidate_versions.c.configuration_version_id,
)

assessment_readiness_records = Table(
    "assessment_readiness_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
assessment_readiness_versions = Table(
    "assessment_readiness_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("assessment_readiness_records.record_id"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column(
        "assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("information_basis_version_ids_json", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_assessment_readiness_lane"),
)
Index(
    "ix_assessment_readiness_selection",
    assessment_readiness_versions.c.lane,
    assessment_readiness_versions.c.case_id,
    assessment_readiness_versions.c.configuration_version_id,
    assessment_readiness_versions.c.decision_use,
)

assessment_adequacy_records = Table(
    "assessment_adequacy_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
assessment_adequacy_versions = Table(
    "assessment_adequacy_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id", String(36), ForeignKey("assessment_adequacy_records.record_id"), nullable=False
    ),
    Column("lane", Text, nullable=False),
    Column(
        "assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("information_basis_version_ids_json", Text, nullable=False),
    Column("outcome", Text, nullable=False),
    Column("material_reasons_json", Text, nullable=False),
    Column("limitations_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("uncertainty", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_assessment_adequacy_lane"),
    CheckConstraint(
        "outcome IN ('ADEQUATE','NOT_ADEQUATE','INDETERMINATE')",
        name="ck_assessment_adequacy_outcome",
    ),
)
Index(
    "ix_assessment_adequacy_selection",
    assessment_adequacy_versions.c.lane,
    assessment_adequacy_versions.c.case_id,
    assessment_adequacy_versions.c.configuration_version_id,
    assessment_adequacy_versions.c.decision_use,
)

assessment_reliance_records = Table(
    "assessment_reliance_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
assessment_reliance_versions = Table(
    "assessment_reliance_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id", String(36), ForeignKey("assessment_reliance_records.record_id"), nullable=False
    ),
    Column("lane", Text, nullable=False),
    Column(
        "assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "adequacy_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("assessed_scope", Text, nullable=False),
    Column("information_basis_version_ids_json", Text, nullable=False),
    Column("candidate_dispositions_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=True,
    ),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_assessment_reliance_lane"),
)
Index(
    "ix_assessment_reliance_selection",
    assessment_reliance_versions.c.lane,
    assessment_reliance_versions.c.case_id,
    assessment_reliance_versions.c.configuration_version_id,
    assessment_reliance_versions.c.decision_use,
)

prospective_integration_records = Table(
    "prospective_integration_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prospective_integration_versions = Table(
    "prospective_integration_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("prospective_integration_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("bounded_scope", Text, nullable=False),
    Column(
        "value_assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_adequacy_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_adequacy_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column("value_information_basis_json", Text, nullable=False),
    Column("risk_information_basis_json", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("prospective_integration_versions.version_id"),
        nullable=True,
    ),
)
Index(
    "ix_prospective_integration_selection",
    prospective_integration_versions.c.case_id,
    prospective_integration_versions.c.configuration_version_id,
    prospective_integration_versions.c.context_digest,
    prospective_integration_versions.c.decision_use,
    prospective_integration_versions.c.bounded_scope,
)

prospective_decision_records = Table(
    "prospective_decision_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prospective_decision_versions = Table(
    "prospective_decision_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("prospective_decision_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("prospective_integration_versions.version_id"),
        nullable=False,
    ),
    Column("decision_use", Text, nullable=False),
    Column("bounded_scope", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column(
        "value_assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_adequacy_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=False,
    ),
    Column(
        "value_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_readiness_version_id",
        String(36),
        ForeignKey("assessment_readiness_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_adequacy_version_id",
        String(36),
        ForeignKey("assessment_adequacy_versions.version_id"),
        nullable=False,
    ),
    Column(
        "risk_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=True,
    ),
    Column(
        "proposal_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=True,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint("status IN ('PROPOSED','AUTHORIZED')", name="ck_prospective_decision_status"),
)
Index(
    "ix_prospective_decision_selection",
    prospective_decision_versions.c.case_id,
    prospective_decision_versions.c.configuration_version_id,
    prospective_decision_versions.c.context_digest,
    prospective_decision_versions.c.decision_use,
    prospective_decision_versions.c.bounded_scope,
)

prospective_decision_authorization_records = Table(
    "prospective_decision_authorization_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prospective_decision_authorization_versions = Table(
    "prospective_decision_authorization_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("prospective_decision_authorization_records.record_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "proposal_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("prospective_integration_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
)
Index(
    "ix_prospective_decision_authorization",
    prospective_decision_authorization_versions.c.decision_version_id,
)

prospective_decision_confirmation_records = Table(
    "prospective_decision_confirmation_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
prospective_decision_confirmation_versions = Table(
    "prospective_decision_confirmation_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("prospective_decision_confirmation_records.record_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "integration_version_id",
        String(36),
        ForeignKey("prospective_integration_versions.version_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
)
Index(
    "ix_prospective_decision_confirmation",
    prospective_decision_confirmation_versions.c.decision_version_id,
)

planned_review_point_records = Table(
    "planned_review_point_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
planned_review_point_versions = Table(
    "planned_review_point_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("planned_review_point_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("review_purpose", Text, nullable=False),
    Column("bounded_scope", Text, nullable=False),
    Column("review_at_us", BigInteger, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("source_basis_version_ids_json", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "planning_authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=True,
    ),
    Column("decision_condition", Boolean, nullable=False),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("planned_review_point_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
)
Index(
    "ix_planned_review_point_selection",
    planned_review_point_versions.c.case_id,
    planned_review_point_versions.c.configuration_version_id,
    planned_review_point_versions.c.decision_version_id,
    planned_review_point_versions.c.context_digest,
    planned_review_point_versions.c.review_purpose,
    planned_review_point_versions.c.bounded_scope,
)

required_review_constraint_records = Table(
    "required_review_constraint_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
required_review_constraint_versions = Table(
    "required_review_constraint_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("required_review_constraint_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("review_purpose", Text, nullable=False),
    Column("bounded_scope", Text, nullable=False),
    Column("state", Text, nullable=False),
    Column("operator", Text, nullable=False),
    Column("window_start_us", BigInteger, nullable=True),
    Column("window_end_us", BigInteger, nullable=True),
    Column("limitations_json", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "source_authority_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "applicability_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("required_review_constraint_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint("state IN ('ACTIVE','WITHDRAWN')", name="ck_required_review_state"),
    CheckConstraint(
        "operator IN ('BY','NOT_BEFORE','WINDOW')",
        name="ck_required_review_operator",
    ),
    CheckConstraint(
        "(operator = 'BY' AND window_start_us IS NULL AND window_end_us IS NOT NULL) OR "
        "(operator = 'NOT_BEFORE' AND window_start_us IS NOT NULL AND window_end_us IS NULL) OR "
        "(operator = 'WINDOW' AND window_start_us IS NOT NULL AND window_end_us IS NOT NULL "
        "AND window_start_us < window_end_us) OR state = 'WITHDRAWN'",
        name="ck_required_review_window",
    ),
)
Index(
    "ix_required_review_constraint_selection",
    required_review_constraint_versions.c.case_id,
    required_review_constraint_versions.c.configuration_version_id,
    required_review_constraint_versions.c.decision_version_id,
    required_review_constraint_versions.c.context_digest,
    required_review_constraint_versions.c.review_purpose,
    required_review_constraint_versions.c.bounded_scope,
)

review_attention_event_records = Table(
    "review_attention_event_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
review_attention_event_versions = Table(
    "review_attention_event_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("review_attention_event_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "event_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column("review_purpose", Text, nullable=False),
    Column("bounded_scope", Text, nullable=False),
    Column("affected_focus_json", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
)
Index(
    "ix_review_attention_event_case",
    review_attention_event_versions.c.case_id,
    review_attention_event_versions.c.configuration_version_id,
    review_attention_event_versions.c.context_digest,
)

review_episode_records = Table(
    "review_episode_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
review_episode_versions = Table(
    "review_episode_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("review_episode_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("status", Text, nullable=False),
    Column("origin", Text, nullable=False),
    Column("origin_version_ids_json", Text, nullable=False),
    Column("focused_scope_json", Text, nullable=False),
    Column(
        "prior_decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_integration_version_id",
        String(36),
        ForeignKey("prospective_integration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_value_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column(
        "prior_risk_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=False,
    ),
    Column("refreshed_result_version_ids_json", Text, nullable=False),
    Column(
        "continued_value_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=True,
    ),
    Column(
        "continued_risk_reliance_version_id",
        String(36),
        ForeignKey("assessment_reliance_versions.version_id"),
        nullable=True,
    ),
    Column(
        "decision_confirmation_version_id",
        String(36),
        ForeignKey("prospective_decision_confirmation_versions.version_id"),
        nullable=True,
    ),
    Column(
        "successor_decision_version_id",
        String(36),
        ForeignKey("prospective_decision_versions.version_id"),
        nullable=True,
    ),
    Column("outcome", Text, nullable=True),
    Column("completion_rationale", Text, nullable=True),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("review_episode_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint("status IN ('OPEN','COMPLETED')", name="ck_review_episode_status"),
    CheckConstraint(
        "(status = 'OPEN' AND outcome IS NULL AND decision_confirmation_version_id IS NULL "
        "AND successor_decision_version_id IS NULL) OR "
        "(status = 'COMPLETED' AND outcome IS NOT NULL AND "
        "((decision_confirmation_version_id IS NOT NULL AND successor_decision_version_id IS NULL) "
        "OR (decision_confirmation_version_id IS NULL "
        "AND successor_decision_version_id IS NOT NULL)))",
        name="ck_review_episode_decision_path",
    ),
)
Index(
    "ix_review_episode_selection",
    review_episode_versions.c.case_id,
    review_episode_versions.c.configuration_version_id,
    review_episode_versions.c.context_digest,
    review_episode_versions.c.status,
)

review_episode_result_links = Table(
    "review_episode_result_links",
    metadata,
    Column(
        "episode_version_id",
        String(36),
        ForeignKey("review_episode_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "result_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        primary_key=True,
    ),
    Column("link_role", Text, primary_key=True),
)

quantitative_claim_records = Table(
    "quantitative_claim_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
quantitative_claim_versions = Table(
    "quantitative_claim_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id", String(36), ForeignKey("quantitative_claim_records.record_id"), nullable=False
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column("lane", Text, nullable=False),
    Column("claim_type", Text, nullable=False),
    Column("construct_id", Text, nullable=False),
    Column("metric_id", Text, nullable=False),
    Column("quantity_kind", Text, nullable=False),
    Column("representation", Text, nullable=False),
    Column("central_value_text", Text, nullable=True),
    Column("lower_value_text", Text, nullable=True),
    Column("upper_value_text", Text, nullable=True),
    Column("distribution_json", Text, nullable=False),
    Column("unit", Text, nullable=False),
    Column("currency", Text, nullable=True),
    Column("scale", Text, nullable=False),
    Column("direction", Text, nullable=False),
    Column("population", Text, nullable=False),
    Column("denominator", Text, nullable=True),
    Column("temporal_basis", Text, nullable=False),
    Column("period_start_us", BigInteger, nullable=False),
    Column("period_end_us", BigInteger, nullable=True),
    Column("horizon", Text, nullable=False),
    Column("baseline", Text, nullable=False),
    Column("gross_net", Text, nullable=False),
    Column("nominal_real", Text, nullable=False),
    Column("method_id", Text, nullable=False),
    Column("assumptions_json", Text, nullable=False),
    Column("uncertainty", Text, nullable=False),
    Column("limitations_json", Text, nullable=False),
    Column(
        "assessment_version_id",
        String(36),
        ForeignKey("assessment_candidate_versions.version_id"),
        nullable=True,
    ),
    Column(
        "review_episode_version_id",
        String(36),
        ForeignKey("review_episode_versions.version_id"),
        nullable=True,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=True,
    ),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("quantitative_claim_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint("lane IN ('VALUE','RISK')", name="ck_quantitative_claim_lane"),
    CheckConstraint(
        "claim_type IN ('ESTIMATE_EXPECTATION','TARGET_OBJECTIVE','OBSERVED_RESULT',"
        "'THRESHOLD_CONSTRAINT','RISK_ESTIMATE','COST_RESOURCE_MEASURE')",
        name="ck_quantitative_claim_type",
    ),
    CheckConstraint(
        "quantity_kind IN ('ABSOLUTE_AMOUNT','RATE','RATIO','PERCENTAGE','COUNT',"
        "'CONTINUOUS_MEASURE','CURRENCY','TIME')",
        name="ck_quantitative_quantity_kind",
    ),
    CheckConstraint(
        "representation IN ('SCALAR','RANGE','INTERVAL','DISTRIBUTION','PROPORTION',"
        "'RATE','COUNT','CURRENCY','TIME','OTHER_BOUNDED')",
        name="ck_quantitative_representation",
    ),
    CheckConstraint(
        "temporal_basis IN ('POINT_IN_TIME','PERIODIC','CUMULATIVE')",
        name="ck_quantitative_temporal_basis",
    ),
    CheckConstraint(
        "(representation IN ('RANGE','INTERVAL') AND central_value_text IS NULL "
        "AND lower_value_text IS NOT NULL AND upper_value_text IS NOT NULL) OR "
        "(representation = 'DISTRIBUTION' AND central_value_text IS NULL "
        "AND lower_value_text IS NULL AND upper_value_text IS NULL) OR "
        "(representation NOT IN ('RANGE','INTERVAL','DISTRIBUTION') "
        "AND central_value_text IS NOT NULL AND lower_value_text IS NULL "
        "AND upper_value_text IS NULL)",
        name="ck_quantitative_value_shape",
    ),
    CheckConstraint(
        "(quantity_kind = 'CURRENCY' AND currency IS NOT NULL) OR quantity_kind <> 'CURRENCY'",
        name="ck_quantitative_currency",
    ),
    CheckConstraint(
        "(temporal_basis = 'POINT_IN_TIME' AND period_end_us IS NULL) OR "
        "(temporal_basis <> 'POINT_IN_TIME' AND period_end_us IS NOT NULL "
        "AND period_start_us < period_end_us)",
        name="ck_quantitative_period",
    ),
    CheckConstraint(
        "claim_type <> 'THRESHOLD_CONSTRAINT' OR authority_source_version_id IS NOT NULL",
        name="ck_quantitative_threshold_authority",
    ),
)
Index(
    "ix_quantitative_claim_selection",
    quantitative_claim_versions.c.case_id,
    quantitative_claim_versions.c.configuration_version_id,
    quantitative_claim_versions.c.context_digest,
    quantitative_claim_versions.c.lane,
    quantitative_claim_versions.c.claim_type,
    quantitative_claim_versions.c.construct_id,
    quantitative_claim_versions.c.metric_id,
)
Index("ix_quantitative_claim_assessment", quantitative_claim_versions.c.assessment_version_id)
Index("ix_quantitative_claim_review", quantitative_claim_versions.c.review_episode_version_id)

quantitative_claim_basis_links = Table(
    "quantitative_claim_basis_links",
    metadata,
    Column(
        "claim_version_id",
        String(36),
        ForeignKey("quantitative_claim_versions.version_id"),
        primary_key=True,
    ),
    Column(
        "source_version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True
    ),
    Column("link_role", Text, primary_key=True),
    CheckConstraint(
        "link_role IN ('SOURCE','APPLICABILITY')", name="ck_quantitative_basis_link_role"
    ),
)

quantitative_comparability_records = Table(
    "quantitative_comparability_records",
    metadata,
    Column("record_id", String(36), ForeignKey("records.record_id"), primary_key=True),
)
quantitative_comparability_versions = Table(
    "quantitative_comparability_versions",
    metadata,
    Column("version_id", String(36), ForeignKey("record_versions.version_id"), primary_key=True),
    Column(
        "record_id",
        String(36),
        ForeignKey("quantitative_comparability_records.record_id"),
        nullable=False,
    ),
    Column("case_id", String(36), ForeignKey("paim_cases.case_id"), nullable=False),
    Column(
        "configuration_version_id",
        String(36),
        ForeignKey("managed_configuration_versions.version_id"),
        nullable=False,
    ),
    Column(
        "context_digest",
        String(64),
        ForeignKey("exact_context_sets.context_digest"),
        nullable=False,
    ),
    Column(
        "left_claim_version_id",
        String(36),
        ForeignKey("quantitative_claim_versions.version_id"),
        nullable=False,
    ),
    Column(
        "right_claim_version_id",
        String(36),
        ForeignKey("quantitative_claim_versions.version_id"),
        nullable=False,
    ),
    Column("outcome", Text, nullable=False),
    Column("rationale", Text, nullable=False),
    Column(
        "responsibility_version_id",
        String(36),
        ForeignKey("responsibility_versions.version_id"),
        nullable=False,
    ),
    Column(
        "assignment_version_id",
        String(36),
        ForeignKey("responsibility_assignment_versions.version_id"),
        nullable=False,
    ),
    Column(
        "authority_source_version_id",
        String(36),
        ForeignKey("record_versions.version_id"),
        nullable=False,
    ),
    Column(
        "predecessor_version_id",
        String(36),
        ForeignKey("quantitative_comparability_versions.version_id"),
        nullable=True,
    ),
    Column("knowledge_cutoff_us", BigInteger, nullable=False),
    CheckConstraint(
        "outcome IN ('COMPARABLE','NOT_COMPARABLE')", name="ck_quantitative_comparability_outcome"
    ),
    CheckConstraint(
        "left_claim_version_id <> right_claim_version_id", name="ck_quantitative_distinct_claims"
    ),
)
Index(
    "ix_quantitative_comparability_pair",
    quantitative_comparability_versions.c.left_claim_version_id,
    quantitative_comparability_versions.c.right_claim_version_id,
)

IMMUTABILITY_TRIGGERS: tuple[str, ...] = (
    """
    CREATE TRIGGER prevent_finalized_version_update
    BEFORE UPDATE ON record_versions
    WHEN OLD.finalized = 1
    BEGIN
      SELECT RAISE(ABORT, 'finalized content is immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_record_version_delete
    BEFORE DELETE ON record_versions
    BEGIN
      SELECT RAISE(ABORT, 'record version history is append-preserving');
    END
    """,
    """
    CREATE TRIGGER prevent_status_event_update
    BEFORE UPDATE ON status_events
    BEGIN
      SELECT RAISE(ABORT, 'status event history is append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_status_event_delete
    BEFORE DELETE ON status_events
    BEGIN
      SELECT RAISE(ABORT, 'status event history is append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_relationship_update
    BEFORE UPDATE ON version_relationships
    BEGIN
      SELECT RAISE(ABORT, 'version relationships are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_relationship_delete
    BEFORE DELETE ON version_relationships
    BEGIN
      SELECT RAISE(ABORT, 'version relationships are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_idempotency_update
    BEFORE UPDATE ON idempotency_facts
    BEGIN
      SELECT RAISE(ABORT, 'idempotency facts are immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_idempotency_delete
    BEFORE DELETE ON idempotency_facts
    BEGIN
      SELECT RAISE(ABORT, 'idempotency facts are immutable');
    END
    """,
    """
    CREATE TRIGGER prevent_audit_update
    BEFORE UPDATE ON audit_facts
    BEGIN
      SELECT RAISE(ABORT, 'audit facts are append-only');
    END
    """,
    """
    CREATE TRIGGER prevent_audit_delete
    BEFORE DELETE ON audit_facts
    BEGIN
      SELECT RAISE(ABORT, 'audit facts are append-only');
    END
    """,
)
