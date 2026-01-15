from datetime import datetime, timedelta

def generate_plan(tasks, available_hours):

    # Sort by deadline, then difficulty
    tasks = sorted(tasks, key=lambda x: (x["deadline"], -x["difficulty"]))

    schedule = []
    current_time = datetime.strptime("09:00", "%H:%M")
    hours_left = available_hours

    work_blocks = [2, 1.5, 1.5, 1]  # realistic human flow

    while hours_left > 0 and tasks:
        for block in work_blocks:
            if hours_left <= 0:
                break

            task = tasks[0]

            duration = min(block, hours_left, task["time"])
            start = current_time
            end = start + timedelta(hours=duration)

            schedule.append({
                "task": task["name"],
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "duration": round(duration, 2)
            })

            task["time"] -= duration
            hours_left -= duration

            current_time = end + timedelta(minutes=15)  # realistic break

            if task["time"] <= 0:
                tasks.pop(0)

    return schedule
