drop table if exists rooms;
create table rooms (
  id integer primary key autoincrement,
  cost_per_hr decimal(8,2),
  included_facilities text not null
);



drop table if exists meetings;
create table meetings (
  meeting_id integer primary key autoincrement,
  person_id integer,
  team_id integer,
  bus_partner_id integer,
  room_num integer,
  start_time text,
  end_time text,
  meeting_date text
  -- FOREIGN KEY (person_id)
  --   REFERENCES company_people(id),
  -- FOREIGN KEY (team_id)
  --   REFERENCES Teams.team_id,
  -- FOREIGN KEY (bus_partner_id)
  --   REFERENCES business_partners(id),
  -- FOREIGN KEY (room_num)
  --   REFERENCES rooms(id)
);

drop table if exists teams;
create table teams (
  id integer primary key autoincrement,
  name text not null,
  total_cost_accrued decimal(8,2)
);


drop table if exists company_people;
create table company_people (
  id integer primary key autoincrement,
  team_id int,
  name text not null,
  position text not null
  -- FOREIGN KEY (team_id)
  --   REFERENCES teams(id)
);

drop table if exists business_partners;
create table business_partners (
  id integer primary key autoincrement,
  name text not null,
  position text not null,
  company text not null
);



-- drop table if exists entries;
-- create table entries (
--   id integer primary key autoincrement,
--   title text not null,
--   'text' text not null
-- );