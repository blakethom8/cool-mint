#!/usr/bin/env python3
"""
Background Sync Runner for Salesforce Contact Sync

This script provides multiple options for running the contact sync in the background
with proper logging, monitoring, and process management.
"""

import sys
import os
import subprocess
import signal
import time
import json
from datetime import datetime
from typing import Optional
import psutil

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)


class BackgroundSyncRunner:
    """Manager for running contact sync operations in the background."""

    def __init__(self):
        self.sync_script = (
            "app/services/salesforce_files/production_contact_sync_bulk.py"
        )
        self.pid_file = "bulk_sync.pid"
        self.status_file = "sync_status.json"

    def start_background_sync(
        self, sync_type: str = "full", days: Optional[int] = None
    ) -> bool:
        """Start a sync process in the background."""

        # Check if already running
        if self.is_sync_running():
            print("❌ Sync is already running!")
            self.show_sync_status()
            return False

        # Build command
        cmd = ["python", self.sync_script]
        if sync_type == "test":
            cmd.append("--test")
        elif sync_type == "incremental" and days:
            cmd.extend(["--incremental", str(days)])
        else:
            cmd.append("--full")

        print(f"🚀 Starting background sync: {' '.join(cmd)}")

        try:
            # Start process in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root,
                start_new_session=True,  # Detach from current session
            )

            # Save PID and status
            self._save_pid(process.pid)
            self._save_status(
                {
                    "pid": process.pid,
                    "command": " ".join(cmd),
                    "start_time": datetime.now().isoformat(),
                    "status": "running",
                    "sync_type": sync_type,
                }
            )

            print(f"✅ Background sync started with PID: {process.pid}")
            print(f"📋 Monitor with: python {__file__} --status")
            print(f"🛑 Stop with: python {__file__} --stop")
            print(f"📄 View logs: tail -f bulk_contact_sync.log")

            return True

        except Exception as e:
            print(f"❌ Failed to start background sync: {str(e)}")
            return False

    def stop_sync(self) -> bool:
        """Stop the running sync process."""

        if not self.is_sync_running():
            print("ℹ️  No sync process is currently running")
            return True

        try:
            pid = self._get_pid()
            if pid:
                print(f"🛑 Stopping sync process (PID: {pid})...")

                # Try graceful shutdown first
                os.kill(pid, signal.SIGTERM)

                # Wait for graceful shutdown
                for _ in range(10):
                    if not self._is_process_running(pid):
                        break
                    time.sleep(1)

                # Force kill if still running
                if self._is_process_running(pid):
                    print("⚠️  Graceful shutdown failed, forcing termination...")
                    os.kill(pid, signal.SIGKILL)

                # Clean up files
                self._cleanup_files()
                print("✅ Sync process stopped")
                return True

        except ProcessLookupError:
            print("ℹ️  Process was already stopped")
            self._cleanup_files()
            return True
        except Exception as e:
            print(f"❌ Error stopping sync: {str(e)}")
            return False

    def show_sync_status(self) -> bool:
        """Show the current status of the sync process."""

        if not self.is_sync_running():
            print("📊 SYNC STATUS: Not running")

            # Check for last run info
            if os.path.exists(self.status_file):
                try:
                    with open(self.status_file, "r") as f:
                        last_status = json.load(f)

                    print(f"📅 Last run: {last_status.get('start_time', 'Unknown')}")
                    print(f"🔧 Last command: {last_status.get('command', 'Unknown')}")
                    print(f"📋 Last status: {last_status.get('status', 'Unknown')}")
                except:
                    pass

            return False

        try:
            status = self._get_status()
            pid = status.get("pid")

            print("📊 SYNC STATUS: Running")
            print("=" * 40)
            print(f"🆔 PID: {pid}")
            print(f"⚡ Command: {status.get('command', 'Unknown')}")
            print(f"📅 Started: {status.get('start_time', 'Unknown')}")
            print(f"🔧 Type: {status.get('sync_type', 'Unknown')}")

            # Get process info
            if pid:
                try:
                    process = psutil.Process(pid)

                    # Calculate runtime
                    start_time = datetime.fromisoformat(status.get("start_time", ""))
                    runtime = datetime.now() - start_time

                    print(f"⏱️  Runtime: {runtime}")
                    print(
                        f"💾 Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB"
                    )
                    print(f"🔥 CPU: {process.cpu_percent()}%")

                except Exception as e:
                    print(f"⚠️  Could not get detailed process info: {e}")

            print("=" * 40)
            print("📄 View real-time logs: tail -f bulk_contact_sync.log")
            print("🛑 Stop sync: python background_sync_runner.py --stop")

            return True

        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")
            return False

    def monitor_sync(self, refresh_seconds: int = 30) -> None:
        """Monitor the sync process with periodic updates."""

        print("🔍 SYNC MONITOR (Press Ctrl+C to exit)")
        print("=" * 50)

        try:
            while True:
                os.system("clear" if os.name == "posix" else "cls")  # Clear screen

                print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 50)

                if self.is_sync_running():
                    self.show_sync_status()

                    # Show log tail
                    print("\n📄 RECENT LOG ENTRIES:")
                    print("-" * 30)
                    try:
                        result = subprocess.run(
                            ["tail", "-5", "bulk_contact_sync.log"],
                            capture_output=True,
                            text=True,
                            cwd=project_root,
                        )
                        if result.stdout:
                            print(result.stdout)
                    except:
                        print("Could not read log file")
                else:
                    print("📊 SYNC STATUS: Not running")
                    break

                print(
                    f"\n🔄 Refreshing in {refresh_seconds} seconds... (Ctrl+C to exit)"
                )
                time.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped")

    def is_sync_running(self) -> bool:
        """Check if a sync process is currently running."""
        pid = self._get_pid()
        return pid is not None and self._is_process_running(pid)

    def _get_pid(self) -> Optional[int]:
        """Get the PID of the running sync process."""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, "r") as f:
                    return int(f.read().strip())
        except:
            pass
        return None

    def _save_pid(self, pid: int) -> None:
        """Save the PID to file."""
        with open(self.pid_file, "w") as f:
            f.write(str(pid))

    def _get_status(self) -> dict:
        """Get the current status from file."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r") as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_status(self, status: dict) -> None:
        """Save status to file."""
        with open(self.status_file, "w") as f:
            json.dump(status, f, indent=2)

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            return psutil.pid_exists(pid)
        except:
            # Fallback method
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def _cleanup_files(self) -> None:
        """Clean up PID and status files."""
        for file in [self.pid_file, self.status_file]:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass


def show_usage():
    """Show usage instructions."""
    print("""
