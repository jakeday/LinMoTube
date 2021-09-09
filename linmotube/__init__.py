#----------------------------------------------------------------------
# LinMoTube
# by Jake Day
# v1.0
# Basic GUI for YouTube on Linux Mobile
#----------------------------------------------------------------------
#
# 2021-07-24 Updated to clean up interface a bit github.com/gurudvlp
#

import os, requests, io, sys, subprocess, wx, json, threading
import wx.lib.scrolledpanel as scrolled
from urllib.parse import urlparse
from youtubesearchpython import *
from PIL import Image

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, size=(300, 420))
		
        self.watch = None
        self.mode = "V"
        self.criteria = None

        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetForegroundColour(wx.Colour(0, 0, 0))
        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.AddSpacer(5)

        self.search = wx.BoxSizer(wx.HORIZONTAL)

        self.my_path = os.path.abspath(os.path.dirname(__file__))
        logoimg = wx.Image(os.path.join(self.my_path, 'assets/linmotube.png'), wx.BITMAP_TYPE_ANY)
        logoimg = logoimg.Scale(30, 30, wx.IMAGE_QUALITY_HIGH)
        logoimgBmp = wx.StaticBitmap(self.panel, wx.ID_ANY, wx.Bitmap(logoimg))
        self.search.Add(logoimgBmp, 0, wx.LEFT, 5)

        self.search.AddSpacer(5)

        self.searchtext = wx.SearchCtrl(self.panel, value="", style=wx.TE_RICH)
        self.search.Add(self.searchtext, 1, wx.EXPAND, 5)

        self.searchbtn = wx.Button(self.panel, label="Go", size=(50, 30))
        self.searchbtn.SetForegroundColour(wx.Colour(0, 0, 0))
        self.searchbtn.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.search.Add(self.searchbtn, 0, wx.RIGHT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnVideoSearch, self.searchbtn)

        self.videoimg = wx.Image(os.path.join(self.my_path, 'assets/video.png'), wx.BITMAP_TYPE_ANY)
        self.videoimg = self.videoimg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.modebtn = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap(self.videoimg), size=(30, 30), style=wx.NO_BORDER|wx.BU_EXACTFIT)
        self.search.Add(self.modebtn, 0, wx.RIGHT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnToggleMode, self.modebtn)

        self.sizer.Add(self.search, flag=wx.EXPAND)

        self.sizer.AddSpacer(5)

        self.videopanel = scrolled.ScrolledPanel(self.panel, -1)
        self.videopanel.SetForegroundColour(wx.Colour(0, 0, 0))
        self.videopanel.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.videos = wx.BoxSizer(wx.VERTICAL)

        wx.InitAllImageHandlers()

        self.videopanel.SetAutoLayout(1)
        self.videopanel.SetSizer(self.videos)

        self.sizer.Add(self.videopanel, 1, wx.EXPAND, 10)

        self.controls = wx.StaticBoxSizer(wx.VERTICAL, self.panel, label='Now Playing')

        self.stopimg = wx.Image(os.path.join(self.my_path, 'assets/stop.png'), wx.BITMAP_TYPE_ANY)
        self.stopimg = self.stopimg.Scale(30, 30, wx.IMAGE_QUALITY_HIGH)
        self.stopbtn = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap(self.stopimg), size=(50, 50), style=wx.NO_BORDER|wx.BU_EXACTFIT)
        self.controls.Add(self.stopbtn, 1, wx.ALIGN_CENTER|wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnStopVideo, self.stopbtn)

        self.playingtitle = wx.StaticText(self.panel, label='Loading...')
        self.playingtitle.Wrap(300)
        self.controls.Add(self.playingtitle, 0, wx.ALIGN_CENTER|wx.ALL, 10)

        self.sizer.Add(self.controls, flag=wx.EXPAND)

        self.stopbtn.Hide()
        self.playingtitle.SetLabel('no media selected')

        self.panel.SetSizerAndFit(self.sizer)
        self.panel.Layout()

        self.musicimg = wx.Image(os.path.join(self.my_path, 'assets/music.png'), wx.BITMAP_TYPE_ANY)
        self.musicimg = self.musicimg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)

        self.playimg = wx.Image(os.path.join(self.my_path, 'assets/play.png'), wx.BITMAP_TYPE_ANY)
        self.playimg = self.playimg.Scale(30, 30, wx.IMAGE_QUALITY_HIGH)

        self.getOriginalIdleTime()
            
        self.scaleFactor = wx.GetApp().GetTopWindow().GetContentScaleFactor()
        
        dsSize = wx.GetDisplaySize()
        
        print("Display Size W: " + str(wx.GetDisplaySize().width))
        print("Display Size H: " + str(wx.GetDisplaySize().height))
        print("Scaling Factor: " + str(self.scaleFactor))
        
        wx.CallLater(0, self.DoSearch, None)

    def getOriginalIdleTime(self):
        
        sbprocess = subprocess.Popen(['gsettings', 'get', 'org.gnome.desktop.session', 'idle-delay'], stdout=subprocess.PIPE)
        out, err = sbprocess.communicate()
        
        self.idleTime = out.decode('UTF-8').replace("uint32", "").strip()


    def OnClose(self, evt):
        self.Close()

    def OnVideoSearch(self, evt):
        self.DoSearch(self.searchtext.GetValue())

    def OnToggleMode(self, evt):
        if self.mode == "V":
            self.mode ="M"
            self.modebtn.SetBitmap(wx.Bitmap(self.musicimg))
        else:
            self.mode = "V"
            self.modebtn.SetBitmap(wx.Bitmap(self.videoimg))

        self.DoSearch(self.criteria)

    def OnStopVideo(self, evt):
        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        self.stopbtn.Hide()
        self.playingtitle.SetLabel('no media selected')
        self.panel.Layout()
        
        # Set screen blanking back to original value
        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', self.idleTime]
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

    def OnVideoSelect(self, evt):
        vidid = evt.GetEventObject().vidid

        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        self.playingtitle.SetLabel('loading...')
        self.panel.Layout()
        
        self.dsWidth = wx.GetDisplaySize().width
        self.dsHeight = wx.GetDisplaySize().height

        vidurl = 'https://www.youtube.com/watch?v=' + vidid

        if self.mode == "V":
            # Currently in video mode.  We need to determine if the screen is
            # in landscape or portrait mode
            lpMode = "portrait"
            if self.dsWidth >= self.dsHeight:
                lpMode = "landscape"
                playerparams = [
                    'mpv', 
                    #'--geometry=1440x' + str(round(self.dsHeight * self.scaleFactor)), 
                    '--fullscreen',
                    '--player-operation-mode=pseudo-gui', 
                    '--ytdl-format="(bestvideo[height<=720]+bestaudio)"',
                    '--', 
                    vidurl]
                #mpv --ytdl-format="(bestvideo[height<=1080]+bestaudio)[ext=webm]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/bestvideo+bestaudio/best" "${url}"
            else:
                playerparams = [
                    'mpv', 
                    #'--geometry=' + str(round(self.dsWidth * self.scaleFactor)) + 'x720', 
                    '--autofit=100%x100%',
                    '--player-operation-mode=pseudo-gui', 
                    #'--ytdl-format="(bestvideo[height<=480]+bestaudio)"',
                    '--', 
                    vidurl]
        else:
            playerparams = ['mpv', '--no-video', '--', vidurl]

        # settings from conf: --ytdl-format="bestvideo[height<=480]+bestaudio/best"
        self.watch = subprocess.Popen(playerparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        # Disable screen blanking for the duration of the video
        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', '0']
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        
        self.stopbtn.Show()
        self.playingtitle.SetLabel(evt.GetEventObject().vidtitle)
        self.panel.Layout()
 
    def DoSearch(self, criteria):
        if criteria is None:
            criteria = "linux mobile"
        else:
            self.criteria = criteria
            
        self.videos.Clear(True)

        videosSearch = VideosSearch(criteria, limit=10)
        results = videosSearch.result()['result']

        for vid in results :
            if self.mode == "V":
                vidthumb = vid['thumbnails'][0]['url']

                vurl = urlparse(vidthumb)
                thumbname = os.path.basename(vurl.path)

                content = requests.get(vidthumb).content

                file = open("/tmp/" + thumbname, "wb")
                file.write(content)
                file.close()

                im = Image.open("/tmp/" + thumbname).convert("RGB")
                im.save("/tmp/" + thumbname, "jpeg")

                vidimg = wx.Image("/tmp/" + thumbname, wx.BITMAP_TYPE_ANY)
                W = vidimg.GetWidth()
                H = vidimg.GetHeight()
                thumbsize = 360
                if W > H:
                    thmw = thumbsize
                    thmh = thumbsize * H / W
                else:
                    thmh = thumbsize
                    thmw = thumbsize * W / H
                vidimg = vidimg.Scale(int(thmw), int(thmh))

                self.vidimgbtn = wx.BitmapButton(self.videopanel, wx.ID_ANY, wx.Bitmap(vidimg), pos=(0, 0), size=(vidimg.GetWidth(), vidimg.GetHeight()),
                                                 style=wx.NO_BORDER|wx.BU_EXACTFIT)
                self.vidimgbtn.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.vidimgbtn.vidid = vid['id']
                self.vidimgbtn.vidtitle = vid['title']
                self.Bind(wx.EVT_BUTTON, self.OnVideoSelect, self.vidimgbtn)

                self.videos.Add(self.vidimgbtn, 0, wx.ALIGN_LEFT | wx.SHAPED, 0)
            
            # Create a Box to put the video meta data inside of
            self.videometa = wx.BoxSizer(wx.HORIZONTAL)
            
            # This will be split into two columns.
            # The left column will have the channel avatar, the right
            # column is going to be the title, channel name and views
            channelthumb = vid['channel']['thumbnails'][0]['url']

            vurl = urlparse(channelthumb)
            thumbname = os.path.basename(vurl.path)

            content = requests.get(channelthumb).content

            file = open("/tmp/" + thumbname, "wb")
            file.write(content)
            file.close()

            im = Image.open("/tmp/" + thumbname).convert("RGB")
            im.save("/tmp/" + thumbname, "jpeg")

            channelimg = wx.Image("/tmp/" + thumbname, wx.BITMAP_TYPE_ANY)
            channelimg = channelimg.Scale(68, 68)

            channelimgBmp = wx.StaticBitmap(self.videopanel, wx.ID_ANY, wx.Bitmap(channelimg))
            self.videometa.Add(channelimgBmp, 0, wx.EXPAND, 0)
            
            # Now, the right column will have two rows.  The title, then the
            # other data.
            self.videoTitleBox = wx.BoxSizer(wx.VERTICAL)
            
            # Create the title, then add it to the title box
            self.vidtitle = wx.StaticText(self.videopanel, label=vid['title'])
            font = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.vidtitle.SetFont(font)
            self.vidtitle.Wrap(290)
            self.vidtitle.vidid = vid['id']
            self.vidtitle.vidtitle = vid['title']
            
            self.videoTitleBox.Add(self.vidtitle, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 0)
            
            # Now assemble the channel name, views, and age
            nameViewsAgeBox = wx.BoxSizer(wx.HORIZONTAL)
            font = wx.Font(9, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.channel = wx.StaticText(self.videopanel, label=vid['channel']['name'])
            self.channel.SetFont(font)
            
            self.views = wx.StaticText(self.videopanel, label=vid['viewCount']['short'])
            self.views.SetFont(font);
 
            # Add the name, views, age box to the videoTitleBox
            nameViewsAgeBox.Add(self.channel, 1, wx.LEFT|wx.EXPAND, 10)
            nameViewsAgeBox.Add(self.views, 1, wx.LEFT|wx.EXPAND, 10)
            
            # Add the avatar and text info to videometa container
            self.videoTitleBox.Add(nameViewsAgeBox, 0, wx.LEFT, 0)
            self.videometa.Add(self.videoTitleBox, 0, wx.LEFT, 0)
            
            # Add everything to the full card
            self.videos.Add(self.videometa, 1, wx.EXPAND, 0)

            if self.mode == "M":
                self.playbtn = wx.BitmapButton(self.videopanel, wx.ID_ANY, wx.Bitmap(self.playimg), size=(50, 50), style=wx.NO_BORDER|wx.BU_EXACTFIT)
                self.playbtn.vidid = vid['id']
                self.playbtn.vidtitle = vid['title']
                self.vidcard.Add(self.playbtn, 0, wx.RIGHT)
                self.Bind(wx.EVT_BUTTON, self.OnVideoSelect, self.playbtn)
                self.vidtitle.Wrap(250)
                self.vidtitle.SetForegroundColour('black')
                self.vidtitle.SetBackgroundColour('white')

            self.videos.AddSpacer(10)

            self.panel.Layout()

            self.videopanel.SetupScrolling(False, True, 20, 20, True, True)

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "LinMoTube")
        self.SetTopWindow(frame)

        frame.Show(True)
        frame.Maximize(True)

        return True

app = MyApp()
app.MainLoop()
