# Development

## Dependencies

You need the Python bindings for `notmuch`. In Debian/Ubuntu, this is provided by the `python3-notmuch` package.

## Fork the two repositories

Fork the `netviel` backend and frontend:

* https://github.com/DavidMStraub/netviel
* https://github.com/DavidMStraub/netviel-frontend

And clone them to your computer.

## Prepare the backend

Build it like so:

`cd netviel && python3 setup.py build`

## Prepare the frontend

Install NVM:

`wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash`

(you can replace `bash` with your shell of choice.)

Then use NVM to install the latest NPM, and use it in the frontend directory you have cloned:

`nvm install --latest-npm`

`cd netviel-frontend && npm install`

## Run a test server

Run the backend first:

`cd netviel && export FLASK_DEBUG=1 && python3 -m pip install -e . --user && python3 -m netviel`

(this avoids the need for admin rights). In a separate terminal, run the frontend:

`cd netviel-frontend && npm run start`

This will open a browser and fetch data from the local backend. Note that both run on `localhost` but the backend runs on port 5000 and the frontend on 8001.
