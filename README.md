Simple application made on Google Cloud Engine with usage of Python3 + Flask. It demonstrates how to store data in Google datastore via HTTP requests.
All commands are executed in browser URL.
List of commands:

SET – /set?name={variable_name}&value={variable_value}] 
Set the variable variable_name to the value variable_value

GET – /get?name={variable_name} 
Print out the value of the variable variable_name or “None” if the variable is not set.

UNSET – /unset?name={variable_name}
Unset the variable variable_name, making it just like the variable was never set.

NUMEQUALTO – /numequalto?value={variable_value}
Print to the browser the number of variables that are currently set to variable_value. If no variables equal that value, prints 0.

UNDO – /undo
Undo the most recent SET/UNSET command or prints NO COMMANDS if no commands may be undone.

REDO – /redo
Redo the most recent SET/UNSET command which was undone. 

END – /end
Exit the program.


