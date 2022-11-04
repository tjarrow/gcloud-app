from google.cloud import datastore

from flask import Flask, render_template, request

from markupsafe import escape

import datetime

app = Flask(__name__)

datastore_client = datastore.Client()

@app.route('/')
def start():
    return render_template('index.html', output='Hello, please type any command')

@app.route('/set')
def set_var():
    name=request.args.get('name')
    value=request.args.get('value')
    
    var_key = datastore_client.key("variable", name)
    var_entity = datastore.Entity(key=var_key)

    last_action_key = datastore_client.key("last_action", name)
    last_action_entity = datastore.Entity(key=last_action_key)

    prev_action = datastore_client.get(last_action_key)
    print('prev_action: ', prev_action)
    if prev_action == None:
        prev_value = None
    else:
        prev_value = prev_action['prev_value']
    
    var_entity.update({
        'value': value,
        'prev_value': prev_value,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    last_action_entity.update({
        'prev_value': value,
        'var_name': name,
        'action_name': 'set',
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })
    datastore_client.put(var_entity)
    datastore_client.put(last_action_entity)

    output = '{var_name}={var_value}'.format(var_name = name, var_value = value)

    return render_template('index.html', output=output)

@app.route('/get')
def get_var():
    name=request.args.get('name')
    complete_key = datastore_client.key("variable", name)

    task = datastore_client.get(complete_key)
    if task == None:
        var_value = None
    else:
        var_value = task['value']    

    output = '{var_name}={var_value}'.format(var_name = name, var_value = var_value)

    return render_template('index.html', output=output)

@app.route('/unset')
def unset_var():
    name=request.args.get('name')
    complete_key = datastore_client.key("variable", name)
    last_action_key = datastore_client.key("last_action", name)
    last_action_entity = datastore.Entity(key=last_action_key)

    task = datastore_client.get(complete_key)
    print('task: ', task)
    if task != None:
        datastore_client.delete(complete_key)
    
        last_action_entity.update({
            'prev_value': task[value],
            'var_name': name,
            'action_name': 'set',
            'updated': datetime.datetime.now(tz=datetime.timezone.utc)
        })
        print('last action entity: ', last_action_entity)
        datastore_client.put(last_action_entity)
        output = '{var_name}={var_value}'.format(var_name = name, var_value = None)

    return render_template('index.html', output=output)

@app.route('/numequalto')    
def get_num_equal_to():
    query = datastore_client.query(kind="variable")
    value=request.args.get('value')
    query.add_filter('value','=', value)
    filtered = list(query.fetch())

    return render_template('index.html', output=len(filtered))
    
@app.route('/undo')
def undo_recent_command():
    query = datastore_client.query(kind="last_action")
    query.order = ['updated']
    print('last actions: ', list(query.fetch()))
    last_action = list(query.fetch()).pop()

    if last_action['action_name'] == 'undo':
        return render_template('index.html', 'NO COMMANDS')

    var_name = last_action['var_name']

    var_key = datastore_client.key("variable", var_name)
    var_entity = datastore.Entity(key=var_key)
    last_action_key = datastore_client.key("last_action", var_name)
    last_action_entity = datastore.Entity(key=last_action_key)

    var = datastore_client.get(var_key)
    if var != None:
        prev_value = var['prev_value']
    else:
        prev_value = last_action['prev_value']

    var_entity.update({
        'value': prev_value,
        'prev_value': None,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    last_action_entity.update({
        'prev_value': prev_value,
        'var_name': var_name,
        'action_name': 'undo',
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    datastore_client.put(var_entity)
    datastore_client.put(last_action_entity)

    output = '{var_name}={var_value}'.format(var_name = var_name, var_value = prev_value)

    return render_template('index.html', output=output)

@app.route('/redo')
def redo_command():
    query = datastore_client.query(kind="last_action")
    query.add_filter("action_name", "=", "set")
    # print('last actions: ', list(query.fetch()))
    last_undone_action = list(query.fetch())[0]
    print('last undone action: ', last_undone_action)

    var_name = last_undone_action['var_name']
    prev_value = last_undone_action['prev_value']

    var_key = datastore_client.key("variable", var_name)
    var_entity = datastore.Entity(key=var_key)
    last_action_key = datastore_client.key("last_action", var_name)
    last_action_entity = datastore.Entity(key=last_action_key)

    var_entity.update({
        'value': prev_value,
        'prev_value': prev_value,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    last_action_entity.update({
        'prev_value': prev_value,
        'var_name': var_name,
        'action_name': 'redo',
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    datastore_client.put(var_entity)
    datastore_client.put(last_action_entity)

    output = '{var_name}={var_value}'.format(var_name = var_name, var_value = prev_value)

    return render_template('index.html', output=output)

@app.route('/end')    
def end_session():
    query = datastore_client.query()
    entities = list(query.fetch())
    print('items: ', entities)
    for entity in entities:
        datastore_client.delete(entity.key)

    output='CLEANED'
    return render_template('index.html', output=output)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)