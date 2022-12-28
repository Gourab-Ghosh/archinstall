import os
from rich import print
from utils import run_command, add_breakpoint
from filesystem_setup import EXT4Filesystem, BTRFSFilesystem
from config import IS_TESTING, ADD_OPTIONAL_PACKAGES
from packages import ALL_PACKAGE_GROUPS, OPTIONAL_PACKAGES

if IS_TESTING:
    run_command = lambda command, *args, **kwargs: print(command)
    os.chroot = lambda path: print("arch-chroot " + path)
    os.chdir = lambda path: print("cd " + path)
    os.chdir = lambda path: print("cd " + path)

disk_mount_password_problem_text = """

// See the polkit(8) man page for more information
// about configuring polkit.

// Allow udisks2 to mount devices without authentication
// for users in the \"wheel\" group.
polkit.addRule(function(action, subject) {
    if ((action.id == \"org.freedesktop.udisks2.filesystem-mount-system\" ||
         action.id == \"org.freedesktop.udisks2.filesystem-mount\") &&
        subject.isInGroup(\"wheel\")) {
        return polkit.Result.YES;
    }
});

""".strip()

class ArchInstaller:

    fs_classes = {
        "BTRFS" : BTRFSFilesystem,
        "ext4" : EXT4Filesystem,
    }

    def __init__(self, response):
        self.response = response
        swap_partition = None
        if self.response["swap_type"].startswith("Swap to Partition"):
            swap_partition = self.response["swap_type"][18:]
        self.fs = self.fs_classes[self.response["filesystem"]](self.response["boot_partition"], self.response["root_partition"], self.response["home_partition"], swap_partition)

    def run_chroot_command(self, command):
        full_command = f"arch-chroot {self.fs.temp_mount_dir} /bin/sh -c {repr(command)}"
        run_command(full_command)

    def enable_parallel_downloads(self, root_dir = "/"):
        pacman_conf_file = os.path.join(root_dir, "etc/pacman.conf")
        run_command(f"sed -i \"s/#ParallelDownloads/ParallelDownloads/g\" {pacman_conf_file}")

    def enable_multilib(self, root_dir = "/"):
        pacman_conf_file = os.path.join(root_dir, "etc/pacman.conf")
        run_command(f"sed -i \"/\[multilib\]/,/Include/\"\'s/^#//\' {pacman_conf_file}")

    def install_linux_base(self):
        required_packages = ALL_PACKAGE_GROUPS["base_packages"].copy()
        if self.response["filesystem"] == "BTRFS":
            required_packages.add("btrfs-progs")
        req_package_str = " ".join(sorted(list(required_packages)))
        run_command(f"pacstrap {self.fs.temp_mount_dir} {req_package_str} --noconfirm")

    def add_chaotic_aur_repo(self):
        self.run_chroot_command("pacman-key --recv-key FBA220DFC880C036 --keyserver keyserver.ubuntu.com")
        self.run_chroot_command("pacman-key --lsign-key FBA220DFC880C036")
        self.run_chroot_command("pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst' --noconfirm")
        self.run_chroot_command("echo \"\" | tee -a /etc/pacman.conf")
        self.run_chroot_command("echo \"[chaotic-aur]\" | tee -a /etc/pacman.conf")
        self.run_chroot_command("echo \"Include = /etc/pacman.d/chaotic-mirrorlist\" | tee -a /etc/pacman.conf")

    def add_blackarch_repo(self):
        self.run_chroot_command("curl -O https://blackarch.org/strap.sh")
        self.run_chroot_command("chmod +x strap.sh")
        self.run_chroot_command("./strap.sh")
        self.run_chroot_command("rm strap.sh")

    def add_sublime_text_repo(self):
        self.run_chroot_command("curl -O https://download.sublimetext.com/sublimehq-pub.gpg && pacman-key --add sublimehq-pub.gpg && pacman-key --lsign-key 8A8F901A && rm sublimehq-pub.gpg")
        self.run_chroot_command('echo -e "\\n[sublime-text]\\nServer = https://download.sublimetext.com/arch/stable/x86_64" | tee -a /etc/pacman.conf')

    def generate_swap_file(self):
        self.run_chroot_command("truncate -s 0 /swap/swapfile")
        self.run_chroot_command("chattr +C /swap/swapfile")
        self.run_chroot_command("btrfs property set /swap/swapfile compression none")
        self.run_chroot_command("dd if=/dev/zero of=/swap/swapfile bs=3G count=8 status=progress")
        self.run_chroot_command("chmod 600 /swap/swapfile")
        self.run_chroot_command("mkswap /swap/swapfile")
        self.run_chroot_command("swapon /swap/swapfile")
        self.run_chroot_command("echo \"\" | tee -a /etc/fstab")
        self.run_chroot_command("echo \"#swap\" | tee -a /etc/fstab")
        self.run_chroot_command("echo \"/swap/swapfile none swap defaults 0 0\" | tee -a /etc/fstab")

    def setup_timezone(self):
        timezone = self.response["timezone"]
        self.run_chroot_command(f"ln -sf {timezone} /etc/localtime")
        self.run_chroot_command("hwclock --systohc")

    def setup_locale(self):
        for locale in self.response["locales"]:
            self.run_chroot_command(f"sed -i \"s/#{locale}/{locale}/g\" /etc/locale.gen")
        self.run_chroot_command("locale-gen")

    def setup_hostname(self):
        pc_name = self.response["pc_name"]
        self.run_chroot_command(f"echo \"{pc_name}\" | tee -a /etc/hostname")
        self.run_chroot_command("echo \"\" | tee -a /etc/hosts")
        self.run_chroot_command("echo \"127.0.0.1    localhost\" | tee -a /etc/hosts")
        self.run_chroot_command("echo \"::1          localhost\" | tee -a /etc/hosts")
        self.run_chroot_command(f"echo \"127.0.1.1    {pc_name}.localdomain    localhost\" | tee -a /etc/hosts")

    def set_password(self, password, user = None):
        command = f"echo -en \"{password}\\n{password}\\n\" | passwd"
        if user:
            command += f" {user}"
        self.run_chroot_command(command)

    def setup_username_and_password(self):
        username = self.response["username"]
        password = self.response["password"]
        root_password = self.response["pc_name"]
        if username:
            self.run_chroot_command(f"useradd -m {username}")
            self.run_chroot_command(f"usermod -aG wheel,audio,video,optical,storage {username}")
            self.set_password(password, username)
        self.set_password(root_password)

    def get_needed_packages(self):
        needed_packages = ALL_PACKAGE_GROUPS["basic_packages"].copy()
        servives_to_install = self.response["servives_to_install"]
        all_groups = servives_to_install.copy()
        all_groups += self.response["packages_to_install"]
        all_groups += self.response["desktop_environments"]
        all_groups.append(self.response["display_manager"])
        all_groups += self.response["additional_kernels"]
        for gpu_type in self.response["gpu_types"]:
            all_groups.append(gpu_type + " Drivers")
            if gpu_type == "AMD":
                continue
            all_groups.append("VLC " + gpu_type)
        if self.response["add_blackarch_repo"]:
            all_groups.append("Blackarch Packages")
        for service in all_groups:
            key = service.lower().replace(" ", "_")
            needed_packages.update(ALL_PACKAGE_GROUPS[key])
        if "Printing Support" in servives_to_install and "Bluetooth Support" in servives_to_install:
            needed_packages.add("bluez-cups")
        if ADD_OPTIONAL_PACKAGES:
            needed_packages.update(OPTIONAL_PACKAGES)
        for package in ["visual-studio-code-bin", "bluetooth-autoconnect"]:
            if package in needed_packages:
                needed_packages.remove(package)
        needed_packages = sorted(list(needed_packages))
        return needed_packages

    def update_mkinitcpio_conf(self, root_dir = "/"):
        mkinitcpio_conf_dir = os.path.join(root_dir, "etc/mkinitcpio.conf")
        with open(mkinitcpio_conf_dir, "r") as rf:
            data = rf.read()
        for line in data.splitlines():
            if line.startswith("MODULES"):
                req_line = line
                break
        modules = req_line[9:-1].split()
        if "btrfs" not in modules or IS_TESTING:
            line_to_replace = req_line
            new_line = req_line.replace("(", "({").replace(")", "})").format(" ".join(modules + ["btrfs"]))
            run_command(f"sed -i \"s/{line_to_replace}/{new_line}/g\" {mkinitcpio_conf_dir}")
            kernels = ["linux"] + [kernel.lower().replace(" ", "-") for kernel in self.response["additional_kernels"]]
            kernels_text = " ".join(kernels)
            self.run_chroot_command(f"mkinitcpio -p {kernels_text}")

    def enable_os_prober_in_grub(self, root_dir = "/"):
        grub_file = os.path.join(root_dir, "etc/default/grub")
        os_prober_enable_text = "GRUB_DISABLE_OS_PROBER=false"
        with open(grub_file, "r") as rf:
            text = rf.read()
        line_to_replace = None
        for line in text.splitlines():
            line = line.strip().replace("\'", "\"")
            if line == os_prober_enable_text:
                return
            if line.replace(" ", "") == "#" + os_prober_enable_text:
                line_to_replace = line
                break
        if line_to_replace:
            run_command(f"sed -i \'s/{line_to_replace}/{os_prober_enable_text}/g\' {grub_file}")
        else:
            os_prober_enable_text = "\n" + os_prober_enable_text + "\n"
            run_command(f"echo -en {repr(os_prober_enable_text)} | tee -a {grub_file}")

    def setup_grub(self):
        bootloader_id = "Arch Linux"
        if self.response["filesystem"] == "BTRFS":
            bootloader_id += " (BTRFS)"
        self.run_chroot_command(f"grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=\"{bootloader_id}\" --recheck")
        if self.response["enable_os_prober"]:
            self.enable_os_prober_in_grub(self.fs.temp_mount_dir)
        self.run_chroot_command("grub-mkconfig -o /boot/grub/grub.cfg")

    def enable_services(self): # incomplete
        services = ["dhcpcd", "NetworkManager"]
        if self.response["filesystem"] == "BTRFS":
            services.append("fstrim.timer")
        if "Printing Support" in self.response["servives_to_install"]:
            services.append("cups")
        if "Bluetooth Support" in self.response["servives_to_install"]:
            # services += ["bluetooth", "bluetooth-autoconnect"]
            services += ["bluetooth"]
        services.append(self.response["display_manager"].lower())
        services.sort(key = lambda _str: _str.lower())
        services_text = " ".join(services)
        self.run_chroot_command(f"systemctl enable {services_text}")

    def fix_disk_mount_password_problem(self, root_dir = "/"):
        rules_folder = os.path.join(root_dir, "etc/polkit-1/rules.d/")
        if not os.path.isdir(rules_folder):
            os.makedirs(rules_folder)
        if IS_TESTING:
            print()
            print(f"Writing the following to {rules_folder}/10-udisks2.rules:")
            print(disk_mount_password_problem_text)
            print()
        else:
            with open(f"{rules_folder}/10-udisks2.rules", "w") as wf:
                wf.write(disk_mount_password_problem_text)

    def install(self):
        self.fs.format_partitions()
        self.fs.mount_partitions()
        self.enable_parallel_downloads()
        self.install_linux_base()
        fstab_path = os.path.join(self.fs.temp_mount_dir, "etc/fstab")
        run_command(f"genfstab -U {self.fs.temp_mount_dir} >> {fstab_path}")
        self.enable_parallel_downloads(self.fs.temp_mount_dir)
        if self.response["enable_multilib_repo"]:
            self.enable_multilib(self.fs.temp_mount_dir)
        if self.response["add_blackarch_repo"]:
            self.add_blackarch_repo()
        if "Sublime Text" in self.response["packages_to_install"]:
            self.add_sublime_text_repo()
        if self.response["swap_type"] == "Swap to File":
            self.generate_swap_file()
        self.setup_timezone()
        self.setup_locale()
        self.setup_hostname()
        self.setup_username_and_password()
        packages_to_install = self.get_needed_packages()
        packages_to_install_text = " ".join(packages_to_install)
        self.run_chroot_command("pacman -Syu --noconfirm")
        self.run_chroot_command(f"pacman -S {packages_to_install_text} --needed --noconfirm")
        add_breakpoint()
        if self.response["add_chaotic_aur_repo"]:
            self.add_chaotic_aur_repo()
        self.run_chroot_command("pacman -Syu --noconfirm")
        if self.response["remove_sudo_password"]:
            self.run_chroot_command("echo \"%wheel ALL=(ALL:ALL) NOPASSWD: ALL\" | tee -a /etc/sudoers.d/10-installer")
        if self.response["filesystem"] == "BTRFS":
            self.update_mkinitcpio_conf(self.fs.temp_mount_dir)
        self.setup_grub()
        self.enable_services()
        if "NVIDIA" in self.response["gpu_types"]:
            self.run_chroot_command("nvidia-xconfig")
        self.fix_disk_mount_password_problem(self.fs.temp_mount_dir)

