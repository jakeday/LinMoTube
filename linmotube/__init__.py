#----------------------------------------------------------------------
# LinMoTube
# by Jake Day
# v1.1
# Basic GUI for YouTube on Linux Mobile
#----------------------------------------------------------------------

import os, requests, io, sys, subprocess, gi, json, threading
from urllib.parse import urlparse
from youtubesearchpython import *
from PIL import Image

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib

class LinMoTube(Gtk.Window):
    def __init__(self):
        super().__init__(title="LinMoTube")
        self.set_border_width(10)
        self.set_default_size(300, 420)
        #self.maximize()

        self.my_path = os.path.abspath(os.path.dirname(__file__))

        provider = Gtk.CssProvider()
        provider.load_from_file(Gio.File.new_for_path(os.path.join(self.my_path, 'assets/linmotube.css')))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.get_style_context().add_class('app-theme')

        self.mode = "V"
        self.criteria = None
        self.watch = None

        header = Gtk.HeaderBar(title="LinMoTube")
        header.get_style_context().add_class('app-theme')
        header.props.show_close_button = True

        self.set_titlebar(header)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(container)

        searchbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        container.add(searchbox)

        logopb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/linmotube.png'),
            width=30, 
            height=30, 
            preserve_aspect_ratio=True)
        logoimg = Gtk.Image.new_from_pixbuf(logopb)
        searchbox.pack_start(logoimg, False, False, 0)

        self.searchentry = Gtk.SearchEntry()
        self.searchentry.set_text("")
        self.searchentry.connect("activate", self.OnVideoSearch)
        self.searchentry.get_style_context().add_class('app-theme')
        searchbox.pack_start(self.searchentry, True, True, 0)

        searchbtn = Gtk.Button(label="Go")
        searchbtn.connect("clicked", self.OnVideoSearch)
        searchbtn.get_style_context().add_class('app-theme')
        searchbox.pack_start(searchbtn, False, False, 0)

        self.musicpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/music.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        self.musicimg = Gtk.Image.new_from_pixbuf(self.musicpb)
        self.videopb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/video.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        self.videoimg = Gtk.Image.new_from_pixbuf(self.videopb)
        self.modebtn = Gtk.Button()
        self.modebtn.connect("clicked", self.OnToggleMode)
        self.modebtn.add(self.videoimg)
        self.modebtn.get_style_context().add_class('app-theme')
        searchbox.pack_start(self.modebtn, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.connect("edge-reached", self.DoSearchMore, 70)

        container.pack_start(scrolled, True, True, 0)

        self.videolist = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scrolled.add(self.videolist)

        self.controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.controls.get_style_context().add_class('border-top')
        container.pack_end(self.controls, False, False, 0)

        nowplayinglabel = Gtk.Label(label="- Now Playing -")
        nowplayinglabel.set_justify(Gtk.Justification.LEFT)
        self.controls.pack_start(nowplayinglabel, False, False, 0)

        playback = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.controls.pack_start(playback, False, False, 0)

        stoppb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/stop.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        stopimg = Gtk.Image.new_from_pixbuf(stoppb)
        self.stopbtn = Gtk.Button()
        self.stopbtn.add(stopimg)
        self.stopbtn.connect("clicked", self.OnStopVideo)
        self.stopbtn.get_style_context().add_class('app-theme')
        playback.pack_start(self.stopbtn, False, False, 0)

        self.currentlabel = Gtk.Label(label="no media selected")
        self.currentlabel.set_justify(Gtk.Justification.CENTER)
        self.currentlabel.set_line_wrap(True)
        self.currentlabel.set_max_width_chars(68)
        playback.pack_start(self.currentlabel, True, True, 0)

        self.show_all()
        self.stopbtn.hide()

        self.GetOriginalIdleTime()

        x = threading.Thread(target=self.DoSearch, args=(None, True))
        x.start()

    def GetOriginalIdleTime(self):
        sbprocess = subprocess.Popen(['gsettings', 'get', 'org.gnome.desktop.session', 'idle-delay'], stdout=subprocess.PIPE)
        out, err = sbprocess.communicate()
        
        self.idleTime = out.decode('UTF-8').replace("uint32", "").strip()

    def OnToggleMode(self, button):
        if self.mode == "V":
            self.mode = "M"
            self.modebtn.get_child().set_from_pixbuf(self.musicpb)
        else:
            self.mode = "V"
            self.modebtn.get_child().set_from_pixbuf(self.videopb)

        x = threading.Thread(target=self.DoSearch, args=(self.criteria, True))
        x.start()

    def OnVideoSearch(self, button):
        x = threading.Thread(target=self.DoSearch, args=(self.searchentry.get_text(), True))
        x.start()

    def DoSearchMore(self, swin, pos, dist):
        if pos == Gtk.PositionType.BOTTOM:
            x = threading.Thread(target=self.DoSearch, args=(self.criteria, False))
            x.start()

    def DoSearch(self, criteria, clear):
        self.criteria = criteria

        if self.criteria == None:
            self.criteria = "linux mobile"

        if clear:
            GLib.idle_add(self.DoClearVideoList)

        if clear:
            self.videosSearch = VideosSearch(self.criteria, limit=10)
        else:
            self.videosSearch.next()
        results = self.videosSearch.result()['result']

        for vid in results :
            thumbname = ""

            if self.mode == "V":
                vidthumb = vid['thumbnails'][0]['url']

                vidurl = urlparse(vidthumb)
                thumbname = os.path.basename(vidurl.path)

                content = requests.get(vidthumb).content

                file = open("/tmp/" + thumbname, "wb")
                file.write(content)
                file.close()

                im = Image.open("/tmp/" + thumbname).convert("RGB")
                im.save("/tmp/" + thumbname, "jpeg")

            if self.mode == "M":
                channelthumb = vid['thumbnails'][0]['url']
            else:
                channelthumb = vid['channel']['thumbnails'][0]['url']

            channelurl = urlparse(channelthumb)
            channelthumbname = os.path.basename(channelurl.path)

            channelcontent = requests.get(channelthumb).content

            file = open("/tmp/" + channelthumbname, "wb")
            file.write(channelcontent)
            file.close()

            im = Image.open("/tmp/" + channelthumbname).convert("RGB")
            im.save("/tmp/" + channelthumbname, "jpeg")

            GLib.idle_add(self.DoAddVideo, vid['id'], vid['title'], thumbname, channelthumbname, vid['channel']['name'], vid['viewCount']['short'])

    def DoClearVideoList(self):
        videos = self.videolist.get_children()
        for video in videos:
            if video is not None:
                self.videolist.remove(video)

    def DoAddVideo(self, id, title, thumbname, channelthumbname, channelname, viewcount):
        vidcard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.videolist.add(vidcard)

        if self.mode == "V":
            thumbpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename=os.path.join('/tmp/' + thumbname),
                width=300,
                height=200,
                preserve_aspect_ratio=True)
            thumbimg = Gtk.Image.new_from_pixbuf(thumbpb)
            vidbtn = Gtk.Button()
            vidbtn.add(thumbimg)
            vidbtn.connect("clicked", self.OnPlayVideo, None, id, title)
            vidbtn.get_style_context().add_class('app-theme')
            vidbtn.get_style_context().add_class('no-border')
            vidcard.pack_start(vidbtn, True, True, 0)

        vidmeta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vidcard.pack_start(vidmeta, False, False, 0)
        
        channelpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join('/tmp/' + channelthumbname),
            width=68,
            height=68,
            preserve_aspect_ratio=False)
        channelimg = Gtk.Image.new_from_pixbuf(channelpb)
        vidmeta.pack_start(channelimg, False, False, 0)

        vidinfo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vidmeta.pack_start(vidinfo, False, False, 0)

        titlelabel = Gtk.Label()
        titlelabel.set_markup("<a href=''><big><b>" + title.replace("&", "&amp;") + "</b></big></a>")
        titlelabel.connect("activate-link", self.OnPlayVideo, id, title)
        titlelabel.set_justify(Gtk.Justification.FILL)
        titlelabel.set_line_wrap(True)
        titlelabel.set_max_width_chars(68)
        titlelabel.get_style_context().add_class('app-theme')
        vidinfo.pack_start(titlelabel, False, False, 0)

        viddets = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vidinfo.pack_start(viddets, False, False, 0)

        if (channelname != None):
            channellabel = Gtk.Label()
            channellabel.set_markup("<small>" + channelname.replace("&", "&amp;") + "</small>")
            viddets.pack_start(channellabel, False, False, 0)

        if (viewcount != None):
            viewslabel = Gtk.Label()
            viewslabel.set_markup("<small>" + viewcount + "</small>")
            viddets.pack_end(viewslabel, False, False, 0)

        self.show_all()
        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.stopbtn.show()
            else:
                self.stopbtn.hide()
                self.currentlabel.set_text("no media selected")
        else:
            self.stopbtn.hide()
            self.currentlabel.set_text("no media selected")

    def OnPlayVideo(self, button, uri, id, title):
        self.currentlabel.set_text(title)
        self.stopbtn.show()
        
        self.swidth = self.get_size().width
        self.sheight = self.get_size().height

        lpmode = "portrait"
        if self.swidth >= self.sheight:
            lpmode = "landscape"
        
        x = threading.Thread(target=self.DoPlayVideo, args=(button, uri, id, lpmode))
        x.start()

    def DoPlayVideo(self, button, uri, id, lpmode):
        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        vidurl = 'https://www.youtube.com/watch?v=' + id

        if self.mode == "V":
            if lpmode == "landscape":
                playerparams = [
                    'mpv', 
                    '--fullscreen',
                    '--player-operation-mode=pseudo-gui', 
                    '--ytdl-format="(bestvideo[height<=720]+bestaudio)"',
                    '--', 
                    vidurl]
            else:
                playerparams = [
                    'mpv', 
                    '--autofit=100%x100%',
                    '--player-operation-mode=pseudo-gui', 
                    '--', 
                    vidurl]
        else:
            playerparams = ['mpv', '--no-video', '--', vidurl]

        self.watch = subprocess.Popen(playerparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', '0']
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        return True

    def OnStopVideo(self, evt):
        if self.watch is not None:
            poll = self.watch.poll()
            if poll is None:
                self.watch.terminate()

        self.currentlabel.set_text("no media selected")
        self.stopbtn.hide()

        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', self.idleTime]
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        
app = LinMoTube()
app.connect("destroy", Gtk.main_quit)
app.show_all()
Gtk.main()
