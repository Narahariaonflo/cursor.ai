"""Domain enumerations shared across entities and application boundaries."""

from enum import Enum


class RunState(str, Enum):
    """Lifecycle states for an analysis run."""

    ACCEPTED = "ACCEPTED"
    VALIDATING = "VALIDATING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    AGGREGATING = "AGGREGATING"
    RENDERING = "RENDERING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Severity(str, Enum):
    """Supported finding severities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EvidenceKind(str, Enum):
    """Supported evidence categories."""

    METRIC = "metric"
    RESPONSE = "response"
    DOM = "dom"
    CONSOLE = "console"
    SCREENSHOT = "screenshot"
    TOOL_OUTPUT = "tool_output"


class DeviceProfile(str, Enum):
    """Supported scan device profiles."""

    DESKTOP = "desktop"
    MOBILE = "mobile"


class AgentKind(str, Enum):
    """Approved MVP analysis-agent identifiers."""

    SEO = "seo"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    HTML = "html"
    LATENCY = "latency"
    BROKEN_LINK = "broken_link"
    SECURITY = "security"
    CONSOLE = "console"


class AgentTaskStatus(str, Enum):
    """Terminal status for one agent task."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class FailureClassification(str, Enum):
    """Approved agent-failure classifications."""

    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    POLICY = "POLICY"
    BUDGET = "BUDGET"


class ReportFormat(str, Enum):
    """Supported report formats."""

    HTML = "html"
    MARKDOWN = "markdown"


class PageEligibilityStatus(str, Enum):
    """Planning eligibility state for a discovered page."""

    ELIGIBLE = "ELIGIBLE"
    EXCLUDED = "EXCLUDED"
    DENIED = "DENIED"
    LIMITED = "LIMITED"
