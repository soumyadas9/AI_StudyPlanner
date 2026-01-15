from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta, date

from models import db, User, Task, StudySession
from intelligence import update_streak, get_weak_subjects, compute_efficiency, generate_feedback

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///focusflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- Scheduler ----------------
def generate_schedule(tasks, daily_hours):
    """
    Realistic schedule generator:
    - Uses mixed block sizes: 1.5, 1, 0.5
    - Inserts breaks: 15 min after >=1 hr, 10 min after 0.5 hr
    - Prioritizes urgent/difficult tasks
    """
    block_sizes = [1.5, 1, 0.5]
    today = datetime.today().date()
    current_time = datetime.strptime("09:00", "%H:%M")
    hours_left = daily_hours
    schedule = []

    # Task pool with remaining hours and daily share
    task_pool = []
    for t in tasks:
        days_left = max((t["deadline"] - today).days + 1, 1)
        daily_share = t["hours"] / days_left
        task_pool.append({
            "name": t["name"],
            "difficulty": t["difficulty"],
            "remaining": t["hours"],
            "daily_share": daily_share
        })

    while hours_left > 0 and any(t["remaining"] > 0 for t in task_pool):
        # sort by urgency (daily_share) then difficulty
        task_pool.sort(key=lambda x: (-x["daily_share"], -x["difficulty"]))

        for task in task_pool:
            if task["remaining"] <= 0 or hours_left <= 0:
                continue

            # pick a block that is <= remaining & <= hours left
            possible_blocks = [b for b in block_sizes if b <= task["remaining"] and b <= hours_left]
            if not possible_blocks:
                continue

            # 🎯 Human-style block selection
            if hours_left <= 1:
                block = min(possible_blocks)          # end of day → short session
            elif task["remaining"] <= 1:
                block = min(possible_blocks)          # finishing a task → short session
            elif hours_left >= 4:
                block = 1.5                           # early day → deep focus
            else:
                block = 1 if 1 in possible_blocks else min(possible_blocks)


            start = current_time
            end = start + timedelta(hours=block)

            schedule.append({
                "task": task["name"],
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "hours": block
            })

            task["remaining"] -= block
            hours_left -= block

            # realistic break
            current_time = end + timedelta(minutes=15 if block >= 1 else 10)

            if hours_left <= 0:
                break

    return schedule
# ---------------- Routes ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    schedule = []
    missed = False

    # get or create user
    user = User.query.first()
    if not user:
        user = User(streak=0)
        db.session.add(user)
        db.session.commit()

    if request.method == "POST":
        # clear old tasks
        Task.query.delete()
        db.session.commit()

        names = request.form.getlist("task[]")
        difficulties = request.form.getlist("difficulty[]")
        hours = request.form.getlist("hours[]")
        deadlines = request.form.getlist("deadline[]")
        daily_hours = float(request.form.get("daily_hours", 8))

        tasks = []
        for i in range(len(names)):
            t = {
                "name": names[i],
                "difficulty": int(difficulties[i]),
                "hours": float(hours[i]),
                "deadline": datetime.strptime(deadlines[i], "%Y-%m-%d").date()
            }
            tasks.append(t)
            db.session.add(Task(
                name=t["name"],
                difficulty=t["difficulty"],
                estimated_time=t["hours"],
                deadline=t["deadline"]
            ))
        db.session.commit()

        schedule = generate_schedule(tasks, daily_hours)

        # check if missed yesterday
        yesterday = date.today() - timedelta(days=1)
        if not StudySession.query.filter_by(date=yesterday).first():
            missed = True

    # today's sessions
    today_sessions = StudySession.query.filter_by(date=date.today()).all()
    efficiency = compute_efficiency(today_sessions, schedule)
    weak_subjects = get_weak_subjects()
    total_planned_hours = sum(s['hours'] for s in schedule)
    overload = max(total_planned_hours - float(request.form.get("daily_hours", 8)), 0)
    feedback = generate_feedback(efficiency, weak_subjects, overload)

    return render_template("index.html",
        schedule=schedule,
        streak=user.streak,
        efficiency=efficiency,
        weak_subjects=weak_subjects[:3],
        feedback=feedback,
        missed=missed
    )


@app.route("/complete", methods=["POST"])
def complete():
    for t in request.form.getlist("completed_tasks"):
        db.session.add(StudySession(task_name=t, hours_spent=1, date=date.today()))
    user = User.query.first()
    update_streak(user)
    db.session.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
