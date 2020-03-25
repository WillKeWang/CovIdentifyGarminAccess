import requests
import uuid
import time
import urllib
import hmac
import base64
import hashlib
import webbrowser
from tkinter import *
from tkinter.ttk import *
from pathlib import Path
from pymongo import MongoClient

oauth_consumer_key = ""
key_text = f"oauth_consumer_key={oauth_consumer_key}"
oauth_consumer_secret = ""
oauth_signature_method = "HMAC-SHA1"
method_text = f"oauth_signature_method={oauth_signature_method}"
oauth_version = "1.0"
version_text = f"oauth_version={oauth_version}"
request_url = "https://connectapi.garmin.com/oauth-service/oauth/request_token"
authorization_url = "https://connect.garmin.com/oauthConfirm"
access_url = 'https://connectapi.garmin.com/oauth-service/oauth/access_token'

user = urllib.parse.quote_plus('')
password = urllib.parse.quote_plus('')
ip = ""
port = ""
uri = f'mongodb://{user}:{password}@{ip}:{port}/?authSource=admin&authMechanism=SCRAM-SHA-256'


def signature_generator(url, key, method, version, secret, token="", verifier="", token_secret=""):
    global oauth_nonce
    oauth_nonce = str(uuid.uuid4().hex)
    nonce_text = f"oauth_nonce={oauth_nonce}"
    global oauth_timestamp
    oauth_timestamp = int(time.time())
    timestamp_text = f"oauth_timestamp={oauth_timestamp}"
    if token != "":
        parameters = "&".join([key, nonce_text, method, timestamp_text, token, verifier, version])
    else:
        parameters = "&".join([key, nonce_text, method, timestamp_text, version])
    parameters_encoded = urllib.parse.quote(parameters, safe='')
    url_encoded = urllib.parse.quote(url, safe='')
    base_string_encoded = url_encoded + "&" + parameters_encoded
    full_base = "POST&" + base_string_encoded
    sig_key = secret + "&" + token_secret
    sig_key_b = bytes(sig_key, 'UTF-8')
    base_string_b = bytes(full_base, 'UTF-8')
    hashed = hmac.new(sig_key_b, base_string_b, hashlib.sha1)
    sig_one = hashed.digest()
    sig_two = base64.standard_b64encode(sig_one)
    return urllib.parse.quote(str(sig_two, 'UTF-8'), safe='')


def generate_access_token():
    oauth_sig = signature_generator(request_url, key_text, method_text,
                                    version_text, oauth_consumer_secret)

    header1 = {'Authorization': f'OAuth oauth_consumer_key="{oauth_consumer_key}", oauth_signature_method="{oauth_signature_method}", oauth_nonce="{oauth_nonce}", oauth_timestamp="{str(oauth_timestamp)}", oauth_version="{oauth_version}", oauth_signature="{oauth_sig}"'}

    request_token = requests.post(request_url, headers=header1)
    print(request_token.content)

    request_token_string = str(request_token.content)
    oauth_token = request_token_string[request_token_string.index("=")+1:request_token_string.index("&")]
    oauth_token_secret = request_token_string[request_token_string.index("&")+20:-1]
    token_text = f'oauth_token={oauth_token}'

    webbrowser.open(authorization_url+"?oauth_token="+oauth_token)

    redirect_response = input("Paste your redirect URL: ")
    oauth_verifier = redirect_response[redirect_response.index('fier')+5:]
    verifier_text = f'oauth_verifier={oauth_verifier}'

    final_sig = signature_generator(access_url, key_text, method_text, version_text,
                                    oauth_consumer_secret, token_text, verifier_text, oauth_token_secret)

    header2 = {'Authorization': f'OAuth oauth_consumer_key="{oauth_consumer_key}", oauth_signature_method="{oauth_signature_method}", oauth_nonce="{oauth_nonce}", oauth_timestamp="{str(oauth_timestamp)}", oauth_version="{oauth_version}", oauth_signature="{final_sig}", oauth_token="{oauth_token}", oauth_verifier="{oauth_verifier}"'}

    access_token_request = requests.post(access_url, headers=header2)
    print(access_token_request.content)

    access_token_string = str(access_token_request.content)
    access_token = access_token_string[access_token_string.index("=")+1:access_token_string.index("&")]
    real_secret = access_token_string[access_token_string.index("&")+20:-1]
    token_text = f'oauth_token={access_token}'
    print(f'{token_text}\nToken Secret={real_secret}\nPlease close the app window now.')
    first_name = input("First Name: ").capitalize()
    last_name = input("Last Name: ").capitalize()
    keys = Path("Keys/")
    key_file = keys / first_name / last_name
    key_list = keys / 'KeyList'
    client = MongoClient(uri)
    db = client["HealthDemo"]
    col = db["Keys"]
    dic = {"Access token": access_token,
           "Access secret": real_secret}
    col.insert_one(dic)
    with open(key_file, 'w') as name_file:
        name_file.write(f'Access token: {access_token}\n')
        name_file.write(f'Access secret: {real_secret}')

    with open(key_list, 'a') as index_file:
        index_file.write(f'\n{access_token}')
    return [access_token, real_secret]


window = Tk()
window.geometry("200x200")
Button(text="Push for token",
       command=lambda: [generate_access_token(), window.destroy()]).pack(fill=BOTH, expand=1)
window.mainloop()