import requests
import time
import uuid
import hmac
import hashlib
import base64
from tkinter import *
from tkinter.ttk import *
from json import loads, dump
from pathlib import Path
import urllib


oauth_consumer_key = ""
key_text = f"oauth_consumer_key={oauth_consumer_key}"
oauth_consumer_secret = ""
oauth_signature_method = "HMAC-SHA1"
method_text = f"oauth_signature_method={oauth_signature_method}"
oauth_version = "1.0"
version_text = f"oauth_version={oauth_version}"
access_token = ""  # me
access_secret = ""  # me
uploadStartTimeInSeconds = "1559237976"
uploadEndTimeInSeconds = "1559324376"
# uploadStartTimeInSeconds = "1559237976"
# uploadEndTimeInSeconds = "1559324376"
uploadStartTimeInSeconds = "1560113315"
uploadEndTimeInSeconds = "1560197315"
summary_type = 'dailies'
myUrl = 'https://healthapi.garmin.com/wellness-api/rest/'+summary_type

summary_list = ['dailies',
                'epochs',
                'thirdPartyDailies',
                'activities',
                'manuallyUpdatedActivities',
                'activityDetails',
                'sleeps',
                'bodyComps',
                'stressDetails',
                'userMetrics',
                'moveiq',
                'pulseOx']


def get_parameters():
    global access_token
    access_token = str(token_entry.get())
    global access_secret
    access_secret = str(secret_entry.get())
    global uploadStartTimeInSeconds
    uploadStartTimeInSeconds = str(start_entry.get())
    global uploadEndTimeInSeconds
    uploadEndTimeInSeconds = str(end_entry.get())
    global summary_type
    summary_type = type_var.get()
    global myUrl
    myUrl = 'https://healthapi.garmin.com/wellness-api/rest/'+summary_type


def request_generator(url, key, method, version, secret, token, token_secret, start, end):
    global oauth_nonce
    oauth_nonce = str(uuid.uuid4().hex)
    nonce_text = f"oauth_nonce={oauth_nonce}"
    global oauth_timestamp
    oauth_timestamp = int(time.time())
    timestamp_text = f"oauth_timestamp={oauth_timestamp}"
    parameters = "&".join([key, nonce_text, method, timestamp_text, token, version, end, start])
    parameters_encoded = urllib.parse.quote(parameters, safe='')
    url_encoded = urllib.parse.quote(url, safe='')
    base_string_encoded = url_encoded + "&" + parameters_encoded
    full_base = "GET&" + base_string_encoded
    sig_key = secret + "&" + token_secret
    sig_key_b = bytes(sig_key, 'UTF-8')
    base_string_b = bytes(full_base, 'UTF-8')
    hashed = hmac.new(sig_key_b, base_string_b, hashlib.sha1)
    sig_one = hashed.digest()
    sig_two = base64.standard_b64encode(sig_one)
    return urllib.parse.quote(str(sig_two, 'UTF-8'), safe='')


window = Tk()
window.title('Pull Request')
window.geometry("400x140")

Label(window, text="User Token: ").grid(row=0)
token_entry = Entry(window, width=44)
token_entry.grid(row=0, column=1, columnspan=3)

Label(window, text="User Secret: ").grid(row=1)
secret_entry = Entry(window, width=44)
secret_entry.grid(row=1, column=1, columnspan=3)

Label(window, text="Upload Start: ").grid(row=2)
start_entry = Entry(window, width=44)
start_entry.grid(row=2, column=1, columnspan=3)

Label(window, text="Upload End: ").grid(row=3)
end_entry = Entry(window, width=44)
end_entry.grid(row=3, column=1, columnspan=3)

Label(window, text="Summary Type: ").grid(row=4)
type_var = StringVar(window)
type_var.set("dailies")
type_list = OptionMenu(window, type_var, "dailies", *summary_list)
type_list.grid(row=4, column=1, columnspan=3)

Button(text="Enter", command=lambda: [get_parameters(), window.destroy()]).grid(row=5, column=0)
window.mainloop()

token_text = f'oauth_token={access_token}'
start_text = f'uploadStartTimeInSeconds={uploadStartTimeInSeconds}'
end_text = f'uploadEndTimeInSeconds={uploadEndTimeInSeconds}'

sig = request_generator(myUrl, key_text, method_text, version_text,
                        oauth_consumer_secret, token_text, access_secret,
                        start_text, end_text)

access_header = {'Authorization': f'OAuth oauth_nonce="{oauth_nonce}", '
                 f'oauth_signature="{sig}", '
                 f'oauth_token="{access_token}", '
                 f'oauth_consumer_key="{oauth_consumer_key}", '
                 f'oauth_timestamp="{str(oauth_timestamp)}", '
                 f'oauth_signature_method="{oauth_signature_method}", '
                 f'oauth_version="{oauth_version}"'}

params = (
    ('uploadStartTimeInSeconds', uploadStartTimeInSeconds),
    ('uploadEndTimeInSeconds', uploadEndTimeInSeconds),
)

pull_demo = requests.get(myUrl, headers=access_header, params=params)

my_data = loads(pull_demo.content.decode('UTF-8'))

if my_data:
    data_folder = Path(access_token)
    data_folder.mkdir(exist_ok=True, parents=True)
    data_file = data_folder / f'{uploadStartTimeInSeconds}to{uploadEndTimeInSeconds}_{summary_type}.json'
    with open(data_file, 'w') as json_file:
        dump(my_data, json_file)
        json_file.close()
else:
    raise Exception(f"No data for {summary_type} in this time range")
