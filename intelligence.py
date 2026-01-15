from models import StudySession, Task

def update_streak(user):
    from datetime import date, timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)

    today_sessions = StudySession.query.filter_by(date=today).count()
    yesterday_sessions = StudySession.query.filter_by(date=yesterday).count()

    if today_sessions > 0:
        if yesterday_sessions > 0:
            user.streak += 1
        else:
            user.streak = 1
    else:
        user.streak = 0

def get_weak_subjects():
    tasks = Task.query.all()
    data = {}
    for t in tasks:
        sessions = StudySession.query.filter_by(task_name=t.name).all()
        data[t.name] = sum(s.hours_spent for s in sessions)
    return sorted(data.items(), key=lambda x: x[1])

def compute_efficiency(today_sessions, schedule):
    planned = sum(b["hours"] for b in schedule)
    done = sum(s.hours_spent for s in today_sessions)
    return round((done / planned) * 100, 2) if planned else 0

def generate_feedback(efficiency, weak_subjects, overload=0):
    if efficiency >= 80:
        msg = "Excellent discipline today. You're building real momentum. "
    elif efficiency >= 50:
        msg = "Good progress — tighten focus and you'll accelerate. "
    else:
        msg = "Rough day — but showing up matters. Tomorrow is yours. "

    if weak_subjects:
        msg += f"Focus more on {weak_subjects[0][0]}. "

    if overload:
        msg += "Protect your energy. Burnout kills consistency."

    return msg
