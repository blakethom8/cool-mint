from datetime import datetime
from typing import Dict, Any
import logging
import json
import os

logger = logging.getLogger(__name__)


class SalesforceMonitoring:
    """Wrapper for monitoring Salesforce API usage."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log_api_call(self, operation: str, details: Dict[str, Any] = None):
        """Log API call details for monitoring."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "details": details or {},
        }

        # Log to file
        log_file = os.path.join(
            self.log_dir, f"salesforce_api_{datetime.now().strftime('%Y%m%d')}.log"
        )
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Log to console
        logger.info(f"Salesforce API call: {operation}")

    def check_api_limits(self, current_limits: Dict[str, Any]) -> bool:
        """
        Check if we're approaching API limits.
        Returns True if usage is safe, False if we're approaching limits.
        """
        daily_limit = current_limits.get("DailyApiRequests", {})
        remaining = daily_limit.get("Remaining", 0)
        maximum = daily_limit.get("Max", 0)

        if maximum == 0:
            return True

        usage_percentage = ((maximum - remaining) / maximum) * 100

        if usage_percentage > 80:
            logger.warning(
                f"High API usage: {usage_percentage:.1f}% of daily limit used"
            )
            return False

        return True

    def get_usage_report(self, start_date: str = None) -> Dict[str, Any]:
        """Generate usage report from logs."""
        if not start_date:
            start_date = datetime.now().strftime("%Y%m%d")

        log_file = os.path.join(self.log_dir, f"salesforce_api_{start_date}.log")
        if not os.path.exists(log_file):
            return {"error": "No logs found for date"}

        operations = {}
        with open(log_file, "r") as f:
            for line in f:
                entry = json.loads(line)
                op = entry["operation"]
                operations[op] = operations.get(op, 0) + 1

        return {
            "date": start_date,
            "total_calls": sum(operations.values()),
            "operations": operations,
        }
