"""Notification service for Email and Zalo."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
import requests
from datetime import date
from config.settings import settings


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
        
        Returns:
            Tuple: (success, message)
        """
        if not settings.smtp_username or not settings.smtp_password:
            return False, "Email configuration not set"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.email_from or settings.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text and HTML parts
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    @staticmethod
    def is_configured() -> bool:
        """Check if email is properly configured."""
        return bool(settings.smtp_username and settings.smtp_password)


class ZaloService:
    """Service for sending Zalo notifications."""
    
    @staticmethod
    def send_message(
        phone_number: str,
        message: str
    ) -> Tuple[bool, str]:
        """
        Send Zalo message notification.
        
        Args:
            phone_number: Recipient phone number
            message: Message content
        
        Returns:
            Tuple: (success, message)
        """
        if not settings.zalo_access_token:
            return False, "Zalo configuration not set"
        
        try:
            # Zalo API endpoint (this is a placeholder - adjust based on actual Zalo API)
            url = "https://openapi.zalo.me/v2.0/oa/message"
            
            headers = {
                'access_token': settings.zalo_access_token,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'recipient': {
                    'phone_number': phone_number
                },
                'message': {
                    'text': message
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return True, "Zalo message sent successfully"
            else:
                return False, f"Zalo API error: {response.text}"
                
        except Exception as e:
            return False, f"Failed to send Zalo message: {str(e)}"
    
    @staticmethod
    def is_configured() -> bool:
        """Check if Zalo is properly configured."""
        return bool(settings.zalo_access_token)


class NotificationService:
    """Unified notification service."""
    
    def __init__(self):
        """Initialize notification service."""
        self.email_service = EmailService()
        self.zalo_service = ZaloService()
    
    def send_allocation_reminder(
        self,
        expense_name: str,
        quarter: int,
        year: int,
        amount: float,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> dict:
        """
        Send allocation reminder via email and/or Zalo.
        
        Args:
            expense_name: Name of the expense
            quarter: Quarter number
            year: Year
            amount: Allocation amount
            email: Email address (optional)
            phone: Phone number (optional)
        
        Returns:
            Dictionary with results for each channel
        """
        results = {}
        
        # Prepare message
        subject = f"Nhắc nhở phân bổ chi phí Q{quarter}/{year}"
        message = f"""
Nhắc nhở phân bổ chi phí trả trước:

Khoản mục: {expense_name}
Quý: Q{quarter}/{year}
Số tiền phân bổ: {amount:,.0f} ₫

Vui lòng thực hiện phân bổ trước ngày kết thúc quý.
        """.strip()
        
        # Send email if configured and email provided
        if email and self.email_service.is_configured():
            success, msg = self.email_service.send_email(
                to_email=email,
                subject=subject,
                body=message
            )
            results['email'] = {'success': success, 'message': msg}
        
        # Send Zalo if configured and phone provided
        if phone and self.zalo_service.is_configured():
            success, msg = self.zalo_service.send_message(
                phone_number=phone,
                message=message
            )
            results['zalo'] = {'success': success, 'message': msg}
        
        return results
    
    def get_configured_channels(self) -> list:
        """Get list of configured notification channels."""
        channels = []
        if self.email_service.is_configured():
            channels.append('email')
        if self.zalo_service.is_configured():
            channels.append('zalo')
        return channels
