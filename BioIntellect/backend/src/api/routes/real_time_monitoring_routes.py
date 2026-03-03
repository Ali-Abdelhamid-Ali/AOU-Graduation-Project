"""Real-Time Monitoring Routes - Frontend interaction logging and execution summary endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime

from src.services.domain.execution_summary_service import (
    ExecutionSummaryService,
)
from src.repositories.real_time_monitoring_repository import (
    RealTimeMonitoringRepository,
)
from src.observability.logger import get_logger
from src.security.auth_middleware import get_current_user

logger = get_logger("routes.real_time_monitoring")

router = APIRouter(prefix="/logs", tags=["real-time-monitoring"])


def get_execution_summary_service():
    return ExecutionSummaryService()


def get_real_time_monitoring_repository():
    return RealTimeMonitoringRepository()


# Frontend Interaction Logging Endpoints


@router.post("/frontend/interaction")
async def log_frontend_interaction(
    interaction_data: Dict[str, Any],
    user: Optional[dict[str, Any]] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Log frontend user interaction event."""
    try:
        # Add user context if available
        if user:
            interaction_data["user_id"] = user.get("id")
            interaction_data["user_role"] = user.get("role")

        # Store in frontend_interactions table (would need to be created)
        logger.info(
            f"Frontend interaction logged: {interaction_data['type']} - {interaction_data.get('component', 'Unknown')}"
        )

        # For now, we'll just log it - in production you'd store in Supabase
        return {"success": True, "message": "Frontend interaction logged successfully"}

    except Exception as e:
        logger.error(f"Error logging frontend interaction: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error logging interaction: {str(e)}"
        )


