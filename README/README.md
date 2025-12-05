# CS 2500 – Final Project
## Cale Ellingson, Kalei Foley-Rutherfurd

### Project Overview
This is a lost and found website to report lost (or found) items that will be stored 
in a database. It works through a website interface that uses input boxes that fill 
in the data.

### Database Description
The database is made up of 4 tables: FoundPosts, LostPosts, Matches, and Users.
It follows this schema:

FoundPosts(**found_id**, _user_id_, item_name, category, description, date_found, found_location, storage_location, date_posted, status)

LostPosts(**lost_id**, _user_id_, item_name, category, description, date_lost, last_seen_location, date_posted, status)

Matches(**match_id**, _lost_id_, _found_id_, matched_by_user_id, date_matched, resolved, notes)

Users(**user_id**, name, email, phone, role, date_joined)

The ER-Diagram can be seen below:
![er-diagram.png](er-diagram.png)


### Code Description

Download required libraries via terminal

    pip install -r requirements.txt

Run the program via terminal 
    
    fastapi dev main.py




