import asyncio
import time
import re
from datetime import datetime
from desktop_notifier import DesktopNotifier
from rubicon import *


class RollMarkingReminder:
    def __init__(self, debug=False):
        self.debug = debug
        self.notifier = DesktopNotifier()

    async def send_notification(self):
        await self.notifier.send(
            title="Roll Marking Reminder",
            message="Have you marked your roll?\nHave you updated students who arrived late?"
        )

    def is_weekday(self):
        day_of_week = datetime.now().isoweekday()  # 1 = Monday, 7 = Sunday
        return 1 <= day_of_week <= 5

    def get_ip_address(self):
        import subprocess
        result = subprocess.run(
            ["/sbin/ifconfig", "en0"], stdout=subprocess.PIPE, text=True
        )
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", result.stdout)
        return match.group(1) if match else None

    def is_staff_subnet(self, ip_address):
        return re.match(r"^10\.10\.(4|5|6|7)\.\d+$", ip_address) is not None

    async def main(self):
        while True:
            # Calculate sleep time until the next full minute
            now = time.time()
            sleep_time = 60 - (now % 60)
            await asyncio.sleep(sleep_time)

            ip_address = self.get_ip_address()
            if self.is_weekday():
                if self.debug:
                    print("Debug mode enabled. Sending notifications instantly.")
                    await self.send_notification()
                elif ip_address and self.is_staff_subnet(ip_address):
                    current_time = datetime.now().strftime("%H:%M")
                    if current_time in ["11:20", "15:30"]:
                        await self.send_notification()
            elif self.debug:
                print("Debug mode enabled, but today is a weekend. Skipping notification.")


if __name__ == "__main__":
    reminder = RollMarkingReminder(debug=False)
    asyncio.run(reminder.main())
