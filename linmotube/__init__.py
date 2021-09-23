#----------------------------------------------------------------------
# LinMoTube
# by Jake Day
# v1.2
# Basic GUI for YouTube on Linux Mobile
#----------------------------------------------------------------------

import ctypes, os, requests, io, sys, subprocess, gi, json, threading
from urllib.parse import urlparse
from youtubesearchpython import *
from PIL import Image

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib

gi.require_version('GL', '1.0')
from OpenGL import GL, GLX

from mpv import MPV, MpvRenderContext, OpenGlCbGetProcAddrFn

class LinMoTube(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_title("LinMoTube")
        self.set_border_width(10)
        self.set_default_size(300, 420)
        #self.maximize()

    def draw(self):
        self.my_path = os.path.abspath(os.path.dirname(__file__))
        self.cache_path = os.path.expanduser("~/.cache/linmotube/")
        self.config_path = os.path.expanduser("~/.config/linmotube/")
        self.library_file = os.path.expanduser("~/.config/linmotube/library.json")

        if os.path.exists(self.cache_path) == False:
            os.mkdir(self.cache_path)

        if os.path.exists(self.config_path) == False:
            os.mkdir(self.config_path)

        if os.path.exists(self.library_file):
            with open(self.library_file, "r") as jsonfile:
                self.librarydata = json.load(jsonfile)
                jsonfile.close()
        else:
            self.librarydata = []

        provider = Gtk.CssProvider()
        provider.load_from_file(Gio.File.new_for_path(os.path.join(self.my_path, 'assets/linmotube.css')))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.get_style_context().add_class('app-theme')

        self.mode = "V"
        self.playing = False
        self.duration = "00:00"
        self.criteria = None
        self.library = False

        header = Gtk.HeaderBar(title="LinMoTube")
        header.get_style_context().add_class('app-theme')
        header.props.show_close_button = True

        logopb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/linmotube.png'),
            width=30, 
            height=30, 
            preserve_aspect_ratio=True)
        logoimg = Gtk.Image.new_from_pixbuf(logopb)
        header.pack_start(logoimg)

        self.set_titlebar(header)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(container)

        searchbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        container.add(searchbox)

        librarypb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/library.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        libraryimg = Gtk.Image.new_from_pixbuf(librarypb)
        librarybtn = Gtk.Button()
        librarybtn.connect("clicked", self.OnLoadLibrary)
        librarybtn.add(libraryimg)
        librarybtn.get_style_context().add_class('app-theme')
        searchbox.pack_start(librarybtn, False, False, 0)

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

        playback = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.controls.pack_start(playback, False, False, 0)

        self.currentlabel = Gtk.Label(label="no media selected")
        self.currentlabel.set_justify(Gtk.Justification.CENTER)
        self.currentlabel.set_line_wrap(True)
        self.currentlabel.set_max_width_chars(68)
        self.currentlabel.get_style_context().add_class('bold')
        playback.pack_start(self.currentlabel, True, True, 0)

        self.positionlabel = Gtk.Label()
        self.positionlabel.set_justify(Gtk.Justification.CENTER)
        playback.pack_start(self.positionlabel, True, True, 0)

        mediabtns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        playback.pack_start(mediabtns, True, True, 0)

        pausepb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/pause.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        pauseimg = Gtk.Image.new_from_pixbuf(pausepb)
        pausebtn = Gtk.Button()
        pausebtn.add(pauseimg)
        pausebtn.connect("clicked", self.OnPauseVideo)
        pausebtn.get_style_context().add_class('app-theme')
        mediabtns.pack_start(pausebtn, True, True, 0)

        stoppb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/stop.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)
        stopimg = Gtk.Image.new_from_pixbuf(stoppb)
        stopbtn = Gtk.Button()
        stopbtn.add(stopimg)
        stopbtn.connect("clicked", self.OnStopVideo)
        stopbtn.get_style_context().add_class('app-theme')
        mediabtns.pack_start(stopbtn, True, True, 0)

        self.loadinglabel = Gtk.Label()
        self.loadinglabel.set_markup("<big><b>loading media...</b></big>");
        self.loadinglabel.set_justify(Gtk.Justification.FILL)
        self.loadinglabel.set_line_wrap(True)
        self.loadinglabel.set_max_width_chars(68)
        self.loadinglabel.get_style_context().add_class('app-theme')
        container.pack_end(self.loadinglabel, False, False, 0)

        self.downloadpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/download.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)

        self.savedpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/saved.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)

        self.removepb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.my_path, 'assets/remove.png'),
            width=24, 
            height=24, 
            preserve_aspect_ratio=True)

        self.show_all()
        self.modebtn.grab_focus()
        self.controls.hide()

        self.GetOriginalIdleTime()

        x = threading.Thread(target=self.DoSearch, args=(None, True))
        x.start()

        self.player = MediaPlayer()

    def GetOriginalIdleTime(self):
        sbprocess = subprocess.Popen(['gsettings', 'get', 'org.gnome.desktop.session', 'idle-delay'], stdout=subprocess.PIPE)
        out, err = sbprocess.communicate()
        
        self.idleTime = out.decode('UTF-8').replace("uint32", "").strip()

    def OnToggleMode(self, button):
        self.library = False

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
            if self.library == False:
                x = threading.Thread(target=self.DoSearch, args=(self.criteria, False))
                x.start()

    def DoSearch(self, criteria, clear):
        self.criteria = criteria
        self.library = False

        if self.criteria == None:
            self.criteria = "linux mobile"

        if clear:
            GLib.idle_add(self.DoClearVideoList)

        GLib.idle_add(self.DoShowLoading)

        if clear:
            self.videosSearch = VideosSearch(self.criteria, limit=10)
        else:
            self.videosSearch.next()
        results = self.videosSearch.result()['result']

        for vid in results:
            thumbname = vid['id']

            if self.mode == "V":
                vidthumb = vid['thumbnails'][0]['url']

                vidurl = urlparse(vidthumb)
                
                if os.path.exists(os.path.join(self.cache_path, thumbname)) == False:
                    content = requests.get(vidthumb).content

                    file = open(os.path.join(self.cache_path, thumbname), "wb")
                    file.write(content)
                    file.close()

                    im = Image.open(os.path.join(self.cache_path, thumbname)).convert("RGB")
                    im.save(os.path.join(self.cache_path, thumbname), "jpeg")

            if self.mode == "M":
                channelthumb = vid['thumbnails'][0]['url']
                channelurl = urlparse(channelthumb)
                channelthumbname = vid['id']
            else:
                channelthumb = vid['channel']['thumbnails'][0]['url']
                channelurl = urlparse(channelthumb)
                channelthumbname = os.path.basename(channelurl.path)

            if os.path.exists(os.path.join(self.cache_path, channelthumbname)) == False:
                channelcontent = requests.get(channelthumb).content

                file = open(os.path.join(self.cache_path, channelthumbname), "wb")
                file.write(channelcontent)
                file.close()

                im = Image.open(os.path.join(self.cache_path, channelthumbname)).convert("RGB")
                im.save(os.path.join(self.cache_path, channelthumbname), "jpeg")

            GLib.idle_add(self.DoAddVideo, vid['id'], vid['title'], thumbname, channelthumbname, vid['channel']['name'], vid['viewCount']['short'])

        GLib.idle_add(self.DoHideLoading)

    def DoClearVideoList(self):
        videos = self.videolist.get_children()
        for video in videos:
            if video is not None:
                self.videolist.remove(video)

    def DoShowLoading(self):
        self.loadinglabel.show()

    def DoHideLoading(self):
        self.loadinglabel.hide()

    def DoAddVideo(self, id, title, thumbname, channelthumbname, channelname, viewcount):
        vidcard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.videolist.add(vidcard)

        if self.mode == "V":
            thumbpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename=os.path.join(self.cache_path, thumbname),
                width=300,
                height=200,
                preserve_aspect_ratio=True)
            thumbimg = Gtk.Image.new_from_pixbuf(thumbpb)
            vidbtn = Gtk.Button()
            vidbtn.add(thumbimg)
            vidbtn.connect("clicked", self.OnPlayVideo, None, id, title, self.mode)
            vidbtn.get_style_context().add_class('app-theme')
            vidbtn.get_style_context().add_class('no-border')
            vidcard.pack_start(vidbtn, True, True, 0)

        vidmeta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vidcard.pack_start(vidmeta, False, False, 0)
        
        channelpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=os.path.join(self.cache_path, channelthumbname),
            width=68,
            height=68,
            preserve_aspect_ratio=False)
        channelimg = Gtk.Image.new_from_pixbuf(channelpb)

        if self.mode == "M":
            vidbtn = Gtk.Button()
            vidbtn.add(channelimg)
            vidbtn.connect("clicked", self.OnPlayVideo, None, id, title, self.mode)
            vidbtn.get_style_context().add_class('app-theme')
            vidbtn.get_style_context().add_class('no-border')
            vidmeta.pack_start(vidbtn, False, False, 0)
        else:
            vidmeta.pack_start(channelimg, False, False, 0)

        vidinfo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vidmeta.pack_start(vidinfo, False, False, 0)

        vidheader = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vidinfo.pack_start(vidheader, False, False, 0)

        titlelabel = Gtk.Label()
        titlelabel.set_markup("<a href=''><big><b>" + title.replace("&", "&amp;") + "</b></big></a>")
        titlelabel.connect("activate-link", self.OnPlayVideo, id, title, self.mode)
        titlelabel.set_justify(Gtk.Justification.FILL)
        titlelabel.set_line_wrap(True)
        titlelabel.set_max_width_chars(68)
        titlelabel.get_style_context().add_class('app-theme')
        vidheader.pack_start(titlelabel, True, True, 0)

        downloadbtn = Gtk.Button()

        if self.mode == "V":
            if os.path.exists(os.path.join(self.cache_path, id + ".mp4")):
                downloadimg = Gtk.Image.new_from_pixbuf(self.savedpb)
            else:
                downloadimg = Gtk.Image.new_from_pixbuf(self.downloadpb)
                downloadbtn.connect("clicked", self.OnDownloadVideo, id, title, thumbname)
        else:
            if os.path.exists(os.path.join(self.cache_path, id + ".mp3")):
                downloadimg = Gtk.Image.new_from_pixbuf(self.savedpb)
            else:
                downloadimg = Gtk.Image.new_from_pixbuf(self.downloadpb)
                downloadbtn.connect("clicked", self.OnDownloadVideo, id, title, thumbname)

        downloadbtn.add(downloadimg)
        downloadbtn.get_style_context().add_class('app-theme')
        downloadbtn.get_style_context().add_class('no-border')
        vidheader.pack_end(downloadbtn, False, False, 0)

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
        if self.playing:
            self.controls.show()
        else:
            self.controls.hide()
            self.currentlabel.set_text("no media selected")

    def OnLoadLibrary(self, button):
        self.DoClearVideoList()

        self.library = True

        for vid in self.librarydata:
            vidcard = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.videolist.add(vidcard)

            vidmeta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            vidcard.pack_start(vidmeta, False, False, 0)
            
            thumbpb = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename=os.path.join(self.cache_path, vid['thumb']),
                width=68,
                height=68,
                preserve_aspect_ratio=False)
            thumbimg = Gtk.Image.new_from_pixbuf(thumbpb)
            vidbtn = Gtk.Button()
            vidbtn.add(thumbimg)
            vidbtn.connect("clicked", self.OnPlayVideo, None, vid['id'], vid['title'], vid['type'])
            vidbtn.get_style_context().add_class('app-theme')
            vidbtn.get_style_context().add_class('no-border')
            vidmeta.pack_start(vidbtn, False, False, 0)

            titlelabel = Gtk.Label()
            titlelabel.set_markup("<a href=''><big><b>" + vid['title'].replace("&", "&amp;") + "</b></big></a>")
            titlelabel.connect("activate-link", self.OnPlayVideo, vid['id'], vid['title'], vid['type'])
            titlelabel.set_justify(Gtk.Justification.FILL)
            titlelabel.set_line_wrap(True)
            titlelabel.set_max_width_chars(68)
            titlelabel.get_style_context().add_class('app-theme')
            vidmeta.pack_start(titlelabel, True, True, 0)

            removeimg = Gtk.Image.new_from_pixbuf(self.removepb)
            removebtn = Gtk.Button()
            removebtn.add(removeimg)
            removebtn.connect("clicked", self.OnRemoveVideo, vid['id'])
            removebtn.get_style_context().add_class('app-theme')
            removebtn.get_style_context().add_class('no-border')
            vidmeta.pack_end(removebtn, False, False, 0)

        self.show_all()
        self.DoHideLoading()

        if self.playing:
            self.controls.show()
        else:
            self.controls.hide()
            self.currentlabel.set_text("no media selected")

    def OnPlayVideo(self, button, uri, id, title, type):
        self.currentlabel.set_text(title)
        self.positionlabel.set_text("loading...")
        self.controls.show()
        
        x = threading.Thread(target=self.DoPlayVideo, args=(button, uri, id, type))
        x.start()

    def DoPlayVideo(self, button, uri, id, type):
        vidurl = 'https://www.youtube.com/watch?v=' + id

        self.player.mode(type)

        if type == "V":
            if os.path.exists(os.path.join(self.cache_path, id + ".mp4")):
                self.player.play(os.path.join(self.cache_path, id + ".mp4"))
            else:
                self.player.play(vidurl)
        else:
            if os.path.exists(os.path.join(self.cache_path, id + ".mp3")):
                self.player.play(os.path.join(self.cache_path, id + ".mp3"))
            else:
                self.player.play(vidurl)

        self.playing = True

        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', '0']
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        return True

    def OnStopVideo(self, evt):
        self.player.stop()
        self.playing = False

        self.controls.hide()
        self.currentlabel.set_text("no media selected")
        self.positionlabel.set_text("")

        sbparams = ['gsettings', 'set', 'org.gnome.desktop.session', 'idle-delay', self.idleTime]
        sbproc = subprocess.Popen(sbparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

    def OnPauseVideo(self, evt):
        if self.playing:
            self.player.pause()
            self.playing = False
        else:
            self.player.resume()
            self.playing = True

    def OnDownloadVideo(self, button, id, title, thumb):
        button.get_child().set_from_pixbuf(self.savedpb)
        
        x = threading.Thread(target=self.DoDownloadVideo, args=(id, title, thumb))
        x.start()

    def DoDownloadVideo(self, id, title, thumb):
        vidurl = 'https://www.youtube.com/watch?v=' + id

        if self.mode == "M":
            downloadparams = [
                'youtube-dl',
                '--extract-audio',
                '--audio-format', 'mp3',
                '-o', os.path.join(self.cache_path, id + ".mp3"),
                vidurl
            ]
        else:
            downloadparams = [
                'youtube-dl',
                '--recode-video', 'mp4',
                '-o', os.path.join(self.cache_path, id + ".mp4"),
                vidurl
            ]
        download = subprocess.Popen(downloadparams, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        videodata = {
            'id' : id,
            'title' : title,
            'type' : self.mode,
            'thumb' : thumb
        }

        vids = []
        for vid in self.librarydata:
            vids.append(vid['id'])

        if id not in vids:
            self.librarydata.append(videodata)

        with open(self.library_file, "w") as jsonfile:
            json.dump(self.librarydata, jsonfile)
            jsonfile.close()

    def OnRemoveVideo(self, button, id):
        newdata = []
        for vid in self.librarydata:
            if (vid['id'] != id):
                newdata.append(vid)

        self.librarydata = newdata

        with open(self.library_file, "w") as jsonfile:
            json.dump(self.librarydata, jsonfile)
            jsonfile.close()

        self.OnLoadLibrary(button)

    def OnUpdateDuration(self, s):
        value = "%02d:%02d" % divmod(s, 60)
        self.duration = str(value)

    def DoUpdatePosition(self, s):
        value = "%02d:%02d" % divmod(s, 60)
        self.positionlabel.set_text(str(value) + "/" + self.duration)

    def OnUpdatePosition(self, s):
        GLib.idle_add(self.DoUpdatePosition, s)
        
        
class MediaPlayer(Gtk.GLArea):
    def __init__(self, **properties):
        super().__init__(**properties)

        self._proc_addr_wrapper = OpenGlCbGetProcAddrFn(get_process_address)

        self.ctx = None
        self.mode("V")

        self.connect("realize", self.DoRealize)
        self.connect("render", self.DoRender)
        self.connect("unrealize", self.DoUnrealize)

    def DoRealize(self, area):
        self.make_current()
        self.ctx = MpvRenderContext(self.mpv, 'opengl', opengl_init_params={'get_proc_address': self._proc_addr_wrapper})
        self.ctx.update_cb = self.wrapped_c_render_func

    def DoUnrealize(self, arg):
        self.ctx.free()
        self.vidmpv.terminate()
        self.audmpv.terminate()

    def wrapped_c_render_func(self):
        GLib.idle_add(self.call_frame_ready, None, GLib.PRIORITY_HIGH)

    def call_frame_ready(self, *args):
        if self.ctx.update():
            self.queue_render()

    def DoRender(self, arg1, arg2):
        if self.ctx:
            factor = self.get_scale_factor()
            rect = self.get_allocated_size()[0]

            width = rect.width * factor
            height = rect.height * factor

            fbo = GL.glGetIntegerv(GL.GL_DRAW_FRAMEBUFFER_BINDING)
            self.ctx.render(flip_y=True, opengl_fbo={'w': width, 'h': height, 'fbo': fbo})
            return True
        return False

    def mode(self, mode):
        if mode == "V":
            self.mpv = MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)
            self.mpv.fullscreen = True
        else:
            self.mpv = MPV(video=False)

        @self.mpv.property_observer('duration')
        def duration_observer(_name, value):
            if value != None:
                app.OnUpdateDuration(value)

        @self.mpv.property_observer('time-pos')
        def time_observer(_name, value):
            if value != None:
                app.OnUpdatePosition(value)

    def play(self, media):
        self.mpv.play(media)

    def stop(self):
        self.mpv.stop()

    def pause(self):
        self.mpv._set_property('pause', True)

    def resume(self):
        self.mpv._set_property('pause', False)

def get_process_address(_, name):
    address = GLX.glXGetProcAddress(name.decode("utf-8"))
    return ctypes.cast(address, ctypes.c_void_p).value

app = LinMoTube()
app.connect("destroy", Gtk.main_quit)
app.draw()
Gtk.main()
