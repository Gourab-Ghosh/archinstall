import os
from rich import print
from utils import run_command, is_ssd
from config import IS_TESTING

if IS_TESTING:
    run_command = lambda command, *args, **kwargs: print(command)
    os.makedirs = lambda _dir: print(f"mkdir -p {_dir}")

class Filesystem:

    def __init__(self, boot_partition, root_partition, home_partition, swap_partition, temp_mount_dir = "/mnt"):
        self.boot_partition = boot_partition
        self.root_partition = root_partition
        self.home_partition = home_partition
        self.swap_partition = swap_partition
        self.temp_mount_dir = temp_mount_dir
        if not os.path.isdir(self.temp_mount_dir):
            os.makedirs(self.temp_mount_dir)

    def format_partitions(self):
        if not hasattr(self, "filesystem_format_command"):
            raise NotImplementedError()
        run_command(f"mkfs.fat -F32 {self.boot_partition}")
        run_command(f"{self.filesystem_format_command} {self.root_partition}")
        if self.home_partition:
            run_command(f"{self.filesystem_format_command} {self.home_partition}")
        if self.swap_partition:
            run_command(f"mkswap {self.swap_partition}")
            run_command(f"swapon {self.swap_partition}")

class EXT4Filesystem(Filesystem):
    filesystem_format_command = "mkfs.ext4 -F"

    def mount_partitions(self):
        run_command(f"mount {self.root_partition} {self.temp_mount_dir}")
        boot_dir = os.path.join(self.temp_mount_dir, "boot")
        if not os.path.isdir(boot_dir):
            os.makedirs(boot_dir)
        run_command(f"mount {self.boot_partition} {boot_dir}")
        if self.home_partition:
            home_dir = os.path.join(self.temp_mount_dir, "home")
            if not os.path.isdir(home_dir):
                os.makedirs(home_dir)
            run_command(f"mount {self.home_partition} {home_dir}")

class BTRFSFilesystem(Filesystem):
    filesystem_format_command = "mkfs.btrfs -f"

    def mount_partitions(self):
        subvols_type_1 = ["srv", "opt", "temp"]
        subvols_type_2 = ["var", "swap"]
        if not self.home_partition:
            subvols_type_1 += ["home"]
        subvols_type_1_mount_options = ["noatime", "compress=zstd", "space_cache=v2", "autodefrag", "discard=async"]
        subvols_type_2_mount_options = ["nodatacow", "discard=async"]
        if self.home_partition:
            run_command(f"mount {self.home_partition} {self.temp_mount_dir}")
            _dir = os.path.join(self.temp_mount_dir, "@home")
            run_command(f"btrfs su cr {_dir}")
            run_command(f"umount -l {self.temp_mount_dir}")
        run_command(f"mount {self.root_partition} {self.temp_mount_dir}")
        for subvol in [""] + subvols_type_1 + subvols_type_2:
            _dir = os.path.join(self.temp_mount_dir, "@" + subvol)
            run_command(f"btrfs su cr {_dir}")
        run_command(f"umount -l {self.temp_mount_dir}")
        mount_options = ",".join(subvols_type_1_mount_options)
        if is_ssd(self.root_partition):
            mount_options += ",ssd"
        run_command(f"mount -o {mount_options},subvol=@ {self.root_partition} {self.temp_mount_dir}")
        for subdir in set(["home", "boot"] + subvols_type_1 + subvols_type_2):
            _dir = os.path.join(self.temp_mount_dir, subdir)
            if not os.path.isdir(_dir):
                os.makedirs(_dir)
        for subvol in subvols_type_1:
            _dir = os.path.join(self.temp_mount_dir, subvol)
            mount_options = ",".join(subvols_type_1_mount_options)
            if is_ssd(self.root_partition):
                mount_options += ",ssd"
            run_command(f"mount -o {mount_options},subvol=@{subvol} {self.root_partition} {_dir}")
        if self.home_partition:
            _dir = os.path.join(self.temp_mount_dir, "home")
            mount_options = ",".join(subvols_type_1_mount_options)
            if is_ssd(self.home_partition):
                mount_options += ",ssd"
            run_command(f"mount -o {mount_options},subvol=@home {self.home_partition} {self.temp_mount_dir}")
        for subvol in subvols_type_2:
            _dir = os.path.join(self.temp_mount_dir, subvol)
            mount_options = ",".join(subvols_type_2_mount_options)
            if is_ssd(self.root_partition):
                mount_options += ",ssd"
            run_command(f"mount -o {mount_options},subvol=@{subvol} {self.root_partition} {_dir}")
        _dir = os.path.join(self.temp_mount_dir, "boot")
        run_command(f"mount {self.boot_partition} {_dir}")


# # fs = EXT4Filesystem("/dev/nvme0n1p1", "/dev/nvme0n1p2", "/dev/sda5")
# fs = BTRFSFilesystem("/dev/nvme0n1p1", "/dev/nvme0n1p2", "/dev/sda5")
# # fs = BTRFSFilesystem("/dev/nvme0n1p1", "/dev/nvme0n1p2", None)
# fs.format_partitions()
# fs.mount_partitions()