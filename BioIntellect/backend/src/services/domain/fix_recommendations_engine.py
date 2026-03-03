"""Fix Recommendations Engine - Rule-based system for generating actionable fix recommendations."""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict, Counter
import re

from src.observability.logger import get_logger

logger = get_logger("service.fix_recommendations")


class FixRecommendationsEngine:
    """Engine for generating fix recommendations based on error patterns and system behavior."""

    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.medical_patterns = self._load_medical_patterns()

    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load error pattern matching rules."""
        return {
            # Authentication Errors
            "authentication": {
                "patterns": [
                    r"401.*unauthorized",
                    r"403.*forbidden",
                    r"invalid.*token",
                    r"token.*expired",
                    r"authentication.*failed",
                ],
                "recommendations": [
                    "Check token expiration logic and refresh mechanism",
                    "Verify JWT secret key configuration",
                    "Implement proper session timeout handling",
                    "Review authentication middleware configuration",
                    "Add logging for failed authentication attempts",
                ],
                "priority": "high",
                "category": "security",
            },
            # Database Errors
            "database": {
                "patterns": [
                    r"connection.*refused",
                    r"timeout.*database",
                    r"database.*error",
                    r"sql.*syntax.*error",
                    r"table.*not.*found",
                    r"constraint.*violation",
                ],
                "recommendations": [
                    "Check database connection pool settings",
                    "Verify database server availability and connectivity",
                    "Review SQL query syntax and optimization",
                    "Implement connection retry logic with exponential backoff",
                    "Monitor database connection pool usage",
                    "Add database health checks",
                ],
                "priority": "critical",
                "category": "infrastructure",
            },
            # Network Errors
            "network": {
                "patterns": [
                    r"connection.*timeout",
                    r"dns.*resolution.*failed",
                    r"network.*unreachable",
                    r"ssl.*error",
                    r"connection.*reset",
                ],
                "recommendations": [
                    "Implement timeout configuration for external calls",
                    "Add DNS resolution monitoring",
                    "Configure SSL certificate validation",
                    "Implement circuit breaker pattern for external services",
                    "Add network connectivity health checks",
                    "Review firewall and routing configurations",
                ],
                "priority": "high",
                "category": "network",
            },
            # Validation Errors
            "validation": {
                "patterns": [
                    r"422.*validation.*error",
                    r"invalid.*input",
                    r"missing.*required.*field",
                    r"validation.*failed",
                    r"bad.*request",
                ],
                "recommendations": [
                    "Implement comprehensive input validation schemas",
                    "Add detailed error messages for validation failures",
                    "Review API endpoint input requirements",
                    "Implement client-side validation to reduce server load",
                    "Add request size limits and rate limiting",
                    "Implement proper error response formatting",
                ],
                "priority": "medium",
                "category": "application",
            },
            # Memory Errors
            "memory": {
                "patterns": [
                    r"memory.*error",
                    r"out.*of.*memory",
                    r"memory.*leak",
                    r"heap.*overflow",
                ],
                "recommendations": [
                    "Implement memory usage monitoring and alerting",
                    "Review large object creation and garbage collection",
                    "Add memory profiling to identify leaks",
                    "Implement connection pooling for database and external services",
                    "Review caching strategies and TTL policies",
                    "Add resource cleanup in exception handlers",
                ],
                "priority": "critical",
                "category": "performance",
            },
            # File System Errors
            "filesystem": {
                "patterns": [
                    r"file.*not.*found",
                    r"permission.*denied",
                    r"disk.*full",
                    r"file.*upload.*failed",
                    r"storage.*quota.*exceeded",
                ],
                "recommendations": [
                    "Implement proper file existence checks",
                    "Review file system permissions and access controls",
                    "Add disk space monitoring and alerting",
                    "Implement file upload size limits and validation",
                    "Review storage quota management",
                    "Add file operation retry logic",
                ],
                "priority": "medium",
                "category": "infrastructure",
            },
        }

    def _load_performance_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load performance-related pattern matching rules."""
        return {
            "slow_responses": {
                "condition": lambda metrics: metrics.get("p95_duration", 0) > 1000,
                "recommendations": [
                    "Review and optimize database queries",
                    "Implement response caching for frequently accessed data",
                    "Add database indexing for slow query patterns",
                    "Review external API call efficiency",
                    "Implement request batching where appropriate",
                    "Add performance monitoring and alerting",
                ],
                "priority": "high",
            },
            "high_memory_usage": {
                "condition": lambda metrics: metrics.get("average_memory", 0) > 500,
                "recommendations": [
                    "Review memory usage patterns and identify leaks",
                    "Implement memory pooling for frequently allocated objects",
                    "Add garbage collection tuning",
                    "Review large data structure usage",
                    "Implement data pagination for large datasets",
                    "Add memory usage monitoring and alerts",
                ],
                "priority": "medium",
            },
            "high_cpu_usage": {
                "condition": lambda metrics: metrics.get("average_cpu", 0) > 80,
                "recommendations": [
                    "Profile CPU usage to identify bottlenecks",
                    "Optimize computationally expensive operations",
                    "Implement asynchronous processing for heavy tasks",
                    "Review algorithm complexity and efficiency",
                    "Add CPU usage monitoring and alerts",
                    "Consider horizontal scaling for CPU-intensive operations",
                ],
                "priority": "medium",
            },
        }

    def _load_medical_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load medical domain-specific error patterns."""
        return {
            "patient_data": {
                "patterns": [
                    r"patient.*not.*found",
                    r"invalid.*patient.*id",
                    r"patient.*data.*corrupted",
                    r"hipaa.*violation",
                    r"patient.*privacy.*breach",
                ],
                "recommendations": [
                    "Implement patient ID validation and verification",
                    "Add patient data integrity checks",
                    "Review HIPAA compliance and data handling procedures",
                    "Implement proper access controls for patient data",
                    "Add audit logging for all patient data access",
                    "Review data encryption and secure storage practices",
                ],
                "priority": "critical",
                "category": "compliance",
            },
            "clinical_workflow": {
                "patterns": [
                    r"workflow.*step.*failed",
                    r"clinical.*process.*interrupted",
                    r"medical.*analysis.*timeout",
                    r"diagnosis.*validation.*failed",
                    r"medical.*record.*incomplete",
                ],
                "recommendations": [
                    "Review clinical workflow step dependencies",
                    "Implement workflow state management and recovery",
                    "Add timeout handling for medical analysis operations",
                    "Review medical data validation and quality checks",
                    "Implement proper error handling for clinical processes",
                    "Add monitoring for medical workflow completion rates",
                ],
                "priority": "high",
                "category": "clinical",
            },
            "medical_imaging": {
                "patterns": [
                    r"image.*upload.*failed",
                    r"invalid.*dicom.*format",
                    r"medical.*image.*corrupted",
                    r"imaging.*processing.*timeout",
                    r"brain.*segmentation.*failed",
                ],
                "recommendations": [
                    "Implement medical image format validation",
                    "Add image integrity checks before processing",
                    "Review medical imaging processing pipeline",
                    "Implement timeout handling for image processing",
                    "Add backup processing for failed image operations",
                    "Review medical imaging storage and retrieval procedures",
                ],
                "priority": "high",
                "category": "medical_imaging",
            },
        }

    def generate_error_recommendations(
        self, error_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for a specific error."""
        recommendations = []

        # Extract error details
        error_message = error_data.get("message", "").lower()
        error_category = error_data.get("category", "")
        priority = error_data.get("priority", "low")

        # Check against general error patterns
        for pattern_name, pattern_config in self.error_patterns.items():
            patterns = pattern_config.get("patterns", [])

            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    recommendations.append(
                        {
                            "type": "error_pattern",
                            "pattern": pattern_name,
                            "priority": pattern_config.get("priority", priority),
                            "category": pattern_config.get("category", "general"),
                            "recommendations": pattern_config.get(
                                "recommendations", []
                            ),
                            "confidence": self._calculate_pattern_confidence(
                                pattern, error_message
                            ),
                        }
                    )
                    break

        # Check against medical patterns if this is a medical domain error
        if any(
            keyword in error_category.lower()
            for keyword in ["medical", "patient", "clinical"]
        ):
            for pattern_name, pattern_config in self.medical_patterns.items():
                patterns = pattern_config.get("patterns", [])

                for pattern in patterns:
                    if re.search(pattern, error_message, re.IGNORECASE):
                        recommendations.append(
                            {
                                "type": "medical_pattern",
                                "pattern": pattern_name,
                                "priority": pattern_config.get("priority", priority),
                                "category": pattern_config.get("category", "medical"),
                                "recommendations": pattern_config.get(
                                    "recommendations", []
                                ),
                                "confidence": self._calculate_pattern_confidence(
                                    pattern, error_message
                                ),
                            }
                        )
                        break

        return recommendations

    def generate_performance_recommendations(
        self, performance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on performance metrics."""
        recommendations = []

        for pattern_name, pattern_config in self.performance_patterns.items():
            condition = pattern_config.get("condition")
            if condition and condition(performance_data):
                recommendations.append(
                    {
                        "type": "performance_pattern",
                        "pattern": pattern_name,
                        "priority": pattern_config.get("priority", "medium"),
                        "category": "performance",
                        "recommendations": pattern_config.get("recommendations", []),
                        "triggered_metrics": self._get_triggered_metrics(
                            performance_data, pattern_config
                        ),
                    }
                )

        return recommendations

    def generate_frequency_based_recommendations(
        self, error_frequency: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on error frequency patterns."""
        recommendations = []

        # Check for high-frequency errors
        for error_type, count in error_frequency.items():
            if count > 10:  # More than 10 occurrences
                recommendations.append(
                    {
                        "type": "frequency_analysis",
                        "error_type": error_type,
                        "frequency": count,
                        "priority": "high" if count > 50 else "medium",
                        "category": "frequency",
                        "recommendations": [
                            f"High frequency of {error_type} errors detected ({count} occurrences)",
                            "Implement systematic error analysis and resolution",
                            "Consider automated error recovery mechanisms",
                            "Review error handling patterns in the codebase",
                            "Implement error rate alerting and monitoring",
                        ],
                    }
                )

        # Check for patterns in error timing
        time_patterns = self._analyze_error_timing_patterns(error_frequency)
        if time_patterns:
            recommendations.extend(time_patterns)

        return recommendations

    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match."""
        # Simple confidence calculation based on pattern specificity
        pattern_length: int = len(pattern)

        # Higher confidence for more specific patterns
        specificity_bonus = min(pattern_length / 50, 1.0)

        # Higher confidence for longer text matches
        coverage_bonus = min(len(re.findall(pattern, text, re.IGNORECASE)) / 3, 1.0)

        return min((specificity_bonus + coverage_bonus) / 2, 1.0)

    def _get_triggered_metrics(
        self, performance_data: Dict[str, Any], pattern_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get the specific metrics that triggered a performance recommendation."""
        condition = pattern_config.get("condition")
        triggered = {}

        if condition:
            # This is a simplified version - in practice, you'd want more sophisticated tracking
            if "p95_duration" in performance_data:
                triggered["p95_duration"] = performance_data["p95_duration"]
            if "average_memory" in performance_data:
                triggered["average_memory"] = performance_data["average_memory"]
            if "average_cpu" in performance_data:
                triggered["average_cpu"] = performance_data["average_cpu"]

        return triggered

    def _analyze_error_timing_patterns(
        self, error_frequency: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze timing patterns in errors."""
        # This would analyze error patterns over time
        # For now, return empty list - could be expanded with time-series analysis
        return []

    def prioritize_recommendations(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on priority, category, and confidence."""
        priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        category_weights = {
            "security": 4,
            "compliance": 4,
            "infrastructure": 3,
            "network": 3,
            "clinical": 3,
            "medical_imaging": 3,
            "performance": 2,
            "application": 2,
            "general": 1,
        }

        def priority_score(rec):
            priority = rec.get("priority", "low")
            category = rec.get("category", "general")
            confidence = rec.get("confidence", 0.5)

            score = (
                priority_weights.get(priority, 1) * 2
                + category_weights.get(category, 1)
                + confidence * 2
            )
            return score

        return sorted(recommendations, key=priority_score, reverse=True)

    def generate_comprehensive_report(
        self,
        execution_summary: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        recent_errors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a comprehensive fix recommendations report."""
        all_recommendations = []

        # Process recent errors
        error_frequency: Counter = Counter()
        for error in recent_errors:
            error_type = error.get("category", "unknown")
            error_frequency[error_type] += 1

            # Generate error-specific recommendations
            error_recommendations = self.generate_error_recommendations(error)
            all_recommendations.extend(error_recommendations)

        # Generate performance recommendations
        performance_recommendations = self.generate_performance_recommendations(
            performance_metrics
        )
        all_recommendations.extend(performance_recommendations)

        # Generate frequency-based recommendations
        frequency_recommendations = self.generate_frequency_based_recommendations(
            dict(error_frequency)
        )
        all_recommendations.extend(frequency_recommendations)

        # Prioritize all recommendations
        prioritized_recommendations = self.prioritize_recommendations(
            all_recommendations
        )

        # Group recommendations by category
        grouped_recommendations = defaultdict(list)
        for rec in prioritized_recommendations:
            category = rec.get("category", "general")
            grouped_recommendations[category].append(rec)

        # Generate summary statistics
        summary_stats = {
            "total_recommendations": len(prioritized_recommendations),
            "critical_issues": len(
                [
                    r
                    for r in prioritized_recommendations
                    if r.get("priority") == "critical"
                ]
            ),
            "high_priority_issues": len(
                [r for r in prioritized_recommendations if r.get("priority") == "high"]
            ),
            "categories_affected": list(grouped_recommendations.keys()),
            "most_common_error_type": error_frequency.most_common(1)[0]
            if error_frequency
            else None,
        }

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary_stats,
            "executive_summary": self._generate_executive_summary(
                summary_stats, grouped_recommendations
            ),
            "recommendations_by_category": dict(grouped_recommendations),
            "top_priorities": prioritized_recommendations[:10],  # Top 10 most important
            "implementation_guide": self._generate_implementation_guide(
                prioritized_recommendations
            ),
        }

        return report

    def _generate_executive_summary(
        self, summary_stats: Dict[str, Any], grouped_recommendations: Dict[str, List]
    ) -> str:
        """Generate executive summary text."""
        total = summary_stats["total_recommendations"]
        critical = summary_stats["critical_issues"]
        high = summary_stats["high_priority_issues"]

        summary = f"System Analysis Report: {total} recommendations identified"

        if critical > 0:
            summary += (
                f", including {critical} critical issues requiring immediate attention"
            )

        if high > 0:
            summary += f" and {high} high-priority improvements"

        categories = ", ".join(summary_stats["categories_affected"][:3])
        if categories:
            summary += f". Primary areas of focus: {categories}"

        if summary_stats["most_common_error_type"]:
            error_type, count = summary_stats["most_common_error_type"]
            summary += f". Most frequent issue: {error_type} ({count} occurrences)"

        return summary

    def _generate_implementation_guide(
        self, recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate implementation guide for recommendations."""
        guide: Dict[str, List[Dict[str, Any]]] = {
            "immediate_actions": [],
            "short_term_improvements": [],
            "long_term_optimizations": [],
        }

        for rec in recommendations[:15]:  # Top 15 recommendations
            priority = rec.get("priority", "low")
            action_item = {
                "description": rec.get("pattern", "General improvement"),
                "category": rec.get("category", "general"),
                "recommendations": rec.get("recommendations", []),
                "estimated_effort": self._estimate_effort(rec),
            }

            if priority == "critical":
                guide["immediate_actions"].append(action_item)
            elif priority == "high":
                guide["short_term_improvements"].append(action_item)
            else:
                guide["long_term_optimizations"].append(action_item)

        return guide

    def _estimate_effort(self, recommendation: Dict[str, Any]) -> str:
        """Estimate implementation effort for a recommendation."""
        # Simple effort estimation based on recommendation type and complexity
        category = recommendation.get("category", "general")
        recommendations_count = len(recommendation.get("recommendations", []))

        if category in ["security", "compliance"] and recommendations_count > 3:
            return "High (1-2 weeks)"
        elif category in ["infrastructure", "network"] and recommendations_count > 2:
            return "Medium (3-5 days)"
        else:
            return "Low (1-2 days)"

