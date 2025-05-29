# tabata-web
Tabata timer web application with Plex integration

The Tabata method is a form of high-intensity interval training consisting of eight rounds of intense exercise performed for 20 seconds at a time with 10-second breaks. These intervals can be modified by each according to his own level or needs.
This project started because my Tabata timer app for Android started to serve too many ads for my taste, and decided that building a web app that can count time intervals cannot be that hard.
What I added besides the timer function is the capability to queue and play a Plex playlist with the same duration as the workout. Every press of a button in the web UI triggers another script in the backend that generates and plays the playlist you want, making sure that artists are not repeated, and you won't hear the same songs every day. The duration of the preset workouts can be set in the config.yml file. I added a public access point because I wanted to trigger the start of a workout by placing the phone next to a NFC tag. In case you will use a reverse-proxy, the web app distinguishes between LAN IPs and outside IPs, so the music playing cannot be triggered from the internet. 
