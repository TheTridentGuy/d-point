# d-point

## Attack the D-point! A hide-and-seek CTF built on the YubiKey's hardware security.

If you had fun playing or hosting this CTF, please drop a star, and consider sponsoring me if you're able to.

## How the CTF works:
- The host sets up a shared machine, and sets ground rules.
- The host configures a YubiKey and connects it to the shared machine, scoring is based on proving access to this YubiKey.
- Players are given root access to the machine.
- Players must make a request from the machine regularly, to prove that they're maintaining a foothold on the system.

## How to Play:
Get the server URL from your host. There are no public instances of this CTF to play, however you may host your own. 
Assuming your host is running the provided client on the CTF machine, the steps to make a request to the scoring server are as follows:
1. Read the contents of `/tmp/d-point` as a string.
2. Make a request to `https://<server_url>/capture?username=<username_of_your_choice>&hmac=<contents_of_file_from_the_last_step>`

## Technical Overview:
The provided client makes scoring simple, especially for beginners. The full scoring process is as follows:
1. Make a GET request to `https://<server_url>/nonce`. The server will respond with a nonce, encoded as a hexadecimal string.
2. [HMAC](https://en.wikipedia.org/wiki/HMAC) the bytes represented by the hex string, using the calculate function of the relevant [OATH](https://www.rfc-editor.org/info/rfc6287/)
application on the YubiKey plugged into the machine. In the default configuration, the OATH application is `d-point:d-point`. 
Most operating systems support some variant of the `yubikey-manager` package, that provides the `ykman` command that can be used for signing.
3. The resulting HMAC is encoded as a hexadecimal string, and sent to the server at `https://<server_url>/capture?username=<username_of_your_choice>&hmac=<hmac_as_hex>`.
4. This process must be repeated regularly, to prove a continued foothold in the system.
The included client automatically does step 1 and step 2, and writes the HMAC, encoded as a hex string to `/tmp/d-point`.

## Hosting an Instance:
### Setting up the YubiKey:
I recommend setting up a venv:
```shell
python3 -m venv .venv
source .venv/bin/activate
```

In the project root run:
```shell
pip3 install -r requirments.txt
python3 oath_setup.py
```
Copy the provided base32 encoded secret, you'll need it to set up the server. Then, open the Yubico Authenticator app on a NFC enabled device (like your phone), and click "Add Account".
Point your phone camera at the QR code printed in the terminal, click "Save", then connect the Yubikey to your device (your phone).
> #### Keep your secret a secret!
> This CTF's scoring is based on it. Anyone with access to the secret can claim to have access to the YubiKey you put it on.
> Note that due to the nature of the YubiKeys, the secret is safe on  your YubiKey. If your secret is leaked, it can be regenerated, 
> and the YubiKey reprogramed.

### Setting up the Server:
Make a `.env` file with `DATABASE_URL` and `OATH_SECRET_B32` environment variables:
```dotenv
DATABASE_URL=file:database.sqlite
OATH_SECRET_B32=<base32_encoded_OATH_secret_from_the_last_section>
```
In your server environment, create a `database.sqlite` to persist your database:
```shell
touch $HOME/database.sqlite
```
If you're familiar with Docker, you can build your own images using the Dockerfile in `server/`.
Pre-built docker images are available at [hub.docker.com/r/thetridentguy/d-point](https://hub.docker.com/r/thetridentguy/d-point).
You can run them with:
```shell
docker run --name d-point thetridentguy/d-point:latest --env-file .env --mount type=bind,src=$HOME/database.sqlite,dst=/database.sqlite
```
The container should expose port 5000. You can reverse proxy this however you'd like.
