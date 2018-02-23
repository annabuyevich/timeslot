#all imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort,\
     render_template, flash
from datetime import datetime
import time

timeFMT = '%H:%M:%S';


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
  
  query = "INSERT INTO rooms(id, cost_per_hr, included_facilities) VALUES(1, 5, 'tv');"
  db.execute(query)
  # query2 = "INSERT INTO business_partners(id, name,position, company) VALUES(1, '', '','');"
  # db.execute(query2)
  db.commit()


@app.cli.command('initdb')
def initdb_command():
  """Initializes the database."""
  init_db()
  # db = get_db()
  # query = "INSERT INTO rooms(cost_per_hr, included_facilities) VALUES(5, 'tv');"

  # db.commit();
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

# TODO: change to our database here
@app.route('/show')
def show():
  return render_template('show.html')

@app.route('/show', methods=['GET', 'POST'])
def show_rooms():
  db = get_db()
  text = request.form['text']
  # print(text, file=sys.stderr)
  query = 'select rooms.id as room_num, rooms.cost_per_hr, rooms.included_facilities, meetings.meeting_date from rooms join meetings on meetings.room_num = rooms.id where meetings.meeting_date=' + text
  cur = db.execute(query)
  entries = cur.fetchall()
  return render_template('show.html', entries=entries)

@app.route('/addMeeting')
def addMeeting_page():
	return render_template('addMeeting.html');

@app.route('/addMeeting', methods=['GET', 'POST'])
def addMeeting():
	message = ""
	# name = request.form['name'];
	room = request.form['room_num'];
	team_name = request.form['team'];
	team_name = team_name.upper();
	#WHERE TO USE THIS?



	start_time = request.form['start_time'];
  
	end_time = request.form['end_time'];
	date = request.form['date'];

	bus_partner = request.form['bus_partner'];
	bus_partner = bus_partner.upper();
	company = request.form['company'];
	company = company.upper();
  # return render_template('addMeeting.html', message = "test1");

	# if room == "" or name == "" or team_name == "" or start_time == "" or end_time == "" or date == "":
	# return render_template('addMeeting.html', message = "Did not add meeting.  Please make sure to enter all valid fields");
  
  
	delta_time = datetime.strptime(end_time, timeFMT) - datetime.strptime(start_time, timeFMT)
	if delta_time == '0:0:0':
		return render_template('addMeeting.html', message = "Please enter a valid time interval")


	db = get_db();


	#Check room availability #TODO: meetings doesn't have a room ( what is constart and conEnd)
	query = 'SELECT * FROM meetings WHERE room_num =' + room + ' and meeting_date  = "' + date + '" and start_time between "' + start_time + '" and "' + end_time + '";';
	cur = db.execute(query);
	line = cur.fetchall();

	if len(line) != 0:
		message = "Meeting room is unavilable to book on " + date + " from " + start_time + " to " + end_time + ".";
		return render_template('addMeeting.html', message = message);
	#NO CONFLICTING MEETING at that time and date

	if bus_partner != "" and company != "":
		#have a business partner
		#Check if valid business partner
		query = "SELECT id FROM business_partners WHERE name = '" + bus_partner + "' and company = '" + company + "';"
		cur = db.execute(query);
		line = cur.fetchall();
		if len(line) == 0:
			#Else just return not possible and do NOT add meeting
			message = "Invalid business partner.  No meeting was booked please try again.";
			return render_template('addMeeting.html', message = message);
		#Valid busines partner.  Add meetings

		query = "INSERT INTO meetings(person_id, team_id, bus_partner_id, room_num, start_time, end_time, meeting_date) VALUES (1, 1,";
		query += str(line[0][0]) + ", " + room + ", '" + start_time + "', '" + end_time + "', '" + date + "');"
    
	else:
		#NO business partner
		#Insert a meeting with these values
		query = "INSERT INTO meetings(person_id, team_id, bus_partner_id, room_num, start_time, end_time, meeting_date) VALUES (1, 1, 0, ";
		query += room + ", '" + start_time + "', '" + end_time + "', '" + date + "');"

	cur = db.execute(query);
	# line = cur.fetchall();
	# if len(line) == 0:
	# 	message = "Failure somewhere with the commands.  Fails when trying to insert."
	# 	return render_template('addMeeting.html', message = delta_time.total_seconds());


	#FIND cost of room and adjust cost in teams 
	query = "SELECT cost_per_hr FROM rooms WHERE id = " + room + ";";
	cur = db.execute(query);
	line = cur.fetchall();
	if len(line) == 0:
		message = "Error with finding room cost."
		return render_template('addMeeting.html', message = message);


	#Find totalCostsAccrued so far for the team that has the corresponding team name
	query = "SELECT total_cost_accrued FROM teams WHERE name = '" + team_name + "';";
	cur = db.execute(query);
	historical_costs = cur.fetchall();
	if len(historical_costs) == 0:
		message = "No team with that name."
		return render_template('addMeeting.html', message=message);
  
	#Found room cost.  Update the team's cost accrued
  # delta_time = int(time.mktime(delta_time.timetuple()))
	query = "UPDATE teams SET total_cost_accrued = " + str(historical_costs[0][0] + (delta_time.total_seconds()/3600.0)* int(str(line[0][0])))  + " WHERE name = '" + team_name + "';"; 
	db.execute(query);



	db.commit();
	message = "Successfully added meeting.";
	return render_template('addMeeting.html', message = message);






