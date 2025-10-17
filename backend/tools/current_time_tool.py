"""
Current Time Tool - provides current date and time information in a structured JSON format.
"""

from typing import Any, Dict
from datetime import datetime
import pytz
from .base_tool import BaseTool


class CurrentTimeTool(BaseTool):
    """
    Simple tool that returns current date and time information in JSON format.
    """

    @property
    def name(self) -> str:
        return "current_time"

    @property
    def description(self) -> str:
        return """Get date and time information with accurate day-of-week calculation.

🚨 CRITICAL USAGE RULES:
1. When user mentions ANY date (like "October 13", "next month on 10th", "tomorrow"):
   → ALWAYS call: current_time(target_date="the date they mentioned")
2. NEVER call current_time() without parameters when user mentions a specific date
3. NEVER try to calculate day-of-week yourself - the tool does it accurately

Args:
    target_date (str, optional): The date to get information about. 
        Examples of CORRECT usage:
        - current_time(target_date="October 13")
        - current_time(target_date="October 13, 2025")  
        - current_time(target_date="next month on 10th") → will parse as Nov 10
        - current_time(target_date="tomorrow")
        - current_time(target_date="10/13/2025")
        - current_time(target_date="November 10")
        If not provided, returns current date/time only.

Returns:
    JSON with: Day, Month, MonthName, Year, DayOfWeek, TimeZone, FormattedDate, RelativeToToday
    
Example:
    User: "How about October 13th?"
    YOU MUST: current_time(target_date="October 13")
    Response: {"DayOfWeek": "Monday", "FormattedDate": "Monday, October 13, 2025", ...}
    Then say: "Perfect! That's Monday, October 13th..."
"""

    def execute(self, target_date: str = None) -> Dict[str, Any]:
        """
        Get current date and time information, or info about a specific date.
        
        Args:
            target_date: Optional date string to get information about
        
        Returns:
            Dict containing date/time details with day of week and formatted strings
        """
        try:
            from dateutil import parser as date_parser
            from datetime import timedelta
            
            # Get current local time for reference
            now_local = datetime.now()
            
            # Determine which date to use
            if target_date:
                # Parse the target date
                target_date_clean = target_date.strip().lower()
                
                # Handle relative dates
                if target_date_clean == "tomorrow":
                    target_dt = now_local + timedelta(days=1)
                elif target_date_clean == "today":
                    target_dt = now_local
                elif "next" in target_date_clean and "week" in target_date_clean:
                    target_dt = now_local + timedelta(days=7)
                elif "next month" in target_date_clean:
                    # Handle "next month on 10th" or "next month on the 10th"
                    try:
                        # Extract day number
                        import re
                        day_match = re.search(r'(\d+)', target_date_clean)
                        if day_match:
                            day = int(day_match.group(1))
                            # Go to next month
                            next_month = now_local.month + 1
                            next_year = now_local.year
                            if next_month > 12:
                                next_month = 1
                                next_year += 1
                            target_dt = now_local.replace(year=next_year, month=next_month, day=day, hour=12, minute=0, second=0, microsecond=0)
                        else:
                            # Just "next month" without day
                            next_month = now_local.month + 1
                            next_year = now_local.year
                            if next_month > 12:
                                next_month = 1
                                next_year += 1
                            target_dt = now_local.replace(year=next_year, month=next_month, day=1)
                    except:
                        target_dt = date_parser.parse(target_date, default=now_local)
                else:
                    # Try to parse the date string
                    try:
                        # If only month and day are provided, assume current year
                        target_dt = date_parser.parse(target_date, default=now_local)
                    except:
                        # If parsing fails, default to current time
                        target_dt = now_local
            else:
                target_dt = now_local
            
            # Get local timezone info
            local_tz = target_dt.astimezone().tzinfo
            
            # Get timezone abbreviation (EST, PST, etc.)
            tz_name = target_dt.strftime('%Z')
            
            # Calculate days from now
            days_diff = (target_dt.date() - now_local.date()).days
            relative_desc = ""
            if days_diff == 0:
                relative_desc = "TODAY"
            elif days_diff == 1:
                relative_desc = "tomorrow"
            elif days_diff == -1:
                relative_desc = "yesterday"
            elif days_diff > 1:
                relative_desc = f"in {days_diff} days"
            elif days_diff < -1:
                relative_desc = f"{abs(days_diff)} days ago"
            
            # Format the response
            return {
                "Day": target_dt.day,
                "Month": target_dt.month,
                "MonthName": target_dt.strftime('%B'),  # Full month name (e.g., "October")
                "Year": target_dt.year,
                "Hour": target_dt.hour,
                "Min": target_dt.minute,
                "Second": target_dt.second,
                "DayOfWeek": target_dt.strftime('%A'),  # Full day name (e.g., "Monday")
                "TimeZone": str(local_tz),
                "TimeZoneAbbr": tz_name if tz_name else str(local_tz),  # Abbreviation like "EST"
                "FormattedDate": target_dt.strftime('%A, %B %d, %Y'),  # "Monday, October 13, 2025"
                "FormattedTime": target_dt.strftime('%I:%M %p %Z'),  # "08:30 PM EST"
                "FullDateTime": target_dt.strftime('%A, %B %d, %Y at %I:%M %p %Z'),  # Complete string
                "ISO8601": target_dt.isoformat(),  # Standard ISO format
                "RelativeToToday": relative_desc,
                "_raw_note": f"TODAY is {now_local.strftime('%A, %B %d, %Y')}. The date you asked about ({target_date if target_date else 'today'}) is {target_dt.strftime('%A, %B %d, %Y')} ({relative_desc}).",
                "_is_target_date": target_date is not None
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get time/date: {str(e)}",
                "Day": None,
                "Month": None,
                "Year": None,
                "Hour": None,
                "Min": None,
                "Second": None,
                "TimeZone": None,
                "_error_detail": f"Input was: '{target_date}'"
            }
