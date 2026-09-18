from datetime import datetime


class ReplayRecorder:

    def __init__(self, scenario_name):
        self.scenario_name = scenario_name
        self.events = []

    def record(self, message):
        event = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": message
        }

        self.events.append(event)

    def show(self):
        print()
        print(f"FAILURE REPLAY: {self.scenario_name}")
        print("=" * 40)

        for event in self.events:
            print(
                f"{event['time']}  "
                f"{event['message']}"
            )

        print()