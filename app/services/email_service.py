"""
Email service for sending maintenance reminders.
"""
import asyncio
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import List, Dict, Any, Tuple

from app.config import Config


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    @staticmethod
    async def get_upcoming_maintenance(data: List[Dict[str, Any]], days_ahead: int = None) -> List[Tuple[str, str, str, str, str, str]]:
        """Get upcoming maintenance within specified days.

        Args:
            data: List of PPM entries
            days_ahead: Days ahead to check (default: from config)

        Returns:
            List of upcoming maintenance as (equipment, mfg_serial, quarter, department, date, engineer)
        """
        if days_ahead is None:
            days_ahead = Config.REMINDER_DAYS

        now = datetime.now()
        upcoming = []

        for entry in data:
            if entry.get('PPM', '').lower() != 'yes':
                continue

            for q in ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']:
                q_data = entry.get(q, {})
                if not q_data or not q_data.get('date'):
                    continue

                try:
                    due_date = datetime.strptime(q_data['date'], '%d/%m/%Y')
                    days_until = (due_date - now).days

                    if 0 <= days_until <= days_ahead:
                        # Include the department field
                        upcoming.append((
                            entry['EQUIPMENT'],
                            entry['MFG_SERIAL'],
                            q.replace('PPM_Q_', 'Quarter '),
                            entry.get('DEPARTMENT', 'N/A'),  # Add department field
                            q_data['date'],
                            q_data['engineer']
                        ))
                except (ValueError, KeyError) as e:
                    logger.error(f"Error parsing date for {entry.get('MFG_SERIAL', 'unknown')}: {str(e)}")

        # Sort by date
        upcoming.sort(key=lambda x: datetime.strptime(x[4], '%d/%m/%Y'))  # Updated index for date
        return upcoming

    @staticmethod
    async def send_reminder_email(upcoming: List[Tuple[str, str, str, str, str, str]]) -> bool:
        """Send reminder email for upcoming maintenance.

        Args:
            upcoming: List of upcoming maintenance as (equipment, mfg_serial, quarter, department, date, engineer)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not upcoming:
            logger.info("No upcoming maintenance to send reminders for")
            return True

        try:
            # Reload configuration to get the latest email settings
            from app.utils.config_reloader import reload_config
            reload_config()
            logger.info("Configuration reloaded before sending email")

            msg = EmailMessage()

            # Email content
            subject = f"Hospital Equipment Maintenance Reminder - {len(upcoming)} upcoming tasks"

            # Create HTML content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Upcoming Equipment Maintenance</h2>
                    <p>The following equipment requires maintenance in the next {Config.REMINDER_DAYS} days:</p>
                </div>
                <table>
                    <tr>
                        <th>Equipment</th>
                        <th>Serial Number</th>
                        <th>Quarter</th>
                        <th>Department</th>
                        <th>Due Date</th>
                        <th>Engineer</th>
                    </tr>
            """

            for equipment, serial, quarter, department, date, engineer in upcoming:
                html_content += f"""
                    <tr>
                        <td>{equipment}</td>
                        <td>{serial}</td>
                        <td>{quarter}</td>
                        <td>{department}</td>
                        <td>{date}</td>
                        <td>{engineer}</td>
                    </tr>
                """

            html_content += """
                </table>
                <p>Please ensure these maintenance tasks are completed on time.</p>
                <p>This is an automated reminder from the Hospital Equipment Maintenance System.</p>
            </body>
            </html>
            """

            # Set up email
            msg.set_content("Please view this email with an HTML-compatible email client.")
            msg.add_alternative(html_content, subtype='html')

            msg['Subject'] = subject
            msg['From'] = Config.EMAIL_SENDER
            msg['To'] = Config.EMAIL_RECEIVER

            # Add CC recipients if configured
            cc_recipients = []
            if Config.CC_EMAIL_1 and Config.CC_EMAIL_1.strip():
                cc_recipients.append(Config.CC_EMAIL_1)
            if Config.CC_EMAIL_2 and Config.CC_EMAIL_2.strip():
                cc_recipients.append(Config.CC_EMAIL_2)
            if Config.CC_EMAIL_3 and Config.CC_EMAIL_3.strip():
                cc_recipients.append(Config.CC_EMAIL_3)

            if cc_recipients:
                msg['Cc'] = ', '.join(cc_recipients)
                logger.info(f"Adding CC recipients: {cc_recipients}")

            # Log email settings being used (without password)
            logger.info(f"Sending email using: SMTP_SERVER={Config.SMTP_SERVER}, SMTP_PORT={Config.SMTP_PORT}, " +
                       f"SMTP_USERNAME={Config.SMTP_USERNAME}, EMAIL_SENDER={Config.EMAIL_SENDER}, " +
                       f"EMAIL_RECEIVER={Config.EMAIL_RECEIVER}")

            # Send email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Reminder email sent for {len(upcoming)} upcoming maintenance tasks to {Config.EMAIL_RECEIVER}")
            return True

        except Exception as e:
            logger.error(f"Failed to send reminder email: {str(e)}")
            return False

    @staticmethod
    async def process_reminders():
        """Process and send reminders for upcoming maintenance."""
        from app.services.data_service import DataService
        from app.utils.config_reloader import reload_config

        try:
            # Reload configuration to get the latest settings
            reload_config()
            logger.info("Configuration reloaded before processing reminders")

            # Load PPM data
            ppm_data = DataService.load_data('ppm')

            # Get upcoming maintenance
            upcoming = await EmailService.get_upcoming_maintenance(ppm_data)

            # Send reminder if there are upcoming maintenance tasks
            if upcoming:
                await EmailService.send_reminder_email(upcoming)
            else:
                logger.info("No upcoming maintenance tasks found")

        except Exception as e:
            logger.error(f"Error processing reminders: {str(e)}")

    @staticmethod
    async def run_scheduler():
        """Run scheduler for periodic reminder sending."""
        from app.utils.config_reloader import reload_config

        # Reload configuration to get the latest settings
        reload_config()

        if not Config.SCHEDULER_ENABLED:
            logger.info("Reminder scheduler is disabled")
            return

        logger.info(f"Starting reminder scheduler (interval: {Config.SCHEDULER_INTERVAL} hours)")

        while True:
            await EmailService.process_reminders()

            # Reload configuration before sleeping to get the latest interval
            reload_config()
            await asyncio.sleep(Config.SCHEDULER_INTERVAL * 3600)  # Convert hours to seconds
