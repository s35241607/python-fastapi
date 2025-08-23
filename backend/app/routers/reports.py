"""
Reports Router Module

This module provides FastAPI endpoints for analytics, reporting, and dashboard
data including metrics, KPIs, exports, and custom reports.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.reporting_service import ReportingService
from app.services.ticket_service import TicketService
from app.schemas import (
    DashboardData, TicketStatistics, # ReportRequest, ReportResponse,
    # PerformanceMetrics, SLAReport, UserProductivityReport,
    # DepartmentAnalytics, TrendAnalysis, CustomReportFilter
)
from app.enums import TicketStatus, Priority, TicketType, UserRole
from app.models import User

# Placeholder for authentication dependency
async def get_current_user() -> User:
    """Get current authenticated user - placeholder"""
    # This will be implemented in Phase 6
    return User(id=1, email="user@example.com", username="testuser", 
               first_name="Test", last_name="User", role="employee")

async def get_current_user_role() -> str:
    """Get current user role - placeholder"""
    # This will be implemented in Phase 6
    return "employee"

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    department_id: Optional[int] = Query(None),
    date_range: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get comprehensive dashboard data for the current user"""
    
    try:
        ticket_service = TicketService(db)
        
        # Determine department access
        target_department_id = department_id
        if user_role == UserRole.EMPLOYEE.value:
            # Employees can only see their own department
            target_department_id = current_user.department_id
        elif department_id and user_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            # Managers can only see their own department unless they're admin
            if department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other department data"
                )
        
        dashboard_data = await ticket_service.get_user_dashboard_data(
            user_id=current_user.id,
            user_role=user_role,
            department_id=target_department_id
        )
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/statistics", response_model=TicketStatistics)
async def get_ticket_statistics(
    user_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get detailed ticket statistics with filters"""
    
    try:
        # Permission checks
        if user_id and user_id != current_user.id:
            if user_role not in [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.DEPARTMENT_HEAD.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' statistics"
                )
        
        if department_id and user_role == UserRole.EMPLOYEE.value:
            if department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other department statistics"
                )
        
        reporting_service = ReportingService(db)
        statistics = await reporting_service.get_advanced_statistics(
            user_id=user_id,
            department_id=department_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/performance")
async def get_performance_metrics(
    metric_type: str = Query("team", pattern="^(individual|team|department|system)$"),
    target_id: Optional[int] = Query(None, description="User ID or Department ID"),
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get performance metrics and KPIs"""
    
    try:
        # Permission checks based on metric type
        if metric_type == "individual" and target_id != current_user.id:
            if user_role not in [UserRole.ADMIN.value, UserRole.MANAGER.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' performance"
                )
        
        if metric_type in ["department", "system"]:
            if user_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.MANAGER.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view department/system metrics"
                )
        
        reporting_service = ReportingService(db)
        metrics = await reporting_service.get_performance_metrics(
            metric_type=metric_type,
            target_id=target_id,
            period=period,
            requesting_user_id=current_user.id,
            user_role=user_role
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.get("/sla")
async def get_sla_report(
    department_id: Optional[int] = Query(None),
    priority_filter: Optional[List[Priority]] = Query(None),
    ticket_type_filter: Optional[List[TicketType]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get SLA compliance report"""
    
    try:
        # Permission checks
        if department_id and user_role == UserRole.EMPLOYEE.value:
            if department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other department SLA data"
                )
        
        reporting_service = ReportingService(db)
        sla_report = await reporting_service.get_sla_report(
            department_id=department_id,
            priority_filter=priority_filter,
            ticket_type_filter=ticket_type_filter,
            start_date=start_date,
            end_date=end_date
        )
        
        return sla_report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SLA report"
        )


@router.get("/productivity")
async def get_productivity_report(
    user_ids: Optional[List[int]] = Query(None),
    department_id: Optional[int] = Query(None),
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    include_details: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get user productivity report"""
    
    try:
        # Permission checks
        if user_ids and any(user_id != current_user.id for user_id in user_ids):
            if user_role not in [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.DEPARTMENT_HEAD.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' productivity"
                )
        
        # If no user_ids specified and not admin/manager, show only current user
        if not user_ids and user_role == UserRole.EMPLOYEE.value:
            user_ids = [current_user.id]
        
        reporting_service = ReportingService(db)
        productivity_report = await reporting_service.get_productivity_report(
            user_ids=user_ids,
            department_id=department_id,
            period=period,
            include_details=include_details
        )
        
        return productivity_report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve productivity report"
        )


@router.get("/department-analytics")
async def get_department_analytics(
    department_id: Optional[int] = Query(None),
    comparison_period: int = Query(30, ge=7, le=365),
    include_trends: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get comprehensive department analytics"""
    
    try:
        # Permission checks
        if user_role == UserRole.EMPLOYEE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view department analytics"
            )
        
        # Non-admin users can only view their own department
        target_department_id = department_id
        if user_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            target_department_id = current_user.department_id
        
        reporting_service = ReportingService(db)
        analytics = await reporting_service.get_department_analytics(
            department_id=target_department_id,
            comparison_period=comparison_period,
            include_trends=include_trends
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve department analytics"
        )


@router.get("/trends")
async def get_trend_analysis(
    analysis_type: str = Query("tickets", pattern="^(tickets|resolution_time|volume|satisfaction)$"),
    period: str = Query("month", pattern="^(day|week|month|quarter)$"),
    duration: int = Query(12, ge=3, le=24, description="Number of periods to analyze"),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get trend analysis for various metrics"""
    
    try:
        # Permission checks
        if department_id and user_role == UserRole.EMPLOYEE.value:
            if department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other department trends"
                )
        
        reporting_service = ReportingService(db)
        trends = await reporting_service.get_trend_analysis(
            analysis_type=analysis_type,
            period=period,
            duration=duration,
            department_id=department_id,
            user_id=current_user.id if user_role == UserRole.EMPLOYEE.value else None
        )
        
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trend analysis"
        )


@router.post("/custom")
async def generate_custom_report(
    report_request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Generate a custom report based on specified criteria"""
    
    try:
        # Permission checks for custom reports
        if user_role == UserRole.EMPLOYEE.value and report_request.scope != "personal":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can only generate personal reports"
            )
        
        reporting_service = ReportingService(db)
        
        # Validate and generate report
        report = await reporting_service.generate_custom_report(
            report_request=report_request,
            requesting_user_id=current_user.id,
            user_role=user_role
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate custom report"
        )


@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    department_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_details: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Export reports in various formats"""
    
    try:
        # Permission checks
        if department_id and user_role == UserRole.EMPLOYEE.value:
            if department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to export other department data"
                )
        
        reporting_service = ReportingService(db)
        
        # Prepare filters
        filters = {
            "department_id": department_id,
            "start_date": start_date,
            "end_date": end_date,
            "include_details": include_details,
            "user_id": current_user.id if user_role == UserRole.EMPLOYEE.value else None
        }
        
        # Generate export based on format
        if format == "csv":
            export_data = await reporting_service.export_report_csv(
                report_type=report_type,
                filters=filters,
                include_details=include_details
            )
            media_type = "text/csv"
            filename = f"{report_type}_report.csv"
            
        elif format == "excel":
            export_data = await reporting_service.export_report_excel(
                report_type=report_type,
                filters=filters,
                include_details=include_details
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{report_type}_report.xlsx"
            
        elif format == "pdf":
            export_data = await reporting_service.export_report_pdf(
                report_type=report_type,
                filters=filters,
                include_details=include_details
            )
            media_type = "application/pdf"
            filename = f"{report_type}_report.pdf"
        
        return Response(
            content=export_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export report"
        )


@router.get("/scheduled", response_model=List[dict])
async def get_scheduled_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get list of scheduled reports for the user"""
    
    try:
        reporting_service = ReportingService(db)
        scheduled_reports = await reporting_service.get_user_scheduled_reports(
            user_id=current_user.id,
            user_role=user_role
        )
        
        return scheduled_reports
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scheduled reports"
        )


@router.post("/schedule", response_model=dict)
async def schedule_report(
    report_config: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Schedule a recurring report"""
    
    try:
        # Validate schedule permissions
        if user_role == UserRole.EMPLOYEE.value and report_config.get("scope") != "personal":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees can only schedule personal reports"
            )
        
        reporting_service = ReportingService(db)
        scheduled_report = await reporting_service.schedule_report(
            config=report_config,
            user_id=current_user.id,
            user_role=user_role
        )
        
        return {
            "schedule_id": scheduled_report["id"],
            "message": "Report scheduled successfully",
            "next_run": scheduled_report["next_run"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule report"
        )


@router.delete("/schedule/{schedule_id}")
async def cancel_scheduled_report(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Cancel a scheduled report"""
    
    try:
        reporting_service = ReportingService(db)
        success = await reporting_service.cancel_scheduled_report(
            schedule_id=schedule_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled report not found or not authorized"
            )
        
        return {"message": "Scheduled report cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel scheduled report"
        )


# Real-time analytics endpoints

@router.get("/realtime/metrics", response_model=dict)
async def get_realtime_metrics(
    metric_types: List[str] = Query(["active_tickets", "pending_approvals"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get real-time system metrics"""
    
    try:
        reporting_service = ReportingService(db)
        metrics = await reporting_service.get_realtime_metrics(
            metric_types=metric_types,
            user_id=current_user.id,
            department_id=current_user.department_id,
            user_role=user_role
        )
        
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time metrics"
        )


@router.get("/health/system", response_model=dict)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get system health and performance indicators"""
    
    try:
        # Only admins can view system health
        if user_role not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view system health data"
            )
        
        reporting_service = ReportingService(db)
        health_data = await reporting_service.get_system_health()
        
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health data"
        )


# Utility endpoints for report metadata

@router.get("/templates", response_model=List[dict])
async def get_report_templates(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get available report templates"""
    
    try:
        reporting_service = ReportingService(db)
        templates = await reporting_service.get_available_templates(
            user_role=user_role,
            category=category
        )
        
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report templates"
        )