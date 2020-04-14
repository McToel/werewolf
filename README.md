# werewolf
A Python server that helps you to play werewolf over a video or voice call

## Installation
- Install [Python 3.7](https://www.python.org/downloads/release/python-377/)
- clone repository
  - either using git or just by downloading and unpacking the repo
- open a terminal in the cloned repo
  - on windows: use the explorer to open the folder `werewolf` and then enter `cmd` in the address bar
- run `pip install -r requirements.txt` to install dependencies
- run `python game_server.py`

Now, enter `localhost:5000` into your Browser and you should see the login page. For players from the internet, you need to forward port 5000 (https://www.google.com/search?q=port+forwarding), and then they can enter `your_public_ip:5000` ([find public ip](https://ipecho.net/))
