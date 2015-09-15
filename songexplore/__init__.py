from flask import Flask, Response, jsonify, render_template, request, redirect, url_for
from wtforms import TextField, Form
from  sqlalchemy.sql.expression import func, select
import json
import time

from songexplore.database import db_session, Recs

LIMIT = 10 #change html description p if you change this
NUM_FIELDS = 5 #id, title, artist, cluster, new_cluster (fields from rec)
NUM_PARAMS = 3 #page, orderby, asc, fields beyond those from recs

app = Flask(__name__)

#cluster_inputs = []


class SearchForm(Form):
    autocomp= TextField('autocomp',id='autocomplete')


@app.route('/autocomplete')
def autocomplete():
    db_vals = []
    search = request.args.get('search[term]')
    #app.logger.debug(search)
    db_vals += db_session.query(Recs).filter(Recs.artist.ilike('%' + search + '%')).all()
    db_vals += db_session.query(Recs).filter(Recs.title.ilike('%' + search + '%')).all() 
    results = []
    for v in db_vals[:LIMIT]:
        results.append({"value": "%s, %s" %(v.artist, v.title), 
                        "id" : v.track_id,
                        "cluster" : v.cluster,
                        "cluster_new" : v.cluster_new})
    return Response(json.dumps(results))
    
def get_recs(cluster_inputs, page, sort, ascdesc):
    if len(cluster_inputs) < 1:
        app.logger.debug("No selected songs")
        results = [{"value": "No songs selected"}]
        return results
    else:
        lim = int(LIMIT/len(cluster_inputs))
    db_vals = []
    for c in cluster_inputs:
        c_old = c[0]
        c_new = c[1]
        init_len = len(db_vals)
        db_vals += db_session.query(Recs).filter(Recs.cluster==c_old,
                   Recs.cluster_new==c_new, Recs.recommend==1) \
                   .order_by(getattr(getattr(Recs, sort), ascdesc)()) \
                   .slice(page*lim, page*lim+lim)
        mid_len = len(db_vals)
        #if not enough double match recs:
        if (mid_len - init_len) < lim:
            new_lim = lim - (mid_len - init_len)
            db_vals += db_session.query(Recs).filter(Recs.cluster!=c_old,
                   Recs.cluster_new==c_new, Recs.recommend==1) \
                   .order_by(getattr(getattr(Recs, sort), ascdesc)()) \
                   .slice(page*new_lim, (page*new_lim+new_lim))
        #if not enough new_rec recs:
        if (len(db_vals) - init_len) < lim:
            new_lim = lim - (len(db_vals) - init_len)
            db_vals += db_session.query(Recs).filter(Recs.cluster==c_old,
                   Recs.cluster_new!=c_new, Recs.recommend==1) \
                   .order_by(getattr(getattr(Recs, sort), ascdesc)()) \
                   .slice(page*new_lim, (page*new_lim+new_lim))
        #if not enough of either, repeat recs, but with random:
        if (len(db_vals) - init_len) < lim:
            new_lim = lim - (len(db_vals) - init_len)
            db_vals += db_session.query(Recs).filter((Recs.cluster==c_old) |
                   (Recs.cluster_new==c_new), Recs.recommend==1) \
                   .order_by(func.random()).limit(new_lim)
    results = []
    for v in db_vals:
        results.append({"value": "%s, %s" %(v.artist, v.title), 
                        "id" : v.track_id,
                        "cluster" : v.cluster,
                        "cluster_new": v.cluster_new})
    return results
    
@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    form_vals = request.form
    app.logger.debug(form_vals)
    app.logger.debug(len(form_vals))
    page = int(form_vals.get("page"))
    sort = form_vals.get("orderby") 
    ascdesc = form_vals.get("asc")
    number_items = (len(form_vals)-NUM_PARAMS)/NUM_FIELDS 
    clusters = []
    for i in range(number_items):
        cluster_old = int(form_vals.get("items["+str(i)+"][cluster]"))
        cluster_new = int(form_vals.get("items["+str(i)+"][cluster_new]"))
        clusters.append((cluster_old, cluster_new))
    app.logger.debug(number_items)
    app.logger.debug(clusters)
    if len(clusters) > LIMIT:
        results = [{"value": "Too many songs selected!"}]
    else:
        results = get_recs(clusters, page, sort, ascdesc)
        app.logger.debug(results)
    return Response(json.dumps(results))
    
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/')
def index():
    form = SearchForm(request.form)
    return render_template('index.html', form=form)
 

#if __name__ == '__main__':
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host='0.0.0.0', port=port)
