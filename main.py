from google.cloud import datastore

from flask import Flask, render_template, request

import datetime

app = Flask(__name__)

datastore_client = datastore.Client()

def update_action_and_var(value, prev_value, redo_value, name, action_name):
    var_key = datastore_client.key("variable", name)
    var_entity = datastore.Entity(key=var_key)

    action_key = datastore_client.key("action")
    action_entity = datastore.Entity(key=action_key)

    var_entity.update({
        'name': name,
        'value': value,
        'prev_value': prev_value,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    action_entity.update({
        'value': value,
        'redo_value': redo_value,
        'var_name': name,
        'action_name': action_name,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })
    datastore_client.put(var_entity)
    datastore_client.put(action_entity)

@app.route('/')
def start():
    return render_template('index.html', output='Hello, please type any command')

@app.route('/set')
def set_var():
    name = request.args.get('name')
    value = request.args.get('value')
    query = datastore_client.query(kind="action")
    query.order = ['updated']
    actions = list(query.fetch())   

    filtered_by_name = [action for action in actions if action['var_name'] == name]
    prev_value = None
    if len(filtered_by_name) != 0:
        prev_action = filtered_by_name.pop()
        prev_value = prev_action['value']
    
    update_action_and_var(value, prev_value, None, name, 'set')

    output = '{var_name} = {var_value}'.format(var_name = name, var_value = value)

    return render_template('index.html', output=output)

@app.route('/get')
def get_var():
    name = request.args.get('name')
    var_key = datastore_client.key("variable", name)

    var = datastore_client.get(var_key)
    if var == None:
        var_value = None
    else:
        var_value = var['value']    

    output = '{var_value}'.format(var_value = var_value)

    return render_template('index.html', output=output)

@app.route('/unset')
def unset_var():
    name=request.args.get('name')
    var_key = datastore_client.key("variable", name)
    action_key = datastore_client.key("action")
    action_entity = datastore.Entity(key=action_key)
    var = datastore_client.get(var_key)
    if var != None:
        datastore_client.delete(var_key)
    
        action_entity.update({
            'value': var['value'],
            'var_name': name,
            'action_name': 'set',
            'updated': datetime.datetime.now(tz=datetime.timezone.utc)
        })

        datastore_client.put(action_entity)
        output = '{var_name} = {var_value}'.format(var_name = name, var_value = None)
    else:
        output = 'The variable was not set'    

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
    query = datastore_client.query(kind="action")
    query.order = ['updated']
    actions = list(query.fetch())
    commands_to_undo = [action for action in actions if action['action_name'] == 'set']
    if len(commands_to_undo) == 0:
        return render_template('index.html', output='NO COMMANDS')
    action_to_undo = commands_to_undo.pop()

    datastore_client.delete(action_to_undo.key)
    
    var_name = action_to_undo['var_name']
    var_key = datastore_client.key("variable", var_name)
    var = datastore_client.get(var_key)
    set_actions_by_name = [el for el in commands_to_undo if el['var_name'] == var['name']]
    value = var['prev_value']
    value_to_recover = var['value']
    if len(set_actions_by_name) > 1:
        prev_value = set_actions_by_name[-2]['value']
    else:
        prev_value = None    
    update_action_and_var(value, prev_value, value_to_recover, var_name, 'undo')
    
    output = '{var_name} = {var_value}'.format(var_name = var_name, var_value = value)

    return render_template('index.html', output=output)

@app.route('/redo')
def redo_command():
    query = datastore_client.query(kind="action")
    query.order = ['updated']
    actions = list(query.fetch())

    commands_to_redo = [action for action in actions if action['action_name'] == 'undo']

    action_to_redo = commands_to_redo.pop()

    prev_value = action_to_redo['value']
    datastore_client.delete(action_to_redo.key)
    
    var_name = action_to_redo['var_name']
    var_key = datastore_client.key("variable", var_name)
    var = datastore_client.get(var_key)
    
    value = action_to_redo['redo_value']

    update_action_and_var(value, prev_value, None, var_name, 'set')
    output = '{var_name} = {var_value}'.format(var_name = var['name'], var_value = value)

    return render_template('index.html', output=output)

@app.route('/end')    
def end_session():
    var_query = datastore_client.query(kind='variable')
    action_query = datastore_client.query(kind='action')

    var_entities = list(var_query.fetch())
    action_entities = list(action_query.fetch())

    for var in var_entities:
        datastore_client.delete(var.key)

    for action in action_entities:
        datastore_client.delete(action.key)

    output='CLEANED'
    return render_template('index.html', output=output)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)