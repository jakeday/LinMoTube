# LinMoTube

A GUI client for YouTube on Linux Mobile.

### About
Browse and play media from YouTube without the need to sign-in. With the recent popularity of Linux Phones and the desire to stream media from YouTube, LinMoTube was born!

Supports both YouTube Video mode and YouTube Music mode with a convenient toggle switch!

Video List | Playback | Music List
:-------------------------:|:-------------------------:|:-------------------------:
![Video List](https://github.com/jakeday/LinMoTube/blob/master/docs/LinMoTube-VideosPage.png?raw=true) | ![Playback](https://github.com/jakeday/LinMoTube/blob/master/docs/LinMoTube-VideoPlayback.png?raw=true) | ![Music List](https://github.com/jakeday/LinMoTube/blob/master/docs/LinMoTube-MusicPage.png?raw=true)

### Instructions

0. (Prep) Install Dependencies:
  ```
   sudo apt install git python3 python3-pip libgtk-3-dev python3-requests python3-setuptools python3-gi python3-gi-cairo python3-opengl gir1.2-gtk-3.0 mpv libmpv-dev
  ```
1. Clone the LinMoTube repo:
  ```
   git clone --depth 1 https://github.com/jakeday/LinMoTube.git ~/linmotube
  ```
2. Change directory to LinMoTube repo:
  ```
   cd ~/linmotube
  ```
3. Install the app:
  ```
   sudo python3 setup.py install
  ```

### TODO

Add support for filters

Additional controls for playback

### Donations Appreciated!

PayPal: https://www.paypal.me/jakeday42

Bitcoin: 1AH7ByeJBjMoAwsgi9oeNvVLmZHvGoQg68
