#----------------------------------------------------------------------
# LinMoTube
# by Jake Day
# v1.0
# Basic GUI for YouTube on Linux Mobile
#----------------------------------------------------------------------

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

        self.searchtext = wx.SearchCtrl(self.panel, value="")
        self.searchtext.SetForegroundColour(wx.Colour(0, 0, 0))
        self.searchtext.SetBackgroundColour(wx.Colour(255, 255, 255))
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
        self.videopanel.SetupScrolling(False, True)
        self.videopanel.SetSizer(self.videos)

        self.sizer.Add(self.videopanel, 1, wx.EXPAND, 10)

        self.controls = wx.BoxSizer(wx.VERTICAL)

        self.stopimg = wx.Image(os.path.join(self.my_path, 'assets/stop.png'), wx.BITMAP_TYPE_ANY)
        self.stopimg = self.stopimg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        self.stopbtn = wx.BitmapButton(self.panel, wx.ID_ANY, wx.Bitmap(self.stopimg), size=(30, 30))
        self.controls.Add(self.stopbtn, 1, wx.ALIGN_CENTER|wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnStopVideo, self.stopbtn)

        self.playingtitle = wx.StaticText(self.panel, label='Loading...')
        self.playingtitle.Wrap(300)
        self.controls.Add(self.playingtitle, 0, wx.ALIGN_CENTER|wx.ALL, 10)

        self.sizer.Add(self.controls, flag=wx.EXPAND)

        self.stopbtn.Hide()
        self.playingtitle.Hide()

        self.panel.SetSizerAndFit(self.sizer)
        self.panel.Layout()

        self.musicimg = wx.Image(os.path.join(self.my_path, 'assets/music.png'), wx.BITMAP_TYPE_ANY)
        self.musicimg = self.musicimg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)

        self.playimg = wx.Image(os.path.join(self.my_path, 'assets/play.png'), wx.BITMAP_TYPE_ANY)
        self.playimg = self.playimg.Scale(20, 20, wx.IMAGE_QUALITY_HIGH)

        wx.CallLater(0, self.DoSearch, None)

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
        self.playingtitle.Hide()
        self.playingtitle.SetLabel("Loading...")
        self.panel.Layout()

    def OnVideoSelect(self, evt):
        vidid = evt.GetEventObject().vidid

        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        self.playingtitle.Show()
        self.panel.Layout()

        vidurl = 'https://www.youtube.com/watch?v=' + vidid

        if self.mode == "V":
            playerparams = ['mpv', '--player-operation-mode=pseudo-gui', '--', vidurl]
        else:
            playerparams = ['mpv', '--no-video', '--', vidurl]

        # settings from conf: --ytdl-format="bestvideo[height<=480]+bestaudio/best"
        self.watch = subprocess.Popen(playerparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        self.stopbtn.Show()
        self.playingtitle.SetLabel(evt.GetEventObject().vidtitle)
        self.panel.Layout()

    def DoSearch(self, criteria):
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
                thumbsize = 300
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

                self.videos.Add(self.vidimgbtn, 0, wx.ALIGN_CENTER|wx.SHAPED, 0)
            
            self.details = wx.BoxSizer(wx.HORIZONTAL)

            font = wx.Font(9, wx.NORMAL, wx.ITALIC, wx.NORMAL)
            if vid['channel']['name'] is not None:
                self.channel = wx.StaticText(self.videopanel, label=vid['channel']['name'])
                self.channel.SetFont(font)
                self.channel.Wrap(250)
                self.details.Add(self.channel, 1, wx.LEFT|wx.EXPAND, 10)
                self.channel.SetForegroundColour(wx.Colour(0, 0, 0))
                self.channel.SetBackgroundColour(wx.Colour(220, 220, 220))

            if vid['viewCount']['short'] is not None:
                self.views = wx.StaticText(self.videopanel, label=vid['viewCount']['short'])
                self.views.SetFont(font)
                self.details.Add(self.views, 0, wx.RIGHT, 10)
                self.views.SetForegroundColour(wx.Colour(0, 0, 0))
                self.views.SetBackgroundColour(wx.Colour(220, 220, 220))
            
            self.videos.Add(self.details, flag=wx.EXPAND)

            self.vidcard = wx.BoxSizer(wx.HORIZONTAL)

            self.vidtitle = wx.StaticText(self.videopanel, label=vid['title'])
            font = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.NORMAL)
            self.vidtitle.SetFont(font)
            self.vidtitle.Wrap(300)
            self.vidtitle.vidid = vid['id']
            self.vidtitle.vidtitle = vid['title']

            self.vidcard.Add(self.vidtitle, 1, wx.ALIGN_CENTER|wx.EXPAND, 10)

            self.videos.Add(self.vidcard, 1, wx.ALIGN_CENTER|wx.EXPAND, 10)

            if self.mode == "M":
                self.playbtn = wx.BitmapButton(self.videopanel, wx.ID_ANY, wx.Bitmap(self.playimg), size=(30, 30), style=wx.NO_BORDER|wx.BU_EXACTFIT)
                self.playbtn.vidid = vid['id']
                self.playbtn.vidtitle = vid['title']
                self.vidcard.Add(self.playbtn, 0, wx.RIGHT)
                self.Bind(wx.EVT_BUTTON, self.OnVideoSelect, self.playbtn)
                self.vidtitle.Wrap(250)
                self.vidtitle.SetForegroundColour('black')
                self.vidtitle.SetBackgroundColour('white')

            self.videos.AddSpacer(10)

            self.panel.Layout()

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "LinMoTube")
        self.SetTopWindow(frame)

        frame.Show(True)

        return True

app = MyApp()
app.MainLoop()