@router.post("/frontend/api-call")
async def log_api_call(
    api_call_data: Dict[str, Any],
    user: Optional[dict[str, Any]] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Log API call made from frontend."""
    try:
        if user:
            api_call_data["user_id"] = user.get("id")

        logger.info(
            f"API call logged: {api_call_data.get('function_name', 'Unknown')} - {api_call_data.get('status', 'Unknown')}"
        )

        return {"success": True, "message": "API call logged successfully"}

    except Exception as e:
        logger.error(f"Error logging API call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging API call: {str(e)}")


@router.post("/frontend/network")
async def log_network_request(
    network_data: Dict[str, Any],
    user: Optional[dict[str, Any]] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Log network request made from frontend."""
    try:
        if user:
            network_data["user_id"] = user.get("id")

        logger.info(
            f"Network request logged: {network_data.get('method', 'Unknown')} {network_data.get('url', 'Unknown')} - {network_data.get('status', 'Unknown')}"
        )

        return {"success": True, "message": "Network request logged successfully"}

    except Exception as e:
        logger.error(f"Error logging network request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error logging network request: {str(e)}"
        )


@router.post("/frontend/user-input")
async def log_user_input(
    input_data: Dict[str, Any],
    user: Optional[dict[str, Any]] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Log user input events."""
    try:
        if user:
            input_data["user_id"] = user.get("id")

        logger.info(
            f"User input logged: {input_data.get('event_type', 'Unknown')} in {input_data.get('component', 'Unknown')}"
        )

        return {"success": True, "message": "User input logged successfully"}

    except Exception as e:
        logger.error(f"Error logging user input: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error logging user input: {str(e)}"
        )


# Execution Summary and Reporting Endpoints


@router.get("/execution/summary")
async def get_execution_summary(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours (1-168)"),
    user: dict[str, Any] = Depends(get_current_user),
    summary_service: ExecutionSummaryService = Depends(get_execution_summary_service),
):
    """Get comprehensive execution summary report."""
    try:
        # Only super admins can view execution summaries
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await summary_service.generate_execution_summary(hours)

        if result["success"]:
            return {"success": True, "data": result["report"]}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to generate summary"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating execution summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating execution summary: {str(e)}"
        )


@router.get("/dashboard/real-time")
async def get_real_time_dashboard(
    user: dict[str, Any] = Depends(get_current_user),
    summary_service: ExecutionSummaryService = Depends(get_execution_summary_service),
):
    """Get real-time dashboard data."""
    try:
        # Only super admins can view real-time dashboard
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await summary_service.generate_real_time_dashboard_data()

        if result["success"]:
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to get dashboard data"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time dashboard: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting real-time dashboard: {str(e)}"
        )


@router.get("/performance/metrics")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours (1-168)"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Get performance metrics for specified time range."""
    try:
        # Only super admins can view performance metrics
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await repo.get_performance_metrics(hours)

        if result["success"]:
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to get performance metrics"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting performance metrics: {str(e)}"
        )


@router.get("/execution/logs")
async def get_execution_logs(
    start_time: Optional[str] = Query(None, description="Start time in ISO format"),
    end_time: Optional[str] = Query(None, description="End time in ISO format"),
    status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    error_category: Optional[str] = Query(None, description="Filter by error category"),
    path_pattern: Optional[str] = Query(
        None, description="Filter by path pattern (SQL LIKE)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Get execution logs with filtering options."""
    try:
        # Only super admins can view execution logs
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await repo.get_execution_logs(
            start_time=start_time,
            end_time=end_time,
            status_code=status_code,
            error_category=error_category,
            path_pattern=path_pattern,
            limit=limit,
            offset=offset,
        )

        if result["success"]:
            return {
                "success": True,
                "data": result["data"],
                "count": result.get("count", 0),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to get execution logs"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting execution logs: {str(e)}"
        )


@router.delete("/execution/cleanup")
async def cleanup_execution_logs(
    days_to_keep: int = Query(
        7, ge=1, le=365, description="Number of days to keep logs"
    ),
    user: dict[str, Any] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Clean up old execution logs."""
    try:
        # Only super admins can clean up logs
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        result = await repo.cleanup_old_logs(days_to_keep)

        if result["success"]:
            return {
                "success": True,
                "message": result.get("message", "Logs cleaned up successfully"),
                "deleted_count": result.get("deleted_count", 0),
            }
        else:
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to clean up logs")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up execution logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error cleaning up execution logs: {str(e)}"
        )


# System Health and Monitoring Endpoints


@router.get("/system/health")
async def get_system_health(
    user: dict[str, Any] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Get system health status based on recent monitoring data."""
    try:
        # Only super admins can view system health
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Get last hour summary for health check
        summary_result = await repo.get_execution_summary(1)

        if not summary_result["success"]:
            raise HTTPException(
                status_code=500, detail="Failed to get system health data"
            )

        summary_data = summary_result["data"]

        # Determine health status
        success_rate = summary_data.get("success_rate", 100)
        avg_duration = summary_data.get("average_duration_ms", 0)
        total_requests = summary_data.get("total_requests", 0)

        if total_requests == 0:
            health_status = "no_data"
        elif success_rate >= 99 and avg_duration <= 500:
            health_status = "healthy"
        elif success_rate >= 95 and avg_duration <= 1000:
            health_status = "warning"
        elif success_rate >= 90:
            health_status = "degraded"
        else:
            health_status = "critical"

        health_data = {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "success_rate": success_rate,
                "average_duration_ms": avg_duration,
                "total_requests": total_requests,
                "error_rate": 100 - success_rate,
            },
            "checks": {
                "response_time": "pass" if avg_duration <= 1000 else "fail",
                "success_rate": "pass" if success_rate >= 95 else "fail",
                "error_rate": "pass" if success_rate >= 95 else "fail",
            },
        }

        return {"success": True, "data": health_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting system health: {str(e)}"
        )


@router.get("/system/alerts")
async def get_system_alerts(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours"),
    user: dict[str, Any] = Depends(get_current_user),
    repo: RealTimeMonitoringRepository = Depends(get_real_time_monitoring_repository),
):
    """Get system alerts based on monitoring data."""
    try:
        # Only super admins can view alerts
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Access denied")

        # Get execution summary to generate alerts
        summary_result = await repo.get_execution_summary(hours)

        if not summary_result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get alert data")

        summary_data = summary_result["data"]

        # Generate alerts
        alerts = []
        success_rate = summary_data.get("success_rate", 100)
        avg_duration = summary_data.get("average_duration_ms", 0)
        error_categories = summary_data.get("error_categories", {})

        # Success rate alerts
        if success_rate < 90:
            alerts.append(
                {
                    "level": "critical",
                    "type": "success_rate",
                    "message": f"Low success rate: {success_rate:.1f}%",
                    "timestamp": datetime.utcnow().isoformat(),
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
                    "timestamp": datetime.utcnow().isoformat(),
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
                    "timestamp": datetime.utcnow().isoformat(),
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
                    "timestamp": datetime.utcnow().isoformat(),
                    "threshold": 1000,
                    "current_value": avg_duration,
                }
            )

        # Error frequency alerts
        for category, count in error_categories.items():
            if count > 50:
                alerts.append(
                    {
                        "level": "warning",
                        "type": "error_frequency",
                        "message": f"High frequency of {category} errors: {count}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "threshold": 50,
                        "current_value": count,
                        "category": category,
                    }
                )

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a["level"] == "critical"]),
                "warning_alerts": len([a for a in alerts if a["level"] == "warning"]),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system alerts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting system alerts: {str(e)}"
        )