@app.route('/add')
def add_page():
  return render_template('add.html');

@app.route('/add', methods=['GET', 'POST'])
def add_team():
  db = get_db();
  text = request.form['text'];
  query = 'INSERT INTO teams (name, total_cost_accrued) VALUES ("';
  query += text.upper();
  query += '", 0.0);';
  cur = db.execute(query);
  db.commit()
  return render_template('add.html', message = 'Successfully added a team named ' + text);


@app.route('/addPerson')
def addPerson_page():
  return render_template('addPerson.html');

@app.route('/addPerson', methods=['GET', 'POST'])
def add_person():
  db = get_db();
  name = request.form['name'];
  position = request.form['position'];
  team = request.form['team'];
  company = request.form['company'];
  if team != '':
    # corporate
    #execute query to get team id
    query1 = 'SELECT id as num FROM teams where name = "' 
    query1 += team.upper() + '";'
    cur = db.execute(query1);
    line = cur.fetchall();
    message = "";
    if len(line) == 0:
      #insert this new team
      query = 'INSERT INTO teams (name, total_cost_accrued) VALUES ("';
      query += team.upper();
      query += '", 0.0);';
      cur = db.execute(query);
      message += "Created a new team called " + team.upper() + ".  ";
      query1 = 'SELECT id as num FROM teams where name = "' 
      query1 += team.upper() + '";'
      cur = db.execute(query1);
      line = cur.fetchall();

    query = 'INSERT INTO company_people(team_id, name, position) VALUES (';
    query += str(line[0][0]) + ', "'
    query += name.upper() + '", "';
    query += position + '");';
    # return render_template('addPerson.html', message=query)

    db.execute(query);
    db.commit();
    message += 'Successfully added ' + name.upper() + ' to the corporate members entity';
  if company != '':
    #business partner
    query = 'INSERT INTO business_partners(name, position, company) VALUES ("';
    query += name + '", "';
    query += position + '", "';
    query += company.upper() + '");';
    cur = db.execute(query);
    db.commit()
    message = 'Successfully added ' + name + ' to the business partners entity';
  return render_template("addPerson.html", message = message);


@app.route('/deletePerson')
def delete_person():
  return render_template('deletePerson.html');


#Deleting
@app.route('/deletePerson', methods=['GET','POST'] )
def delete():
  db = get_db();
  name = request.form['name']
  team = request.form['team']
  position = request.form['position']
  query1 = 'SELECT teams.id as team_id from teams WHERE teams.name="'
  query1 += team.upper() + '";';
  cur = db.execute(query1)
  line = cur.fetchall()
  if len(line) == 0:
    return render_template('deletePerson.html', message = "Invalid team name.")
  query = 'DELETE from company_people WHERE name = "' + name +'" AND team_id='+ str(line[0][0]) + ' AND position="' + position +'";';  
  cur = db.cursor()
  cur.execute(query)

  # line = cur.fetchall()
  # if len(line) == 0:
  #   return render_template('deletePerson.html', message = "Cannot delete.")
  message = 'You have just deleted ' + name.upper() + ' who belonged to ' + team.upper() + ' team';  
  db.commit()
  return render_template('deletePerson.html', message = message)

@app.route('/deleteTeam')
def deleteTeam_page():
	return render_template('deleteTeam.html');

@app.route('/deleteTeam', methods=['GET', 'POST'])
def deleteTeam():
	db = get_db();
	team = request.form['team'];
	team = team.upper();
	#Check if team exists
	#If not, do not delete
	#If exists, delete ALL team members and delete the team

	query = 'SELECT id FROM teams WHERE name = "' + team + '";';
	cur = db.execute(query);
	line = cur.fetchall();

	if len(line) == 0:
		message = "No team with that name."
		return render_template('deleteTeam.html', message=message);


	query = "DELETE FROM company_people WHERE team_id = " + str(line[0][0]) + ";";
	cur = db.execute(query);

	query = "DELETE FROM teams WHERE id = " + str(line[0][0]) + ";";
	cur = db.execute(query)
	# line = cur.fetchall();
	# if len(line) == 0;
	# 	message = "Some issue with deleting a team.";
	# 	return render_template('deleteTeam.html', message=message);
	db.commit();
	return render_template('deleteTeam.html', message=str("Successfully deleted " + team));












@app.route('/', methods=['GET', 'POST'])
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