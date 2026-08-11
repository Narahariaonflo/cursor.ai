"""Dependency injection container."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from adapters.outbound.analysis.regex_html_analysis import RegexHtmlAnalysisAdapter
from adapters.outbound.analysis.regex_secret_scan import RegexSecretScanAdapter
from adapters.outbound.analysis.stub_axe import FixtureAxeAdapter
from adapters.outbound.analysis.threshold_lighthouse import MappingLighthouseAdapter
from adapters.outbound.browser.playwright_browser import PlaywrightBrowserAdapter
from adapters.outbound.filesystem.artifact_store import FilesystemArtifactStore
from adapters.outbound.filesystem.report_renderer import SimpleReportRenderer
from adapters.outbound.network.html_link_discovery import HtmlLinkDiscovery
from adapters.outbound.network.http_html_fetcher import HttpHtmlFetcher
from adapters.outbound.network.http_link_check import HttpLinkCheckAdapter
from adapters.outbound.network.simple_header_probe import SimpleHeaderProbeAdapter
from adapters.outbound.network.socket_dns_resolver import SocketDnsResolver
from adapters.outbound.observability.structured_logger import JsonStructuredLogger
from adapters.outbound.postgres.scan_repository import PostgresScanRepository
from adapters.outbound.s3.artifact_store import S3ArtifactStore
from adapters.outbound.sqlite.scan_repository import SqliteScanRepository
from domain.exceptions.errors import ValidationError
from ports.outbound.artifact_store import ArtifactStorePort
from application.agent_services.accessibility_agent import AccessibilityAgentService
from application.agent_services.broken_link_agent import BrokenLinkAgentService
from application.agent_services.console_agent import ConsoleAgentService
from application.agent_services.html_agent import HtmlDocumentAgentService
from application.agent_services.latency_agent import LatencyAgentService
from application.agent_services.performance_agent import PerformanceAgentService
from application.agent_services.security_agent import SecurityAgentService
from application.agent_services.seo_agent import SeoAgentService
from application.evidence.browser_evidence_collector import BrowserEvidenceCollector
from application.limit_services.cost_governor import InMemoryCostGovernor
from application.orchestration.agent_execution_coordinator import (
    AgentExecutionCoordinator,
)
from application.orchestration.crawl_planner import CrawlPlannerService
from application.orchestration.finding_aggregation import FindingAggregationService
from application.policy_services.target_policy import TargetPolicyService
from application.security.sensitive_data_masker import SensitiveDataMasker
from application.services.assistive_narrative import AssistiveNarrativeService
from application.use_cases.get_run_status import GetRunStatus
from application.use_cases.plan_analysis_run import PlanAnalysisRun
from application.use_cases.process_analysis_run import ProcessAnalysisRun
from application.use_cases.publish_run_report import PublishRunReport
from application.use_cases.start_analysis_run import StartAnalysisRun
from application.use_cases.validate_analysis_run import ValidateAnalysisRun
from config.environment import EXTERNAL_PERSISTENCE_ENVIRONMENTS, LOCAL_ENVIRONMENTS
from config.settings import Settings
from domain.value_objects.enums import AgentKind
from ports.outbound.dns_resolver import DnsResolverPort
from ports.outbound.repository import ScanRepositoryPort


@dataclass
class Container:
    """Assemble application dependencies."""

    settings: Settings
    repository: ScanRepositoryPort
    start_analysis_run: StartAnalysisRun
    validate_analysis_run: ValidateAnalysisRun
    plan_analysis_run: PlanAnalysisRun
    get_run_status: GetRunStatus
    publish_run_report: PublishRunReport
    browser_evidence_collector: BrowserEvidenceCollector
    agent_execution_coordinator: AgentExecutionCoordinator
    process_analysis_run: ProcessAnalysisRun

    @classmethod
    def build(cls, resolver: Optional[DnsResolverPort] = None) -> "Container":
        """Build the full dependency graph."""
        settings = Settings.from_env()
        logger = JsonStructuredLogger(settings.app_name, settings.log_level)
        repository, artifact_store = cls._build_persistence(settings)
        report_renderer = SimpleReportRenderer()
        target_policy = TargetPolicyService(
            resolver=resolver or SocketDnsResolver(),
            allowed_ports=settings.allowed_target_ports,
            denied_domains=settings.denied_target_domains,
            max_url_length_bytes=settings.max_url_length_bytes,
        )
        cost_governor = InMemoryCostGovernor(
            max_pages=settings.max_pages_ceiling,
            max_depth=settings.max_depth_ceiling,
            resource_limits=settings.resource_limits,
            policy_version=settings.guardrail_policy_version,
        )
        crawl_planner = CrawlPlannerService(
            target_policy=target_policy,
            max_discovered_urls=settings.max_discovered_urls,
            denied_path_prefixes=settings.denied_path_prefixes,
            tracking_query_parameters=settings.tracking_query_parameters,
        )
        html_fetcher = HttpHtmlFetcher(
            target_policy=target_policy,
            timeout_seconds=settings.http_probe_timeout_seconds,
            max_bytes=settings.max_html_fetch_bytes,
        )
        link_discovery = HtmlLinkDiscovery(fetch_html=html_fetcher.fetch)
        masker = SensitiveDataMasker(settings.secret_mask_patterns)
        browser = PlaywrightBrowserAdapter(
            artifact_store=artifact_store,
            navigation_timeout_ms=settings.page_navigation_timeout_seconds * 1000,
            max_dom_chars=settings.max_dom_chars,
        )
        html_analysis = RegexHtmlAnalysisAdapter()
        link_check = HttpLinkCheckAdapter(
            target_policy=target_policy,
            timeout_seconds=settings.http_probe_timeout_seconds,
            max_redirects=5,
        )
        header_probe = SimpleHeaderProbeAdapter(
            target_policy=target_policy,
            timeout_seconds=settings.http_probe_timeout_seconds,
        )
        secret_scan = RegexSecretScanAdapter(
            pattern_expressions=settings.secret_mask_patterns,
            mask_text=masker.mask_text,
        )
        seo_agent = SeoAgentService()
        html_agent = HtmlDocumentAgentService(html_analysis)
        console_agent = ConsoleAgentService()
        broken_link_agent = BrokenLinkAgentService(link_check)
        accessibility_agent = AccessibilityAgentService(FixtureAxeAdapter())
        performance_agent = PerformanceAgentService(
            lighthouse=MappingLighthouseAdapter({}),
            thresholds=settings.performance_thresholds,
            psi_enabled=settings.psi_enabled,
        )
        latency_agent = LatencyAgentService(
            header_probe=header_probe,
            thresholds_ms=settings.latency_thresholds_ms,
        )
        security_agent = SecurityAgentService(
            secret_scan=secret_scan,
            header_probe=header_probe,
            masker=masker,
        )
        coordinator = AgentExecutionCoordinator(
            agents={
                AgentKind.SEO: seo_agent.execute,
                AgentKind.HTML: html_agent.execute,
                AgentKind.CONSOLE: console_agent.execute,
                AgentKind.BROKEN_LINK: broken_link_agent.execute,
                AgentKind.ACCESSIBILITY: accessibility_agent.execute,
                AgentKind.PERFORMANCE: performance_agent.execute,
                AgentKind.LATENCY: latency_agent.execute,
                AgentKind.SECURITY: security_agent.execute,
            },
            logger=logger,
            max_in_flight=settings.max_agent_tasks_in_flight_per_run,
        )
        validate_analysis_run = ValidateAnalysisRun(
            repository=repository,
            target_policy=target_policy,
            cost_governor=cost_governor,
            logger=logger,
        )
        plan_analysis_run = PlanAnalysisRun(
            repository=repository,
            crawl_planner=crawl_planner,
            link_discovery=link_discovery,
            logger=logger,
        )
        browser_evidence_collector = BrowserEvidenceCollector(
            browser=browser,
            artifact_store=artifact_store,
            cost_governor=cost_governor,
            masker=masker,
            logger=logger,
            max_retries=settings.max_retries_per_operation,
        )
        publish_run_report = PublishRunReport(
            repository=repository,
            artifact_store=artifact_store,
            report_renderer=report_renderer,
            logger=logger,
        )
        process_analysis_run = ProcessAnalysisRun(
            repository=repository,
            validate_analysis_run=validate_analysis_run,
            plan_analysis_run=plan_analysis_run,
            browser_evidence_collector=browser_evidence_collector,
            agent_execution_coordinator=coordinator,
            finding_aggregation=FindingAggregationService(),
            assistive_narrative=AssistiveNarrativeService(),
            publish_run_report=publish_run_report,
            logger=logger,
        )
        return cls(
            settings=settings,
            repository=repository,
            start_analysis_run=StartAnalysisRun(
                repository=repository,
                logger=logger,
            ),
            validate_analysis_run=validate_analysis_run,
            plan_analysis_run=plan_analysis_run,
            get_run_status=GetRunStatus(repository=repository, logger=logger),
            publish_run_report=publish_run_report,
            browser_evidence_collector=browser_evidence_collector,
            agent_execution_coordinator=coordinator,
            process_analysis_run=process_analysis_run,
        )

    @staticmethod
    def _build_persistence(
        settings: Settings,
    ) -> Tuple[ScanRepositoryPort, ArtifactStorePort]:
        """Select filesystem or external persistence adapters from environment."""
        if settings.runtime_environment in LOCAL_ENVIRONMENTS:
            return (
                SqliteScanRepository(settings.database_path),
                FilesystemArtifactStore(settings.artifact_root),
            )
        if settings.runtime_environment not in EXTERNAL_PERSISTENCE_ENVIRONMENTS:
            raise ValidationError("unsupported runtime environment for persistence")
        if not settings.database_url or not settings.s3_bucket:
            raise ValidationError("external persistence configuration is incomplete")
        return (
            PostgresScanRepository(settings.database_url),
            S3ArtifactStore(
                bucket=settings.s3_bucket,
                endpoint_url=settings.s3_endpoint_url,
                access_key_id=settings.s3_access_key_id,
                secret_access_key=settings.s3_secret_access_key,
                region_name=settings.s3_region,
            ),
        )