🚀 SALESFORCE CONTACT SYNC - BACKGROUND RUNNER

Usage:
    python background_sync_runner.py [OPTION]

Options:
    --start-full           Start full contact sync in background
    --start-incremental N  Start incremental sync (N days back)
    --start-test          Start test connection in background
    --status              Show current sync status
    --stop                Stop running sync
    --monitor             Monitor sync with live updates
    --help                Show this help

Examples:
    # Start full sync in background
    python background_sync_runner.py --start-full
    
    # Start incremental sync for last 7 days
    python background_sync_runner.py --start-incremental 7
    
    # Check if sync is running
    python background_sync_runner.py --status
    
    # Monitor sync progress
    python background_sync_runner.py --monitor
    
    # Stop sync
    python background_sync_runner.py --stop

Files created:
    - bulk_sync.pid: Process ID file
    - sync_status.json: Sync status information
    - bulk_contact_sync.log: Detailed sync logs
    """)


def main():
    """Main function for background sync management."""

    runner = BackgroundSyncRunner()

    if len(sys.argv) < 2:
        show_usage()
        return

    command = sys.argv[1]

    if command == "--start-full":
        runner.start_background_sync("full")

    elif command == "--start-incremental":
        if len(sys.argv) < 3:
            print("❌ Please specify number of days: --start-incremental N")
            return
        try:
            days = int(sys.argv[2])
            runner.start_background_sync("incremental", days)
        except ValueError:
            print("❌ Please provide a valid number of days")

    elif command == "--start-test":
        runner.start_background_sync("test")

    elif command == "--status":
        runner.show_sync_status()

    elif command == "--stop":
        runner.stop_sync()

    elif command == "--monitor":
        runner.monitor_sync()

    elif command == "--help":
        show_usage()

    else:
        print(f"❌ Unknown command: {command}")
        show_usage()


if __name__ == "__main__":
    main()
