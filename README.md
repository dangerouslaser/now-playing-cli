<h1>Now Playing</h1>
<h2>Script to pull currently playing and library information from tautulli API.</h2>

<img src="https://github.com/dangerouslaser/now-playing-cli/blob/main/now-playing-latest.png">

<b>Download the script</b>

<code>wget https://github.com/dangerouslaser/now-playing-cli/blob/main/now-playing</code>

<b>Make it executable</b>

<code>sudo chmod +x ./now-playing</code>

<b>Add your tautulli API key and URL</b>

<code>sudo nano ./now-playing</code>

<b>Move to /usr/local/bin/</b>

<code>sudo mv ./now-playing /usr/local/bin</code>

<h3>Usage</h3>

<b>Run with now-playing</b>

<code>now-playing</code>

<b>Monitor sessions and progress in real time</b>

<code>now-playing --watch</code>

<b>Show Library Stats</b>

<img src="https://github.com/dangerouslaser/now-playing-cli/blob/main/now-playing-library.png">

<code>now-playing --library</code>

<b>Check for active sessions and reboot</b>


<img src="https://github.com/dangerouslaser/now-playing-cli/blob/main/now-playing-reboot.png">

<code>now-playing --reboot</code>
