"""
Notification Service Module

This module handles all notification functionality including email, Teams, Slack,
and in-app notifications with template management and delivery tracking.
"""

import asyncio
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any, Union
from jinja2 import Template

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Ticket, ApprovalStep
from app.schemas import NotificationTemplate, NotificationRequest
from app.enums import NotificationChannel, Priority, TicketStatus, UserRole


class NotificationService:
    """Service class for managing notifications across multiple channels"""

    def __init__(self, session: AsyncSession, config: Optional[Dict[str, Any]] = None):
        self.session = session
        self.config = config or {}
        
        # Email configuration
        self.smtp_server = self.config.get('smtp_server', 'localhost')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.smtp_username = self.config.get('smtp_username', '')
        self.smtp_password = self.config.get('smtp_password', '')
        self.smtp_use_tls = self.config.get('smtp_use_tls', True)
        self.from_email = self.config.get('from_email', 'noreply@company.com')
        
        # Teams configuration
        self.teams_webhook_url = self.config.get('teams_webhook_url', '')
        
        # Slack configuration
        self.slack_webhook_url = self.config.get('slack_webhook_url', '')
        self.slack_bot_token = self.config.get('slack_bot_token', '')
        
        # Notification templates
        self.templates = self._load_notification_templates()

    async def send_ticket_notification(
        self,
        ticket: Ticket,
        event_type: str,
        recipient_ids: Optional[List[int]] = None,
        custom_message: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, bool]:
        """Send ticket-related notification to specified recipients"""
        
        # Determine recipients if not specified
        if not recipient_ids:
            recipient_ids = await self._get_ticket_notification_recipients(ticket, event_type)
        
        # Get recipients with preferences
        recipients = await self._get_users_with_preferences(recipient_ids)
        
        # Get appropriate template
        template = self._get_template_for_event(event_type, 'ticket')
        
        # Prepare template variables
        template_vars = {
            'ticket': ticket,
            'ticket_url': f"{self.config.get('app_base_url', '')}/tickets/{ticket.id}",
            'custom_message': custom_message,
            'event_type': event_type
        }
        
        # Send notifications
        results = {}
        for recipient in recipients:
            user_channels = channels or self._get_user_notification_channels(recipient, event_type)
            
            for channel in user_channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        success = await self._send_email_notification(
                            recipient, template, template_vars
                        )
                    elif channel == NotificationChannel.TEAMS:
                        success = await self._send_teams_notification(
                            recipient, template, template_vars
                        )
                    elif channel == NotificationChannel.SLACK:
                        success = await self._send_slack_notification(
                            recipient, template, template_vars
                        )
                    elif channel == NotificationChannel.IN_APP:
                        success = await self._send_in_app_notification(
                            recipient, template, template_vars
                        )
                    else:
                        success = False
                    
                    results[f"{recipient.id}_{channel.value}"] = success
                    
                except Exception as e:
                    print(f"Failed to send {channel.value} notification to user {recipient.id}: {e}")
                    results[f"{recipient.id}_{channel.value}"] = False
        
        return results

    async def send_approval_notification(
        self,
        approval_step: ApprovalStep,
        event_type: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, bool]:
        """Send approval-related notification"""
        
        # Get approver
        approver = approval_step.approver
        ticket = approval_step.workflow.ticket
        
        # Get template
        template = self._get_template_for_event(event_type, 'approval')
        
        # Prepare template variables
        template_vars = {
            'approval_step': approval_step,
            'ticket': ticket,
            'approver': approver,
            'approval_url': f"{self.config.get('app_base_url', '')}/approvals/{approval_step.id}",
            'custom_message': custom_message,
            'event_type': event_type
        }
        
        # Get notification channels for approver
        channels = self._get_user_notification_channels(approver, event_type)
        
        # Send notifications
        results = {}
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_email_notification(
                        approver, template, template_vars
                    )
                elif channel == NotificationChannel.TEAMS:
                    success = await self._send_teams_notification(
                        approver, template, template_vars
                    )
                elif channel == NotificationChannel.SLACK:
                    success = await self._send_slack_notification(
                        approver, template, template_vars
                    )
                else:
                    success = False
                
                results[f"{approver.id}_{channel.value}"] = success
                
            except Exception as e:
                print(f"Failed to send {channel.value} notification to approver {approver.id}: {e}")
                results[f"{approver.id}_{channel.value}"] = False
        
        return results

    async def send_bulk_notification(
        self,
        request: NotificationRequest
    ) -> Dict[str, bool]:
        """Send bulk notification to multiple recipients"""
        
        # Get recipients
        recipients = await self._get_users_with_preferences(request.recipient_ids)
        
        # Send notifications
        results = {}
        for recipient in recipients:
            for channel_name in request.channels:
                try:
                    channel = NotificationChannel(channel_name)
                    
                    if channel == NotificationChannel.EMAIL:
                        success = await self._send_email_notification(
                            recipient, request.template, {}
                        )
                    elif channel == NotificationChannel.TEAMS:
                        success = await self._send_teams_notification(
                            recipient, request.template, {}
                        )
                    elif channel == NotificationChannel.SLACK:
                        success = await self._send_slack_notification(
                            recipient, request.template, {}
                        )
                    else:
                        success = False
                    
                    results[f"{recipient.id}_{channel.value}"] = success
                    
                except Exception as e:
                    print(f"Failed to send notification to user {recipient.id}: {e}")
                    results[f"{recipient.id}_{channel_name}"] = False
        
        return results

    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: Priority = Priority.MEDIUM,
        admin_only: bool = True
    ) -> Dict[str, bool]:
        """Send system-wide alert to administrators"""
        
        # Get admin users
        if admin_only:
            recipient_ids = await self._get_admin_user_ids()
        else:
            recipient_ids = await self._get_all_active_user_ids()
        
        # Prepare alert template
        template = NotificationTemplate(
            subject=f"System Alert: {alert_type}",
            body=message,
            template_vars={'severity': severity.value, 'alert_type': alert_type}
        )
        
        # Send to all admins via email and in-app
        channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        recipients = await self._get_users_with_preferences(recipient_ids)
        
        results = {}
        for recipient in recipients:
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        success = await self._send_email_notification(
                            recipient, template, template.template_vars
                        )
                    elif channel == NotificationChannel.IN_APP:
                        success = await self._send_in_app_notification(
                            recipient, template, template.template_vars
                        )
                    else:
                        success = False
                    
                    results[f"{recipient.id}_{channel.value}"] = success
                    
                except Exception as e:
                    print(f"Failed to send alert to user {recipient.id}: {e}")
                    results[f"{recipient.id}_{channel.value}"] = False
        
        return results

    async def schedule_reminder_notifications(self) -> None:
        """Schedule and send reminder notifications for overdue items"""
        
        # This would be called by a background task scheduler
        
        # Send overdue ticket reminders
        await self._send_overdue_ticket_reminders()
        
        # Send overdue approval reminders
        await self._send_overdue_approval_reminders()
        
        # Send SLA breach warnings
        await self._send_sla_breach_warnings()

    # Private helper methods

    async def _send_email_notification(
        self,
        recipient: User,
        template: NotificationTemplate,
        template_vars: Dict[str, Any]
    ) -> bool:
        """Send email notification"""
        
        try:
            # Render template
            subject_template = Template(template.subject)
            body_template = Template(template.body)
            
            subject = subject_template.render(**template_vars)
            body = body_template.render(**template_vars)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = recipient.email
            
            # Add body
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(body, "html")  # If HTML template
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, recipient.email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    async def _send_teams_notification(
        self,
        recipient: User,
        template: NotificationTemplate,
        template_vars: Dict[str, Any]
    ) -> bool:
        """Send Microsoft Teams notification"""
        
        try:
            # This would integrate with Microsoft Graph API
            # For now, returning placeholder
            
            # Example Teams message format
            teams_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "summary": template.subject,
                "themeColor": "0078D4",
                "sections": [{
                    "activityTitle": template.subject,
                    "activitySubtitle": f"For: {recipient.first_name} {recipient.last_name}",
                    "text": template.body,
                    "facts": []
                }]
            }
            
            # Send to Teams webhook or via Graph API
            # Implementation would depend on Teams setup
            
            return True
            
        except Exception as e:
            print(f"Teams notification failed: {e}")
            return False

    async def _send_slack_notification(
        self,
        recipient: User,
        template: NotificationTemplate,
        template_vars: Dict[str, Any]
    ) -> bool:
        """Send Slack notification"""
        
        try:
            # This would integrate with Slack API
            # For now, returning placeholder
            
            # Example Slack message format
            slack_message = {
                "text": template.subject,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": template.body
                        }
                    }
                ]
            }
            
            # Send via Slack webhook or Bot API
            # Implementation would depend on Slack setup
            
            return True
            
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False

    async def _send_in_app_notification(
        self,
        recipient: User,
        template: NotificationTemplate,
        template_vars: Dict[str, Any]
    ) -> bool:
        """Send in-app notification"""
        
        try:
            # This would create a notification record in the database
            # and potentially use WebSocket for real-time delivery
            
            # For now, just logging
            print(f"In-app notification for user {recipient.id}: {template.subject}")
            
            return True
            
        except Exception as e:
            print(f"In-app notification failed: {e}")
            return False

    async def _get_ticket_notification_recipients(
        self,
        ticket: Ticket,
        event_type: str
    ) -> List[int]:
        """Get list of user IDs who should receive ticket notifications"""
        
        recipient_ids = []
        
        # Always notify requester and assignee
        if ticket.requester_id:
            recipient_ids.append(ticket.requester_id)
        if ticket.assignee_id and ticket.assignee_id != ticket.requester_id:
            recipient_ids.append(ticket.assignee_id)
        
        # Notify department manager for certain events
        if event_type in ['ticket_created', 'ticket_escalated'] and ticket.department:
            if ticket.department.manager_id:
                recipient_ids.append(ticket.department.manager_id)
        
        # Notify relevant team members based on ticket type
        # This would be configurable based on business rules
        
        return list(set(recipient_ids))  # Remove duplicates

    async def _get_users_with_preferences(self, user_ids: List[int]) -> List[User]:
        """Get users with their notification preferences"""
        
        # This would query users from database
        # For now, returning placeholder
        users = []
        for user_id in user_ids:
            # Query user from database
            # user = await self.session.get(User, user_id)
            # if user:
            #     users.append(user)
            pass
        
        return users

    def _get_user_notification_channels(
        self,
        user: User,
        event_type: str
    ) -> List[NotificationChannel]:
        """Get notification channels for user based on preferences"""
        
        # Check user preferences (stored in user.preferences JSON field)
        preferences = user.preferences or {}
        
        # Default channels
        default_channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        # Get user's preferred channels for this event type
        event_prefs = preferences.get(f'notifications.{event_type}', {})
        
        if 'channels' in event_prefs:
            try:
                return [NotificationChannel(ch) for ch in event_prefs['channels']]
            except ValueError:
                pass
        
        return default_channels

    def _get_template_for_event(self, event_type: str, category: str) -> NotificationTemplate:
        """Get notification template for event type"""
        
        template_key = f"{category}.{event_type}"
        
        if template_key in self.templates:
            return self.templates[template_key]
        
        # Default template
        return NotificationTemplate(
            subject=f"{category.title()} {event_type.replace('_', ' ').title()}",
            body="This is a notification about {{event_type}} for {{category}}."
        )

    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        
        # In a real implementation, these would be loaded from database or files
        return {
            'ticket.ticket_created': NotificationTemplate(
                subject="New Ticket Created: {{ticket.title}}",
                body="A new ticket has been created:\n\nTitle: {{ticket.title}}\nPriority: {{ticket.priority}}\nRequester: {{ticket.requester.first_name}} {{ticket.requester.last_name}}\n\nView ticket: {{ticket_url}}"
            ),
            'ticket.ticket_assigned': NotificationTemplate(
                subject="Ticket Assigned: {{ticket.title}}",
                body="You have been assigned a ticket:\n\nTitle: {{ticket.title}}\nPriority: {{ticket.priority}}\nRequester: {{ticket.requester.first_name}} {{ticket.requester.last_name}}\n\nView ticket: {{ticket_url}}"
            ),
            'ticket.status_changed': NotificationTemplate(
                subject="Ticket Status Updated: {{ticket.title}}",
                body="Ticket status has been updated:\n\nTitle: {{ticket.title}}\nNew Status: {{ticket.status}}\n\nView ticket: {{ticket_url}}"
            ),
            'approval.approval_requested': NotificationTemplate(
                subject="Approval Required: {{ticket.title}}",
                body="Your approval is required for:\n\nTitle: {{ticket.title}}\nRequester: {{ticket.requester.first_name}} {{ticket.requester.last_name}}\nDue Date: {{approval_step.due_date}}\n\nApprove or reject: {{approval_url}}"
            ),
            'approval.approval_overdue': NotificationTemplate(
                subject="Overdue Approval: {{ticket.title}}",
                body="You have an overdue approval:\n\nTitle: {{ticket.title}}\nRequester: {{ticket.requester.first_name}} {{ticket.requester.last_name}}\nDue Date: {{approval_step.due_date}}\n\nPlease review: {{approval_url}}"
            )
        }

    async def _send_overdue_ticket_reminders(self) -> None:
        """Send reminders for overdue tickets"""
        # Implementation would query overdue tickets and send notifications
        pass

    async def _send_overdue_approval_reminders(self) -> None:
        """Send reminders for overdue approvals"""
        # Implementation would query overdue approvals and send notifications
        pass

    async def _send_sla_breach_warnings(self) -> None:
        """Send warnings for potential SLA breaches"""
        # Implementation would check tickets approaching SLA limits
        pass

    async def _get_admin_user_ids(self) -> List[int]:
        """Get list of admin user IDs"""
        # Query admin users from database
        return []

    async def _get_all_active_user_ids(self) -> List[int]:
        """Get list of all active user IDs"""
        # Query all active users from database
        return []