#all imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort,\
     render_template, flash
from datetime import datetime
import time

timeFMT = '%H:%M:%S';
user_id = "1";

app = Flask(__name__) #create the application instance
app.config.from_object(__name__) #load config from this file, flaskr.py

#load default config and override config from an environment variable
app.config.update(dict(
  DATABASE=os.path.join(app.root_path, 'flaskr.db'),
  SECRET_KEY = 'development key',
  USERNAME = 'admin',
  PASSWORD = 'default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
  """Connects to the specific database."""
  rv = sqlite3.connect(app.config['DATABASE'])
  rv.row_factory = sqlite3.Row
  return rv

def init_db():
  db = get_db()
  with app.open_resource('schema.sql', mode='r') as f:
    db.cursor().executescript(f.read())
  
  query = "INSERT INTO rooms(id, cost_per_hr, included_facilities) VALUES(1, 5, 'tv'), (2, 3, 'whiteboard');"

  query1 = "INSERT INTO teams(id, name, total_cost_accrued, deleted)"
  query1 += "VALUES (1, 'marketing', 10, 0),"
  query1 += "(2, 'software', 6, 0),"
  query1 += "(3, 'summer', 0, 0);" 

  query2 = "INSERT INTO company_people(id, team_id, name, position)"
  query2 += "VALUES(1,1,'John Smith', 'market researcher'),"
  query2 += "(2, 2, 'Jane Dough', 'developer'),"
  query2 += "(3, 3, 'Franny Miller', 'intern');";

  query5 = "DELETE FROM company_people WHERE company_people.id = 3;"
  query6 = "UPDATE teams SET deleted = 1 WHERE id = 3;"

  query3 = "INSERT INTO business_partners(id, name, position, company)"
  query3 += "VALUES(1,'Jeff Phillip', 'head of marketing', 'Walgreens'),"
  query3 += "(2, 'Samantha Waters', 'analyst', 'Morgan Stanly'),"
  query3 += "(3, 'None', 'None', 'None');"
 
  query4 = "INSERT INTO meetings(meeting_id, person_id, team_id, bus_partner_id, room_num, start_time, end_time, meeting_date)"
  query4 += "VALUES (1, 1, 1, 1,1,'13:00:00', '15:00:00', '2018-04-01'),"
  query4 += "(2,2,2,2,2, '10:00:00', '12:00:00', '2018-04-02');"
  
  db.execute(query)
  db.execute(query1)
  db.execute(query2)
  db.execute(query3)
  db.execute(query4)
  db.execute(query5)
  db.execute(query6)

  db.commit()


@app.cli.command('initdb')
def initdb_command():
  """Initializes the database."""
  init_db()
  print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet 
    for the current application context."""
    if not hasattr(g, 'sqlite_db'):
      g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
  """Closes the database again at the end of the request."""
  if hasattr(g, 'sqlite_db'):
    g.sqlite_db.close()


@app.route('/show', methods=['GET', 'POST'])
def show_rooms():
  db = get_db()

  query = 'select rooms.id, rooms.cost_per_hr, rooms.included_facilities, meetings.meeting_date, meetings.start_time, meetings.end_time, teams.name, company_people.name, meetings.meeting_id,  company_people.position from rooms join meetings on meetings.room_num = rooms.id join teams on meetings.team_id = teams.id join company_people on company_people.id = meetings.person_id order by meetings.meeting_id;'; 
  query1 = 'select meetings.meeting_id, teams.name from meetings, company_people join teams on teams.id = company_people.team_id order by meetings.meeting_id;';
  cur = db.execute(query)
  cur1 = db.execute(query1);
  entries = cur.fetchall()
  entries1 = cur1.fetchall();

  retVal = [];
  for i in range(len(entries)):
    retVal.append("MEETING:")
    retVal.append('\n');
    retVal.append("Room Number: " + str(entries[i][0]));
    retVal.append('\n');
    retVal.append("Cost of Room Per Hour: " + str(entries[i][1]));
    retVal.append('\n');
    retVal.append("Included Facilities: " + str(entries[i][2]));
    retVal.append('\n');
    retVal.append("Meeting Date: " + str(entries[i][3]));
    retVal.append('\n')
    retVal.append("Time slot: " + str(entries[i][4]) + " - " + str(entries[i][5]));
    retVal.append('\n');
    retVal.append(str(entries[i][7]) + " (Team: " + str(entries1[i][1]) + " , "+ str(entries[i][9]) + ") has a meeting with team " + str(entries[i][6]));
    retVal.append('\n');
    retVal.append('-----------------------------------------------------------------------------------')

  return render_template('show.html', entries=retVal)

@app.route('/addMeeting', methods = ['GET', 'POST'])
def addMeetingPage():
  companies = [];
  rooms = [];
  bus_people = [];
  teams = []
  db = get_db();
  query = "SELECT name, company, position FROM business_partners;"
  query1 = "SELECT id, included_facilities, cost_per_hr FROM rooms;"

  query2 = "SELECT name FROM teams WHERE deleted = 0;"

  cur = db.execute(query);
  cur1 = db.execute(query1);
  cur2 = db.execute(query2);
  line = cur.fetchall();
  line1 = cur1.fetchall();
  line2 = cur2.fetchall();
  for i in range(len(line)):
    insertThis = str(line[i][0]) + ", " + str(line[i][1] + ", " + str(line[i][2]));
    companies.append(insertThis);
  
  for i in range(len(line1)):
    rooms.append(str(line1[i][0]) + ", " + str(line1[i][1]) + ", " + str(line1[i][2]));
  
  for i in range(len(line2)):
    teams.append(str(line2[i][0]));

  if request.method == 'POST':
    query = "SELECT id from teams where teams.name = '" + request.form['teams']+"';";
    cur = db.execute(query);
    line = cur.fetchall();
    dateSelected = request.form['year'] + "-" + request.form['month'] + "-" + request.form['day'];
    dateTime = dateSelected + " " + request.form['start_time'];
    query1 = "SELECT strftime('%s', 'now') - strftime('%s','" + dateTime + "');" 

    cur1 = db.execute(query1);
    line1 = cur1.fetchall();
   

    if int(str(line1[0][0])) > 0: 
      return render_template('results.html', message = "Date or time has already passed.");
    
    endDateTime = dateSelected + " " + request.form['end_time'];
    query2 = "SELECT strftime('%s','" + endDateTime + "') - strftime('%s','" + dateTime + "');" 
    cur2 = db.execute(query2);
    line2 = cur2.fetchall();

    if int(str(line2[0][0])) <= 0:
      return render_template('results.html', message = "The time you have selected is invalid.");

    return redirect(url_for('resultsOfAddMeeting', companies = request.form['companies'], room = request.form['rooms'], team_id = line[0][0],team_name = request.form['teams'], year = request.form['year'], month = request.form['month'], day = request.form['day'], start_time = request.form['start_time'], end_time = request.form['end_time']));
  return render_template('addMeeting.html', companies = companies, message = "", rooms = rooms, teams=teams);



@app.route('/resultOfAddMeeting/<companies>/<room>/<team_id>/<team_name>/<year>/<month>/<day>/<start_time>/<end_time>', methods=['GET','POST'])
def resultsOfAddMeeting(companies, room, team_id, team_name, year, month, day, start_time, end_time):
  message = "";
  delta_time = datetime.strptime(end_time, timeFMT) - datetime.strptime(start_time, timeFMT)
	
  if delta_time == '00:00:00':
    return render_template('results.html', message = "Please enter a valid time interval")
  
  if (delta_time.total_seconds()/3600.0) < 0:
    return render_template('results.html', message = "Please make sure your start time is earlier than your end time.");

  db = get_db();
  date = year + "-" + month +"-" + day;

  stuff2 = room.split(', ');
  room = stuff2[0]

  query = "SELECT * FROM meetings WHERE room_num = " + room + " and meeting_date  = '" + date + "' and ((start_time >= '" + start_time + "' and start_time < '" + end_time + "') OR (end_time > '" + start_time + "' and end_time <= '" + end_time + "'));";
  cur = db.execute(query);
  line = cur.fetchall();
  if len(line) != 0:
    message = "Meeting room is unavilable to book on " + date + " from " + start_time + " to " + end_time + ".";
    return render_template('results.html', message = message);
	#NO CONFLICTING MEETING at that time and date
  
  if companies == "None, None, None":
		#NO business partner
		#Insert a meeting with these values
    query = "INSERT INTO meetings(person_id, team_id, bus_partner_id, room_num, start_time, end_time, meeting_date) VALUES (1, "+ team_id +", 0, ";
    query += room + ", '" + start_time + "', '" + end_time + "', '" + date + "');"
  else:
    stuff = companies.split(', ');
    bus_partner = stuff[0];
    company = stuff[1];
    
    query = "SELECT id FROM business_partners WHERE name = '" + bus_partner + "' and company = '" + company + "';"
    cur = db.execute(query);
    line = cur.fetchall();
    
    if len(line) == 0:
			#Else just return not possible and do NOT add meeting
      message = "Invalid business partner.  No meeting was booked please try again.";
      return render_template('results.html', message = message);
		#Valid busines partner.  Add meetings
    
    query = "INSERT INTO meetings(person_id, team_id, bus_partner_id, room_num, start_time, end_time, meeting_date) VALUES (1, " + team_id + ", ";
    query += str(line[0][0]) + ", " + room + ", '" + start_time + "', '" + end_time + "', '" + date + "');";
    
  cur = db.execute(query);

	#FIND cost of room and adjust cost in teams 
  query = "SELECT cost_per_hr FROM rooms WHERE id = " + room + ";";
  cur = db.execute(query);
  line = cur.fetchall();

  if len(line) == 0:
    message = "Issue with room."
    return render_template('results.html', message = message);

  room_cost = str(line[0][0]);
  
  if len(line) == 0:
    message = "Error with finding room cost."
    return render_template('results.html', message = message);


  query = "SELECT team_id FROM company_people WHERE id = " + user_id + ";";
  cur = db.execute(query);
  line1 = cur.fetchall();
  if len(line1) == 0:
    message = "Issue with team_id with the user_id."
    return render_template('results.html', message = message);
  user_team_id = str(line1[0][0]);

	#Find totalCostsAccrued so far for the team that has the corresponding team name
  query = "SELECT total_cost_accrued FROM teams WHERE id = '" + user_team_id + "';";
  cur = db.execute(query);
  historical_costs = cur.fetchall();
  if len(historical_costs) == 0:
    message = "No team with that name."
    return render_template('results.html', message=message);
  
	#Found room cost.  Update the team's cost accrued
  # delta_time = int(time.mktime(delta_time.timetuple()))
  query = "UPDATE teams SET total_cost_accrued = " + str(historical_costs[0][0] + (delta_time.total_seconds()/3600.0)* int(str(line[0][0])))  + " WHERE id = '" + user_team_id + "';"; 
  db.execute(query);
  
  db.commit();
	# message = "Successfully added meeting.";
	# return render_template('addMeeting.html', message = message);
  message = "You just booked a meeting in room number " + room + " on " + month + "/" + day + "/" + year + " from " + start_time + " to " + end_time + " with the team called " + team_name ;
  if companies != "None, None":
    message += " and " + companies;
  message += ".";
  
  return render_template('results.html', message=message)


@app.route('/deleteMeeting', methods = ['GET', 'POST'])
def deleteMeetingPage():
  db = get_db()
  #ONLY DISPLAY MEETINGS IN THE DROP DOWN IF THEY BELONG TO US AND HAVEN'T HAPPENED YET

  query = "select rooms.id, rooms.cost_per_hr, rooms.included_facilities, meetings.meeting_date, meetings.start_time, meetings.end_time, teams.name, company_people.name, meetings.meeting_id from rooms join meetings on meetings.room_num = rooms.id join teams on meetings.team_id = teams.id join company_people on company_people.id = meetings.person_id "
  query += "WHERE company_people.id = " + user_id + " AND meetings.meeting_date between date('now') AND '2030-12-31' AND strftime('%s','now') - strftime('%s',meetings.start_time) >= 0 order by meetings.meeting_id;"; 
  query1 = 'select meetings.meeting_id, teams.name from meetings, company_people join teams on teams.id = company_people.team_id order by meetings.meeting_id;';
  cur = db.execute(query)
  cur1 = db.execute(query1);
  entries = cur.fetchall()
  if len(entries) == 0:
    message = "Time check went weird."
    return render_template('results.html', message = query)
  entries1 = cur1.fetchall();

  retVal = [];
  for i in range(len(entries)):
    cur = ""
    cur += ("Room: " + str(entries[i][0]));
    cur += '\n';
    cur += ("Cost Per Hour: " + str(entries[i][1]) + " ");
    cur += ("Meeting Date: " + str(entries[i][3]));
    cur += (" Time slot: " + str(entries[i][4]) + " - " + str(entries[i][5]));
    cur += '\n';
    cur += " with team " + str(entries[i][6]);
    cur += '\n';
    retVal.append(cur);

  if request.method == 'POST':
    index = request.form['allMeetings'];
    index = int(index);
    room_num = (str(entries[index][0]));
    meeting_date = (str(entries[index][3]));
    meeting_date = meeting_date.replace('/','.');
    start_time = str(entries[index][4]);
    end_time = str(entries[index][5]);

    return redirect(url_for('resultsOfDeleteMeeting', roomNum = room_num, date = meeting_date, startTime = start_time, endTime = end_time));
  return render_template('deleteMeeting.html', message = "", allMeetings = retVal);


@app.route('/resultsOfDeleteMeeting/<roomNum>/<date>/<startTime>/<endTime>', methods = ['GET', 'POST'])
def resultsOfDeleteMeeting(roomNum, date, startTime, endTime):
  message = "";
  db = get_db();
  date = date.replace('.','/');
  delta_time = datetime.strptime(endTime, timeFMT) - datetime.strptime(startTime, timeFMT)

  #We want to make sure that the meeting exists and that the person_id == user_id
  query = "SELECT meeting_id FROM meetings WHERE start_time = '" + startTime + "' AND end_time = '" + endTime + "' AND meeting_date = '" + date + "' AND room_num = " + roomNum + " AND person_id =" + user_id + ";";
  cur = db.execute(query);
  line = cur.fetchall();
  meeting_id = str(line[0][0])
  if len(line) == 0:
    message = "No such meeting";
    #Is there a way to see which is not a real meeting and which fields need to be changed?
    return render_template('results.html', message=message);
  
  meetingID = str(line[0][0]);
  
  query = "SELECT cost_per_hr FROM rooms WHERE id= " + roomNum + ";";
  cur = db.execute(query);
  line = cur.fetchall();
  if len(line) == 0:
    message = "Not a valid room number";
    return render_template('results.html', message = message);
	
  roomCost = int(str(line[0][0]));
  query = "SELECT team_id FROM company_people WHERE id = " + user_id + ";";
  cur = db.execute(query);
  line = cur.fetchall();
  if len(line) == 0:
    message = "No such team_id for the given user_id."
    return render_template('results.html', message = message);
  user_team_id = str(line[0][0]);
  query = "SELECT total_cost_accrued FROM teams WHERE id = " + user_team_id + ";";
  cur = db.execute(query);
  line = cur.fetchall();
  if len(line) == 0:
    message = "Issue with finding the total costs accrued for the given team."
    return render_template('results.html', message = message);
  historical_costs = str(line[0][0]);
  # return render_template('results.html', message=str(roomCost))
  #UPDATE THE TOTALCOSTSACCRUED - This updates the totalCostsAccrued for a team if the meeting is deleted.  There is no other way to get back what the total costs accrued were after this query.
  query = "UPDATE teams SET total_cost_accrued = " + str(int(historical_costs) - (delta_time.total_seconds()/3600.0) * roomCost) + " WHERE id = " + user_team_id + ";";
  db.execute(query);

  query = "DELETE FROM meetings WHERE meeting_id = " + meeting_id + ";"
  db.execute(query);
  db.commit();
  message = "Successfully deleted the meeting on " + date + " going from " + startTime + " to " + endTime + " in room " + roomNum + ".";
  return render_template('results.html', message = message);


@app.route('/cost', methods=['GET', 'POST'])
def cost_page():
  db = get_db();
	#select time frame?
	#include deleted teams?
	#the costs accrued are updated when a meeting is BOTH added and deleted.  We do NOT need to keep track of the costs accrued from deleted meetings.
  query = "SELECT name FROM teams;"
  cur = db.execute(query);
  line = cur.fetchall()
  
  teams = [];
  for i in range(len(line)):
    teams.append(line[i][0])
    
  if request.method == 'POST':
    query = "SELECT id FROM teams WHERE name = '" + request.form['teams'] + "';";
    cur = db.execute(query);
    line = cur.fetchall();

    return redirect(url_for('cost', team_name = request.form['teams'], team_id = str(line[0][0]), year = request.form['year'], month = request.form['month'], day = request.form['day'], toyear = request.form['toyear'], tomonth = request.form['tomonth'], today = request.form['today']));
  return render_template('cost.html', teams = teams);

@app.route('/cost/<team_name>/<team_id>/<year>/<month>/<day>/<toyear>/<tomonth>/<today>', methods = ['GET', 'POST'])
def cost(team_name, team_id, year, month, day, toyear, tomonth, today):
  message = "";
  db = get_db();
  startDate = year + "-" + month + "-" + day;
  endDate = toyear + "-" + tomonth + "-" + today;

  query1 = "SELECT rooms.cost_per_hr, meetings.start_time, meetings.end_time FROM meetings join teams on teams.id = meetings.team_id join rooms on rooms.id = meetings.room_num WHERE teams.id = "+ team_id + " AND meetings.meeting_date >= '" + startDate + "' AND meetings.meeting_date <= '" + endDate + "';";
  cur1 = db.execute(query1);
  line1 = cur1.fetchall();
  if len(line1) == 0:
    return render_template('results.html', message = "No meetings for " + team_name +  " team from " + startDate + " to " + endDate + ".");

  total = 0;
  for i in range(len(line1)):
    delta_time = datetime.strptime(str(line1[i][2]), timeFMT) - datetime.strptime(str(line1[i][1]), timeFMT);
    delta_time = delta_time.total_seconds()/3600.0
    total += delta_time * int(str(line1[i][0]));


  # query = "SELECT total_cost_accrued FROM teams WHERE id = " + team_id + ";";
  # cur = db.execute(query);
  # line = cur.fetchall();
  message = "The total costs accrued for team " + team_name + " from " + startDate + " to " + endDate + " is " + str(total);
  return render_template('results.html', message = message);


@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
      error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
      error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You were logged in')
      return redirect(url_for('show_rooms'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('show_rooms'))


with app.app_context():
      init_db()