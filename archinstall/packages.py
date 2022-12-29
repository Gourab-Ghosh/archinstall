SERVICES = {
    "base_packages": {"base", "linux", "linux-firmware", "linux-headers", "linux-docs", "python", "python-rich"},
    "basic_packages": {"pkgfile", "base-devel", "bash-completion", "rsync", "sudo", "networkmanager", "dhcpcd", "grub", "freetype2", "fuse2", "dosfstools", "lzop", "efibootmgr", "libisoburn", "os-prober", "mtools", "neofetch"},
    "blackarch_packages": {"yay"},
    "printing_support": {"cups", "hplip"},
    "bluetooth_support": {"bluez", "bluez-utils", "bluez-hid2hci", "bluetooth-autoconnect"},
    "nvidia_drivers": {"nvidia-utils", "nvidia-settings", "nvidia-dkms"},
    "amd_drivers": {"xf86-video-amdgpu", "xf86-video-vesa", "vulkan-radeon", "libva-mesa-driver", "mesa-vdpau"},
    "intel_drivers": {"xf86-video-intel"},
}

PACKAGES = {
    "visual_studio_code": {"visual-studio-code-bin", "glib2", "libdbusmenu-glib", "org.freedesktop.secrets"}, # "icu69"
    "sublime_text": {"sublime-text", "gksu"},
    "firefox": {"sublime-text", "gksu"},
    "vlc": {"vlc"}, # "avahi", "aom", "gst-plugins-base-libs", "dav1d", "libdvdcss", "libavc1394", "libdc1394", "kwallet", "libbluray", "flac", "twolame", "libgme", "vcdimager", "libmtp", "systemd-libs", "smbclient", "libcdio", "gnu-free-fonts", "ttf-dejavu", "libssh2", "libnfs", "mpg123", "protobuf", "libmicrodns", "lua52-socket", "libdvdread", "libdvdnav", "libogg", "libshout", "libmodplug", "libvpx", "libvorbis", "speex", "opus", "libtheora", "libpng", "libjpeg-turbo", "librsvg", "x264", "x265", "zvbi", "libass", "libkate", "libtiger", "sdl_image", "srt", "aalib", "libcaca", "libpulse", "alsa-lib", "jack", "libsamplerate", "libsoxr", "lirc", "libgoom2", "projectm", "ncurses", "libnotify", "gtk3", "aribb24", "aribb25", "pcsclite", "live-media"
    "vlc_nvidia": {"libva-vdpau-driver"},
    "vlc_intel": {"libva-intel-driver"},
    "gimp": {"gimp", "poppler-glib", "alsa-lib", "curl", "ghostscript", "gvfs"},
    "thunderbird": {"thunderbird", "libotr", "libnotify"},
}

DE = {
    "kde": {"plasma", "plasma-wayland-session", "kde-applications", "kde-applications-meta", "xf86-video-nouveau"},
    "gnome": {"gnome", "gnome-extra"},
    "i3": {"i3"},
    "cinnamon": {"cinnamon", "gnome-terminal"},
    "lxqt": {"lxqt", "xdg-utils", "ttf-freefont", "filezilla",  "xscreensaver"},
    "lxde": {"lxde"},
    "xfce": {"xfce4", "xfce4-goodies"},
}

for key in DE.keys():
    DE[key].update({"xorg", "xorg-server"})

DM = {
    "gdm": {"gdm"},
    "sddm": {"sddm"},
    "lightdm": {"lightdm" "lightdm-settings" "lightdm-gtk-greeter"},
    "lxdm": {"lxdm"},
    "no_display_manager": set(),
}

KERNELS = {f"linux_{name}": {f"linux-{name}", f"linux-{name}-headers", f"linux-{name}-docs"} for name in ["zen", "lts", "hardened"]}

OPTIONAL_PACKAGES = {"xorg-server-devel", "xorg-apps", "iw", "wpa_supplicant", "dialog", "intel-ucode", "git", "reflector", "lshw", "unzip", "htop", "wget", "pulseaudio", "alsa-utils", "alsa-plugins", "pavucontrol", "xdg-user-dirs", "fprint", "archlinux-wallpaper"}

ALL_PACKAGE_GROUPS = {}
for _dict in [SERVICES, PACKAGES, DE, DM, KERNELS]:
    ALL_PACKAGE_GROUPS.update(_dict)

CHAOTIC_AUR_PACKAGES = {"visual-studio-code-bin", "bluetooth-autoconnect"}
