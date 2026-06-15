"""
email_service.py — Email service for sending violation alerts.

Supports both SMTP (Gmail, Outlook) and SendGrid API.
Uses templated HTML emails for professional violation reports.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """Service to send violation alert emails."""
    
    def __init__(self):
        self.email_service = os.getenv("EMAIL_SERVICE", "smtp").lower()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        if self.email_service == "smtp" and not self.sender_email:
            print("[EmailService] WARNING: SMTP configured but SENDER_EMAIL not set")
        if self.email_service == "sendgrid" and not self.sendgrid_api_key:
            print("[EmailService] WARNING: SendGrid configured but SENDGRID_API_KEY not set")
    
    def send_violation_alert(
        self,
        recipient_email: str,
        video_title: str,
        violations: list[dict],
        violation_filter: str = "all"  # "critical", "high", "all"
    ) -> dict:
        """
        Send a violation alert email.
        
        Args:
            recipient_email: Email to send to
            video_title: Original uploaded video title
            violations: List of violation records with url, match_score, risk_level, etc.
            violation_filter: Filter violations by severity ("critical", "high", "all")
        
        Returns:
            Dict with status, message_id, and error (if any)
        """
        # Filter violations by severity
        filtered_violations = self._filter_violations(violations, violation_filter)
        
        if not filtered_violations:
            return {
                "success": False,
                "message": "No violations match the selected filter",
                "sent": False
            }
        
        # Generate HTML email
        html_content = self._generate_email_html(video_title, filtered_violations)
        subject = f"🚨 {len(filtered_violations)} Unauthorized Copies Detected"
        
        # Send via configured service
        try:
            if self.email_service == "sendgrid":
                return self._send_via_sendgrid(recipient_email, subject, html_content)
            else:
                return self._send_via_smtp(recipient_email, subject, html_content)
        except Exception as e:
            return {
                "success": False,
                "sent": False,
                "error": str(e)
            }
    
    def _filter_violations(self, violations: list[dict], filter_level: str) -> list[dict]:
        """Filter violations by risk level."""
        if filter_level == "critical":
            return [v for v in violations if v.get("risk_level") == "critical"]
        elif filter_level == "high":
            return [v for v in violations if v.get("risk_level") in ["critical", "high"]]
        else:  # "all"
            return violations
    
    def _generate_email_html(self, video_title: str, violations: list[dict]) -> str:
        """Generate professional HTML email with violation summary."""
        
        violation_rows = ""
        for v in violations[:10]:  # Limit to 10 in email
            match_score = round(v.get("match_score", 0) * 100, 1)
            risk_level = v.get("risk_level", "unknown").upper()
            watermark_status = "✓ Found" if v.get("watermark_found") else "✗ Not found"
            
            violation_rows += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px; font-size: 13px;">
                    <a href="{v.get('url', '#')}" target="_blank" style="color: #0066cc; text-decoration: none;">
                        {v.get('url', 'Unknown')[:60]}...
                    </a>
                </td>
                <td style="padding: 12px; text-align: center; font-size: 13px;">{match_score}%</td>
                <td style="padding: 12px; text-align: center;">
                    <span style="background: {'#d32f2f' if risk_level == 'CRITICAL' else '#f57c00'}; 
                                 color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        {risk_level}
                    </span>
                </td>
                <td style="padding: 12px; text-align: center; font-size: 13px;">{watermark_status}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
                .footer {{ color: #666; font-size: 12px; text-align: center; padding-top: 20px; border-top: 1px solid #eee; }}
                .action-btn {{ display: inline-block; background: #667eea; color: white; 
                              padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Unauthorized Copies Detected</h1>
                    <p>Your video "{video_title}" has been found on {len(violations)} unauthorized platform(s)</p>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    <p>We have detected {len(violations)} unauthorized use(s) of your content. Below is a summary of the violations:</p>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Video URL</th>
                                <th>Match Score</th>
                                <th>Risk Level</th>
                                <th>Watermark</th>
                            </tr>
                        </thead>
                        <tbody>
                            {violation_rows}
                        </tbody>
                    </table>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Review the violation details above</li>
                        <li>Visit each URL to assess the severity</li>
                        <li>File DMCA takedown requests if necessary</li>
                        <li>Contact the platform's support team</li>
                    </ul>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="https://your-dashboard-url.com" class="action-btn">View Full Report</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from Digital Asset Protection.</p>
                    <p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _send_via_smtp(self, recipient_email: str, subject: str, html_content: str) -> dict:
        """Send email via SMTP (Gmail, Outlook, etc.)."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            
            # Attach HTML
            part = MIMEText(html_content, "html")
            msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
            
            return {
                "success": True,
                "sent": True,
                "recipient": recipient_email,
                "method": "smtp"
            }
        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "sent": False,
                "error": f"SMTP authentication failed: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "sent": False,
                "error": str(e)
            }
    
    def _send_via_sendgrid(self, recipient_email: str, subject: str, html_content: str) -> dict:
        """Send email via SendGrid API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=self.sender_email,
                to_emails=recipient_email,
                subject=subject,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            return {
                "success": response.status_code == 202,
                "sent": response.status_code == 202,
                "status_code": response.status_code,
                "recipient": recipient_email,
                "method": "sendgrid"
            }
        except Exception as e:
            return {
                "success": False,
                "sent": False,
                "error": str(e)
            }


# Create global instance
email_service = EmailService()
