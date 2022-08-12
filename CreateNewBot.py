import requests
def getCurrentId():
    with open("./currId.txt","r") as f:
        return int(f.read())
def SignUp(i):
    url = "http://localhost:8000/signup"
    payload = {
        "username": "BotAccountNumber" + str(i),
        "password": "password",
        "email": "BotAcountNumber" + str(i)
    }
    response = requests.request("POST", url, json=payload)
    print(response.text)
    return response.json()['token']
i = getCurrentId()
token = SignUp(i)
with open("./currId.txt","w") as f:
    f.write(str(i+1))
print(token)
with open("./users/model" + str(i) + ".py","w") as f:
    f.write(f'token = "{token}"')