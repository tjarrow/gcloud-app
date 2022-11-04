from google.cloud import datastore

from flask import Flask, render_template, request

import datetime

app = Flask(__name__)

datastore_client = datastore.Client()

def update_action_and_var(var_entity, action_entity, value, prev_value, name):
    var_entity.update({
        'value': value,
        'prev_value': prev_value,
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })

    action_entity.update({
        'value': value,
        'var_name': name,
        'action_name': 'set',
        'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    })
    datastore_client.put(var_entity)
    datastore_client.put(action_entity)

@app.route('/')
def start():
    return render_template('index.html', output='Hello, please type any command')

@app.route('/set')
def set_var():
    name=request.args.get('name')
    value=request.args.get('value')
    
    var_key = datastore_client.key("variable", name)
    var_entity = datastore.Entity(key=var_key)

    action_key = datastore_client.key("action")
    action_entity = datastore.Entity(key=action_key)

    query = datastore_client.query(kind="action")
    # query.add_filter('var_name','=', name)
    query.order = ['updated']
    print('actions by name: ', list(query.fetch()))
    actions = list(query.fetch())   
    filtered_by_name = [p for p in actions if p['var_name'] == name]
    # print('filtered by name: ', filtered_by_name)
    # prev_action = datastore_client.get(action_key)
    prev_value = None
    if len(actions) != 0:
        prev_action = list(query.fetch()).pop()
        print('prev action: ', prev_action)
        prev_value = prev_action['value']
        print('prev value: ', prev_value)
    
    update_action_and_var(var_entity, action_entity, value, prev_value, name)
    print('var: ', var_entity)

    output = '{var_name}={var_value}'.format(var_name = name, var_value = value)

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
    action_key = datastore_client.key("action", name)
    action_entity = datastore.Entity(key=action_key)
    var = datastore_client.get(var_key)
    print('var: ', var)
    if var != None:
        datastore_client.delete(var_key)
    
        action_entity.update({
            'value': var['value'],
            'var_name': name,
            'action_name': 'set',
            'updated': datetime.datetime.now(tz=datetime.timezone.utc)
        })

        datastore_client.put(action_entity)
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
    query = datastore_client.query(kind="action")
    query.order = ['updated']
    # action = list(query.fetch()).pop()
    actions = list(query.fetch())
    print('all actions: ', actions)
    # if action['action_name'] == 'undo':
    #     return render_template('index.html', 'NO COMMANDS')

    var_name = action['var_name']

    var_key = datastore_client.key("variable", var_name)
    var_entity = datastore.Entity(key=var_key)
    action_key = datastore_client.key("action", var_name)
    action_entity = datastore.Entity(key=action_key)

    var = datastore_client.get(var_key)
    print('var: ', var)

    if var['prev_value'] == None:
        output = 'NO COMMANDS'
        return render_template('index.html', output=output)
    # value = None
    if var != None:
        value = var['prev_value']
    else:
        value = action['value']
        

    update_action_and_var(var_entity, action_entity, value, None, var_name)
    # var_entity.update({
    #     'value': prev_value,
    #     'prev_value': None,
    #     'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    # })

    # action_entity.update({
    #     'prev_value': prev_value,
    #     'var_name': var_name,
    #     'action_name': 'undo',
    #     'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    # })

    # datastore_client.put(var_entity)
    # datastore_client.put(action_entity)

    output = '{var_name}={var_value}'.format(var_name = var_name, var_value = value)

    return render_template('index.html', output=output)

@app.route('/redo')
def redo_command():
    query = datastore_client.query(kind="action")
    query.add_filter("action_name", "=", "set")
    # print('last actions: ', list(query.fetch()))
    last_undone_action = list(query.fetch())[0]
    print('last undone action: ', last_undone_action)

    var_name = last_undone_action['var_name']
    prev_value = last_undone_action['value']

    var_key = datastore_client.key("variable", var_name)
    var_entity = datastore.Entity(key=var_key)
    action_key = datastore_client.key("action", var_name)
    action_entity = datastore.Entity(key=action_key)

    update_action_and_var(var_entity, action_entity, prev_value, prev_value, var_name)
    # var_entity.update({
    #     'value': prev_value,
    #     'prev_value': prev_value,
    #     'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    # })

    # action_entity.update({
    #     'value': prev_value,
    #     'var_name': var_name,
    #     'action_name': 'redo',
    #     'updated': datetime.datetime.now(tz=datetime.timezone.utc)
    # })

    # datastore_client.put(var_entity)
    # datastore_client.put(action_entity)

    output = '{var_name}={var_value}'.format(var_name = var_name, var_value = prev_value)

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