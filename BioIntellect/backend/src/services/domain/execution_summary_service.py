"""Execution Summary Service - Unified execution summary report generation."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from src.repositories.real_time_monitoring_repository import (
    RealTimeMonitoringRepository,
)
from src.services.domain.fix_recommendations_engine import (
    FixRecommendationsEngine,
)
from src.observability.logger import get_logger

logger = get_logger("service.execution_summary")


class ExecutionSummaryService:
    """Service for generating unified execution summary reports."""

    def __init__(self):
        self.monitoring_repo = RealTimeMonitoringRepository()
        self.recommendations_engine = FixRecommendationsEngine()

    async def generate_execution_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive execution summary for the specified time period."""
        try:
            logger.info(f"Generating execution summary for last {hours} hours")

            # Get execution summary data
            execution_summary = await self.monitoring_repo.get_execution_summary(hours)
            if not execution_summary["success"]:
                raise Exception(
                    f"Failed to get execution summary: {execution_summary['message']}"
                )

            # Get performance metrics
            performance_metrics = await self.monitoring_repo.get_performance_metrics(
                hours
            )
            if not performance_metrics["success"]:
                raise Exception(
                    f"Failed to get performance metrics: {performance_metrics['message']}"
                )

            # Get recent errors for analysis
            recent_errors = await self._get_recent_errors(hours)

            # Generate fix recommendations
            recommendations_report = (
                self.recommendations_engine.generate_comprehensive_report(
                    execution_summary["data"],
                    performance_metrics["data"],
                    recent_errors,
                )
            )

            # Create the unified report
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "time_range_hours": hours,
                    "report_version": "1.0.0",
                },
                "executive_summary": self._create_executive_summary(
                    execution_summary["data"]
                ),
                "error_analysis": self._create_error_analysis(
                    execution_summary["data"], recent_errors
                ),
                "performance_profile": self._create_performance_profile(
                    performance_metrics["data"]
                ),
                "fix_recommendations": recommendations_report,
                "action_items": self._extract_action_items(recommendations_report),
            }

            logger.info(f"Execution summary generated successfully for {hours} hours")
            return {"success": True, "report": report}

        except Exception as e:
            logger.error(f"Error generating execution summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating execution summary: {str(e)}",
            }

    async def generate_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Generate real-time dashboard data for monitoring."""
        try:
            # Get last hour summary
            hour_summary = await self.monitoring_repo.get_execution_summary(1)
            day_summary = await self.monitoring_repo.get_execution_summary(24)

            # Get current performance metrics
            performance_metrics = await self.monitoring_repo.get_performance_metrics(1)

            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "current_status": self._determine_system_status(
                    day_summary["data"] if day_summary["success"] else {}
                ),
                "last_hour": hour_summary["data"] if hour_summary["success"] else {},
                "last_24_hours": day_summary["data"] if day_summary["success"] else {},
                "performance": performance_metrics["data"]
                if performance_metrics["success"]
                else {},
                "alerts": self._generate_alerts(
                    day_summary["data"] if day_summary["success"] else {}
                ),
            }

            return {"success": True, "data": dashboard_data}

        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating dashboard data: {str(e)}",
            }

    async def _get_recent_errors(self, hours: int) -> List[Dict[str, Any]]:
        """Get recent errors for analysis."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Get error logs
            error_logs = await self.monitoring_repo.get_execution_logs(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                limit=1000,
            )

            if not error_logs["success"]:
                return []

            # Filter for errors only
            errors = []
            for log in error_logs["data"]:
                if not log.get("success", True):
                    errors.append(
                        {
                            "type": log.get("error_type", "Unknown"),
                            "category": log.get("error_category", "unknown"),
                            "message": log.get("error_message", "No message"),
                            "priority": log.get("error_priority", "low"),
                            "timestamp": log.get("timestamp"),
                            "path": log.get("request_path"),
                            "method": log.get("request_method"),
                        }
                    )

            return errors

        except Exception as e:
            logger.error(f"Error getting recent errors: {str(e)}")
            return []

    def _create_executive_summary(
        self, execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create executive summary section."""
        total_requests = execution_data.get("total_requests", 0)
        success_rate = execution_data.get("success_rate", 0)
        avg_duration = execution_data.get("average_duration_ms", 0)

        # Determine overall health
        if success_rate >= 99:
            health_status = "excellent"
        elif success_rate >= 95:
            health_status = "good"
        elif success_rate >= 90:
            health_status = "fair"
        else:
            health_status = "poor"

        # Top 5 slowest endpoints
        slowest_endpoints = execution_data.get("slowest_endpoints", [])[:5]
        slowest_summary = []
        for endpoint in slowest_endpoints:
            slowest_summary.append(
                {
                    "endpoint": endpoint.get("request_path", "Unknown"),
                    "average_duration_ms": endpoint.get("duration_ms", 0),
                }
            )

        return {
            "total_requests": total_requests,
            "success_rate_percent": round(success_rate, 2),
            "average_response_time_ms": avg_duration,
            "system_health_status": health_status,
            "top_5_slowest_endpoints": slowest_summary,
            "error_categories": execution_data.get("error_categories", {}),
        }

    def _create_error_analysis(
        self, execution_data: Dict[str, Any], recent_errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create error analysis section."""
        error_categories = execution_data.get("error_categories", {})

        # Categorize errors by priority
        priority_breakdown: Dict[str, int] = defaultdict(int)
        for category, count in error_categories.items():
            # Determine priority based on category
            if category in ["server_error", "medical_critical", "security"]:
                priority_breakdown["critical"] += count
            elif category in ["authentication", "authorization", "network"]:
                priority_breakdown["high"] += count
            elif category in ["validation", "client_error"]:
                priority_breakdown["medium"] += count
            else:
                priority_breakdown["low"] += count

        # Most common error patterns
        error_patterns: Counter = Counter()
        for error in recent_errors:
            pattern = (
                f"{error.get('category', 'unknown')}:{error.get('type', 'unknown')}"
            )
            error_patterns[pattern] += 1

        return {
            "total_errors": sum(error_categories.values()),
            "error_rate_percent": round(
                (
                    sum(error_categories.values())
                    / max(execution_data.get("total_requests", 1), 1)
                )
                * 100,
                2,
            ),
            "error_categories": dict(error_categories),
            "priority_breakdown": dict(priority_breakdown),
            "most_common_patterns": dict(error_patterns.most_common(10)),
            "error_frequency_analysis": self._analyze_error_frequency(recent_errors),
        }

    def _create_performance_profile(
        self, performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create performance profile section."""
        avg_duration = performance_data.get("average_duration_ms", 0)
        p95_duration = performance_data.get("p95_duration", 0)
        p99_duration = performance_data.get("p99_duration", 0)
        avg_memory = performance_data.get("average_memory", 0)
        avg_cpu = performance_data.get("average_cpu", 0)

        # Determine performance status
        if p95_duration <= 500 and avg_cpu <= 50 and avg_memory <= 200:
            performance_status = "excellent"
        elif p95_duration <= 1000 and avg_cpu <= 70 and avg_memory <= 400:
            performance_status = "good"
        elif p95_duration <= 2000 and avg_cpu <= 85 and avg_memory <= 600:
            performance_status = "acceptable"
        else:
            performance_status = "needs_attention"

        return {
            "response_time_metrics": {
                "average_ms": avg_duration,
                "p50_ms": performance_data.get("p50_duration", 0),
                "p95_ms": p95_duration,
                "p99_ms": p99_duration,
                "max_ms": performance_data.get("max_duration", 0),
                "min_ms": performance_data.get("min_duration", 0),
            },
            "resource_usage": {
                "average_memory_mb": avg_memory,
                "average_cpu_percent": avg_cpu,
            },
            "performance_status": performance_status,
            "throughput": {
                "total_requests": performance_data.get("total_requests", 0),
                "requests_per_hour": round(
                    performance_data.get("total_requests", 0)
                    / max(performance_data.get("time_range_hours", 1), 1),
                    2,
                ),
            },
        }

    def _extract_action_items(
        self, recommendations_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract prioritized action items from recommendations."""
        action_items = []

        # Extract from immediate actions
        immediate_actions = recommendations_report.get("implementation_guide", {}).get(
            "immediate_actions", []
        )
        for action in immediate_actions:
            action_items.append(
                {
                    "priority": "critical",
                    "category": action.get("category", "general"),
                    "description": action.get(
                        "description", "Critical issue requiring immediate attention"
                    ),
                    "estimated_effort": action.get("estimated_effort", "Unknown"),
                    "recommendations": action.get("recommendations", []),
                }
            )

        # Extract from short-term improvements
        short_term = recommendations_report.get("implementation_guide", {}).get(
            "short_term_improvements", []
        )
        for action in short_term[:5]:  # Top 5 short-term
            action_items.append(
                {
                    "priority": "high",
                    "category": action.get("category", "general"),
                    "description": action.get(
                        "description", "High priority improvement"
                    ),
                    "estimated_effort": action.get("estimated_effort", "Unknown"),
                    "recommendations": action.get("recommendations", []),
                }
            )

        return action_items[:10]  # Return top 10 action items

    def _determine_system_status(self, execution_data: Dict[str, Any]) -> str:
        """Determine current system status."""
        success_rate = execution_data.get("success_rate", 100)
        avg_duration = execution_data.get("average_duration_ms", 0)
        total_requests = execution_data.get("total_requests", 0)

        if total_requests == 0:
            return "no_data"

        if success_rate >= 99 and avg_duration <= 500:
            return "healthy"
        elif success_rate >= 95 and avg_duration <= 1000:
            return "warning"
        elif success_rate >= 90:
            return "degraded"
        else:
            return "critical"

    def _generate_alerts(self, execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on system metrics."""
        alerts = []

        success_rate = execution_data.get("success_rate", 100)
        avg_duration = execution_data.get("average_duration_ms", 0)
        error_categories = execution_data.get("error_categories", {})

        # Success rate alerts
        if success_rate < 90:
            alerts.append(
                {
                    "level": "critical",
                    "type": "success_rate",
                    "message": f"Low success rate: {success_rate:.1f}%",
                    "threshold": 90,
                    "current_value": success_rate,
                }
            )
        elif success_rate < 95:
            alerts.append(
                {
                    "level": "warning",
                    "type": "success_rate",
                    "message": f"Declining success rate: {success_rate:.1f}%",
                    "threshold": 95,
                    "current_value": success_rate,
                }
            )

        # Performance alerts
        if avg_duration > 2000:
            alerts.append(
                {
                    "level": "critical",
                    "type": "response_time",
                    "message": f"High response time: {avg_duration:.0f}ms",
                    "threshold": 2000,
                    "current_value": avg_duration,
                }
            )
        elif avg_duration > 1000:
            alerts.append(
                {
                    "level": "warning",
                    "type": "response_time",
                    "message": f"Elevated response time: {avg_duration:.0f}ms",
                    "threshold": 1000,
                    "current_value": avg_duration,
                }
            )

        # Error pattern alerts
        for category, count in error_categories.items():
            if count > 50:  # High frequency errors
                alerts.append(
                    {
                        "level": "warning",
                        "type": "error_frequency",
                        "message": f"High frequency of {category} errors: {count}",
                        "threshold": 50,
                        "current_value": count,
                        "category": category,
                    }
                )

        return alerts

    def _analyze_error_frequency(
        self, recent_errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze error frequency patterns."""
        if not recent_errors:
            return {
                "pattern": "no_errors",
                "analysis": "No errors detected in the specified time period",
            }

        # Group errors by hour
        hourly_errors: Dict[str, int] = defaultdict(int)
        error_types: Counter = Counter()

        for error in recent_errors:
            # Extract category count
            category = error.get("category", "unknown")
            error_types[category] += 1

            # Extract hour from timestamp
            timestamp = error.get("timestamp", "")
            if timestamp and "T" in timestamp:
                try:
                    hour = timestamp.split("T")[1][:2]  # Extract HH from ISO timestamp
                    if hour.isdigit():
                        hourly_errors[hour] += 1
                except (IndexError, AttributeError):
                    pass

        # Find peak error hours
        peak_hour = (
            max(hourly_errors.items(), key=lambda x: x[1]) if hourly_errors else None
        )

        analysis = {
            "total_errors": len(recent_errors),
            "unique_error_types": len(error_types),
            "most_common_error": error_types.most_common(1)[0] if error_types else None,
            "peak_error_hour": peak_hour[0] if peak_hour else None,
            "hourly_distribution": dict(hourly_errors),
            "error_trend": self._determine_error_trend(hourly_errors),
        }

        return analysis

    def _determine_error_trend(self, hourly_errors: Dict[str, int]) -> str:
        """Determine error trend over time."""
        if not hourly_errors:
            return "no_data"

        hours = sorted(hourly_errors.keys())
        if len(hours) < 2:
            return "insufficient_data"

        # Compare first half vs second half
        mid_point = len(hours) // 2
        first_half_avg = sum(hourly_errors[h] for h in hours[:mid_point]) / mid_point
        second_half_avg = sum(hourly_errors[h] for h in hours[mid_point:]) / (
            len(hours) - mid_point
        )

        if second_half_avg > first_half_avg * 1.5:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.5:
            return "decreasing"
        else:
            return "stable"

