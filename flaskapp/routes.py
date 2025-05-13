from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day
from flaskapp.forms import PostForm
import datetime  
from flaskapp.models import UkData
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import io
import base64
from sqlalchemy import func 
import plotly
import plotly.express as px


# Route for the home page, which is where the blog posts will be shown 
@app.route("/")
@app.route("/home")
def home():
    # Querying all blog posts from the database
    posts = BlogPost.query.all()
    return render_template('home.html', posts=posts)


# Route for the about page
@app.route("/about")
def about():
    return render_template('about.html', title='About page')


# Route to where users add posts (needs to accept get and post requests)
@app.route("/post/new", methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = BlogPost(title=form.title.data, content=form.content.data, user_id=1)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)


# Route to the dashboard page
@app.route('/dashboard')
def dashboard():
    days = Day.query.all()
    df = pd.DataFrame([{'Date': day.id, 'Page views': day.views} for day in days])

    fig = px.bar(df, x='Date', y='Page views')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('dashboard.html', title='Page views per day', graphJSON=graphJSON) 


@app.route('/uk_analysis')
def uk_analysis():
    # Data for Visualization 1: Regional Party Support
    regional_data = db.session.query(
        UkData.region,
        func.avg(UkData.ConVote19 / UkData.TotalVote19 * 100).label('avg_con_share'),
        func.avg(UkData.LabVote19 / UkData.TotalVote19 * 100).label('avg_lab_share'),
        func.avg(UkData.LDVote19 / UkData.TotalVote19 * 100).label('avg_ld_share')
    ).group_by(UkData.region).all()
    
    regions = [r[0] for r in regional_data]
    con_shares = [float(r[1]) if r[1] is not None else 0 for r in regional_data]
    lab_shares = [float(r[2]) if r[2] is not None else 0 for r in regional_data]
    ld_shares = [float(r[3]) if r[3] is not None else 0 for r in regional_data]
    
    # Data for Visualization 2: Demographic Correlation
    # Get all constituencies with both home ownership and Con vote data
    scatter_data = db.session.query(
        UkData.constituency_name,
        UkData.c11HouseOwned, 
        (UkData.ConVote19 / UkData.TotalVote19 * 100).label('con_vote_share')
    ).filter(
        UkData.c11HouseOwned.isnot(None),
        UkData.ConVote19.isnot(None),
        UkData.TotalVote19.isnot(None)
    ).all()
    
    house_owned = [float(d[1]) for d in scatter_data]
    con_vote_share = [float(d[2]) for d in scatter_data]
    constituency_names = [d[0] for d in scatter_data]
    
    # Pass data to template
    return render_template(
        'uk_analysis.html',
        regions=json.dumps(regions),
        con_shares=json.dumps(con_shares),
        lab_shares=json.dumps(lab_shares),
        ld_shares=json.dumps(ld_shares),
        house_owned=json.dumps(house_owned),
        con_vote_share=json.dumps(con_vote_share),
        constituency_names=json.dumps(constituency_names)
    )


@app.before_request
def before_request_func():
    day_id = datetime.date.today()  # get our day_id
    client_ip = request.remote_addr  # get the ip address of where the client request came from

    query = Day.query.filter_by(id=day_id)  # try to get the row associated to the current day
    if query.count() > 0:
        # the current day is already in table, simply increment its views
        current_day = query.first()
        current_day.views += 1
    else:
        # the current day does not exist, it's the first view for the day.
        current_day = Day(id=day_id, views=1)
        db.session.add(current_day)  # insert a new day into the day table

    query = IpView.query.filter_by(ip=client_ip, date_id=day_id)
    if query.count() == 0:  # check if it's the first time a viewer from this ip address is viewing the website
        ip_view = IpView(ip=client_ip, date_id=day_id)
        db.session.add(ip_view)  # insert into the ip_view table
    db.session.commit()  # commit all the changes to the database