if __name__ == "__main__":
    minimum_response = {
        "boot_partition": "/dev/sda1",
        "root_partition": "/dev/sda2",
        "home_partition": None,
        "swap_type": "No Swap",
        "filesystem": "BTRFS",
        "additional_kernels": [],
        "desktop_environments": ["i3"],
        "display_manager": "SDDM",
        "locales": ["en_US.UTF-8 UTF-8"],
        "enable_multilib_repo": False,
        "add_chaotic_aur_repo": False,
        "add_blackarch_repo": False,
        "remove_sudo_password": False,
        "enable_os_prober": False,
        "servives_to_install": [],
        "packages_to_install": [],
        "username": "gg8576",
        "pc_name": "archbtrfs",
        "password": "pass",
        "root_password": "pass",
        "timezone": "/usr/share/zoneinfo/Asia/Kolkata",
        "gpu_types": [],
    }

    dummy_response = {
        "boot_partition": "/dev/nvme0n1p1",
        "root_partition": "/dev/nvme0n1p2",
        "home_partition": "/dev/sda5",
        "swap_type": "Swap to File",
        # "swap_type": "Swap to Partition /dev/nvme0n1p3",
        "filesystem": "BTRFS",
        "additional_kernels": ["Linux Zen", "Linux LTS", "Linux Hardened"],
        "desktop_environments": ["KDE"],
        "display_manager": "SDDM",
        "locales": ["en_US.UTF-8 UTF-8"],
        # "locales": ["zu_ZA ISO-8859-1"],
        "enable_multilib_repo": True,
        "add_chaotic_aur_repo": True,
        "add_blackarch_repo": True,
        "remove_sudo_password": True,
        "enable_os_prober": True,
        "servives_to_install": ["Printing Support", "Bluetooth Support"],
        "packages_to_install": ["Visual Studio Code", "Sublime Text"],
        "username": "gg8576",
        "pc_name": "archbtrfs",
        "password": "pass",
        "root_password": "pass",
        "timezone": "/usr/share/zoneinfo/Asia/Kolkata",
        "gpu_types": ["NVIDIA"],
    }
    
    dummy_response_2 = {
        "boot_partition": "/dev/sda1",
        "root_partition": "/dev/sda2",
        "home_partition": None,
        "swap_type": "Swap to File",
        "filesystem": "BTRFS",
        "gpu_types": [],
        "additional_kernels": ["Linux Zen", "Linux LTS", "Linux Hardened"],
        "desktop_environments": ["KDE", "Gnome", "i3", "Cinnamon", "lxqt", "lxde", "xfce"],
        "display_manager": "SDDM",
        "locales": ["en_US.UTF-8 UTF-8"],
        "enable_multilib_repo": True,
        "add_chaotic_aur_repo": True,
        "add_blackarch_repo": True,
        "remove_sudo_password": True,
        "enable_os_prober": True,
        "servives_to_install": [],
        "packages_to_install": ["Visual Studio Code", "Sublime Text", "Firefox", "VLC", "Gimp", "Thunderbird"],
        "username": "user",
        "pc_name": "archlinux",
        "password": "pass",
        "root_password": "pass",
        "timezone": "/usr/share/zoneinfo/Asia/Kolkata"
    }

    maximum_response = {
        "boot_partition": "/dev/sda1",
        "root_partition": "/dev/sda2",
        "home_partition": None,
        "swap_type": "Swap to File",
        "filesystem": "BTRFS",
        "gpu_types": ["NVIDIA", "AMD", "Intel"],
        "additional_kernels": ["Linux Zen", "Linux LTS", "Linux Hardened"],
        "desktop_environments": ["KDE", "Gnome", "i3", "Cinnamon", "lxqt", "lxde", "xfce"],
        "display_manager": "SDDM",
        "locales": ["en_US.UTF-8 UTF-8"],
        "enable_multilib_repo": True,
        "add_chaotic_aur_repo": True,
        "add_blackarch_repo": True,
        "remove_sudo_password": True,
        "enable_os_prober": True,
        "servives_to_install": ["Printing Support", "Bluetooth Support"],
        "packages_to_install": ["Visual Studio Code", "Sublime Text", "Firefox", "VLC", "Gimp", "Thunderbird"],
        "username": "user",
        "pc_name": "archlinux",
        "password": "pass",
        "root_password": "pass",
        "timezone": "/usr/share/zoneinfo/Asia/Kolkata"
    }

    # installer = ArchInstaller(minimum_response)
    # installer = ArchInstaller(dummy_response)
    installer = ArchInstaller(dummy_response_2)
    # installer = ArchInstaller(maximum_response)
    installer.install()



# Packages not found: visual-studio-code-bin, bluetooth-autoconnect
# firezilla

