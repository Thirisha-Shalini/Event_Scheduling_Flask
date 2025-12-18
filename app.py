from flask import Flask, render_template, request, redirect, flash
from datetime import datetime
from config import Config
from models import db, Event, Resource, EventResourceAllocation
from sqlalchemy import text
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/events')

# ---------------- EVENTS ----------------
@app.route('/events')
def events():
    return render_template('events.html', events=Event.query.all())

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('desc')  # ✅ SAFE
        start_raw = request.form.get('start')
        end_raw = request.form.get('end')

        if not title or not start_raw or not end_raw:
            flash("All required fields must be filled")
            return redirect('/add_event')

        start = datetime.fromisoformat(start_raw)
        end = datetime.fromisoformat(end_raw)

        if start >= end:
            flash("End time must be after start time")
            return redirect('/add_event')

        event = Event(
            title=title,
            description=desc,
            start_time=start,
            end_time=end
        )

        db.session.add(event)
        db.session.commit()
        flash("Event created successfully")
        return redirect('/events')

    return render_template('add_event.html')

# ---------------- RESOURCES ----------------
@app.route('/resources')
def resources():
    return render_template('resources.html', resources=Resource.query.all())

@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'POST':
        name = request.form.get('name')
        rtype = request.form.get('type')

        if not name or not rtype:
            flash("All fields are required")
            return redirect('/add_resource')

        resource = Resource(
            resource_name=name,
            resource_type=rtype
        )
        db.session.add(resource)
        db.session.commit()
        flash("Resource added successfully")
        return redirect('/resources')

    return render_template('add_resource.html')

# ---------------- CONFLICT CHECK ----------------
def check_conflict(resource_id, start, end):
    allocations = (
        db.session.query(Event)
        .join(EventResourceAllocation)
        .filter(EventResourceAllocation.resource_id == resource_id)
        .all()
    )

    for e in allocations:
        if start < e.end_time and end > e.start_time:
            return True
    return False

# ---------------- ALLOCATION ----------------
@app.route('/allocate', methods=['GET', 'POST'])
def allocate():
    if request.method == 'POST':
        event_id = request.form.get('event')
        resource_id = request.form.get('resource')

        event = Event.query.get(event_id)

        if check_conflict(resource_id, event.start_time, event.end_time):
            flash("❌ Resource conflict detected")
            return redirect('/conflicts')

        allocation = EventResourceAllocation(
            event_id=event.event_id,
            resource_id=resource_id
        )
        db.session.add(allocation)
        db.session.commit()
        flash("✅ Resource allocated successfully")
        return redirect('/events')

    return render_template(
        'allocate.html',
        events=Event.query.all(),
        resources=Resource.query.all()
    )

# ---------------- CONFLICT PAGE ----------------
@app.route('/conflicts')
def conflicts():
    return render_template('conflicts.html')

# ---------------- REPORT ----------------
@app.route('/report', methods=['GET', 'POST'])
def report():
    data = []

    if request.method == 'POST':
        start = request.form.get('start')
        end = request.form.get('end')

        sql = text("""
            SELECT r.resource_name,
                   SUM(TIMESTAMPDIFF(HOUR, e.start_time, e.end_time)) AS hours
            FROM resource r
            JOIN event_resource_allocation a ON r.resource_id = a.resource_id
            JOIN event e ON e.event_id = a.event_id
            WHERE e.start_time BETWEEN :start AND :end
            GROUP BY r.resource_id
        """)

        result = db.session.execute(sql, {
            "start": start,
            "end": end
        })

        data = result.fetchall()

    return render_template('report.html', data=data)


# ---------------- RUN ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
