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

        self.panel = wx.Panel(self, wx.ID_ANY)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.search = wx.BoxSizer(wx.HORIZONTAL)

        self.searchtext = wx.SearchCtrl(self.panel, value="")
        self.search.Add(self.searchtext, 1, wx.EXPAND, 5)

        self.searchbtn = wx.Button(self.panel, label="Search")
        self.search.Add(self.searchbtn, 0, wx.RIGHT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnVideoSearch, self.searchbtn)

        self.sizer.Add(self.search, flag=wx.EXPAND)

        self.sizer.AddSpacer(5)

        self.videopanel = scrolled.ScrolledPanel(self.panel, -1)

        self.videos = wx.BoxSizer(wx.VERTICAL)

        wx.InitAllImageHandlers()

        my_path = os.path.abspath(os.path.dirname(__file__))
        logoimg = wx.Image(os.path.join(my_path, 'assets/linmotube.png'), wx.BITMAP_TYPE_ANY)
        logoimgBmp = wx.StaticBitmap(self.videopanel, wx.ID_ANY, wx.Bitmap(logoimg))
        self.videos.Add(logoimgBmp, 0, wx.ALIGN_CENTER, 10)

        self.videopanel.SetAutoLayout(1)
        self.videopanel.SetupScrolling()
        self.videopanel.SetSizer(self.videos)

        self.sizer.Add(self.videopanel, 1, wx.EXPAND, 10)

        self.panel.SetSizerAndFit(self.sizer)
        self.panel.Layout()

    def OnClose(self, evt):
        self.Close()

    def OnVideoSearch(self, evt):
        self.DoSearch(self.searchtext.GetValue())

    def OnVideoSelect(self, evt):
        vidid = evt.GetEventObject().vidid

        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        vidurl = 'https://www.youtube.com/watch?v=' + vidid

        # settings from conf: --ytdl-format="bestvideo[height<=480]+bestaudio/best"
        self.watch = subprocess.Popen(['mpv', '--player-operation-mode=pseudo-gui', '--', vidurl],
                                  shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

    def DoSearch(self, criteria):
        self.videos.Clear(True)

        videosSearch = VideosSearch(criteria, limit=10)
        results = videosSearch.result()['result']

        for vid in results :
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
            thumbsize = 280
            if W > H:
                thmw = thumbsize
                thmh = thumbsize * H / W
            else:
                thmh = thumbsize
                thmw = thumbsize * W / H
            vidimg = vidimg.Scale(thmw, thmh)

            self.vidimgbtn = wx.BitmapButton(self.videopanel, wx.ID_ANY, wx.Bitmap(vidimg))
            self.vidimgbtn.vidid = vid['id']
            self.Bind(wx.EVT_BUTTON, self.OnVideoSelect, self.vidimgbtn)

            self.videos.Add(self.vidimgbtn, 0, wx.ALIGN_CENTER, 10)
            
            self.vidtitle = wx.StaticText(self.videopanel, label=vid['title'])
            self.vidtitle.Wrap(300)
            self.videos.Add(self.vidtitle, 0, wx.ALIGN_CENTER, 10)
            
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
