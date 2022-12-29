import os, inquirer
from rich import print
from inquirer.shortcuts import confirm, list_input
from inquirer.render.console import ConsoleRender
from utils import get_locales, run_command, get_disks, get_partitons
from config import IS_TESTING

checkbox_message = "(Press <spacebar> to select or desellect and then hit <enter>)"

class Checkbox(inquirer.Checkbox):

    def __init__(self, name, message="", choices=None, default=None, ignore=False, validate=True, carousel=False):
        if default == "ALL":
            default = choices.copy()
        super().__init__(name, message.strip() + " " + checkbox_message, choices, default, ignore, validate, carousel)

choices_questions = [
    inquirer.List(
        "boot_partition",
        message="Select your boot partition",
        choices=get_partitons(),
        default="/dev/nvme0n1p1",
    ),
    inquirer.List(
        "root_partition",
        message="Select your root partition",
        choices=get_partitons(),
        default="/dev/nvme0n1p2",
    ),
    inquirer.List(
        "home_partition",
        message="Select your home partition",
        choices=[None] + get_partitons(),
        default="/dev/sda5"
    ),
    inquirer.List(
        "swap_type",
        message="Linux Swap Options",
        choices=["No Swap"] + ["Swap to File"] + ["Swap to Partition " + partiton for partiton in get_partitons()],
        default="Swap to File",
    ),
    inquirer.Text(
        "swap_file_size",
        message="Enter your swap file size (in GB) [Ignore if you have not selected Swap to File option]",
        default="8",
    ),
    inquirer.List(
        "filesystem",
        message="What filesyatem you want to use?",
        choices=[
            "BTRFS",
            "ext4",
        ],
        default="BTRFS",
    ),
    Checkbox(
        "gpu_types",
        message="Select the types of GPU you have in your system",
        choices=[
            "NVIDIA",
            "AMD",
            "Intel",
        ],
        default=["NVIDIA"],
    ),
    Checkbox(
        "additional_kernels",
        message="What addidional kernels do you want to install?",
        choices=[
            "Linux Zen",
            "Linux LTS",
            "Linux Hardened",
        ],
        default="ALL",
    ),
    Checkbox(
        "desktop_environments",
        message="What Desktop environment do you want to install?",
        choices=[
            "Gnome",
            "KDE",
            "i3",
            "Cinnamon",
            "lxqt",
            "lxde",
            "xfce",
        ],
        default=["KDE"],
    ),
    inquirer.List(
        "display_manager",
        message="What Desktop environment do you want to install?",
        choices=[
            "GDM",
            "SDDM",
            "LightDM",
            "LXDM",
            "No Display Manager",
        ],
        default="SDDM",
    ),
    Checkbox(
        "locales",
        message="Select your locales [Default Selected: en_US.UTF-8 UTF-8]",
        choices=get_locales(),
        default=["en_US.UTF-8 UTF-8"],
    ),
    inquirer.Confirm(
        "enable_multilib_repo",
        message="Do you want to add the multilib repository?",
        default=True,
    ),
    inquirer.Confirm(
        "add_chaotic_aur_repo",
        message="Do you want to add the chaotic aur repository?",
        default=True,
    ),
    inquirer.Confirm(
        "add_blackarch_repo",
        message="Do you want to add the blackarch repository?",
        default=True,
    ),
    inquirer.Confirm(
        "remove_sudo_password",
        message="Do you want to remove sudo password in terminal?",
        default=True,
    ),
    inquirer.Confirm(
        "enable_os_prober",
        message="Do you want to enable os-prober in grub? (Recommended for Multiboot system)",
        default=True,
    ),
    Checkbox(
        "servives_to_install",
        message="Select the services you want to install",
        choices=[
            "Printing Support",
            "Bluetooth Support",
        ],
        default="ALL",
    ),
    Checkbox(
        "packages_to_install",
        message="Select the packages you want to install",
        choices=[
            "Visual Studio Code [Requires Chaotic AUR]",
            "Sublime Text",
            "Firefox",
            "VLC",
            "Gimp",
            "Thunderbird",
        ],
        default="ALL",
    ),
    inquirer.Text(
        "username",
        message="Enter your username [Keep the field empty if you don't want to make any user]",
    ),
    inquirer.Text(
        "pc_name",
        message="Enter your PC name",
        default="archlinux"
    ),
]

def ask_for_partition():
    def run_cfdisk(disk_to_partition):
        if IS_TESTING:
            print("cfdisk " + disk_to_partition)
            print()
        else:
            run_command("cfdisk " + disk_to_partition)
            run_command("clear")
    run_command("lsblk")
    print()
    if confirm("Do you want to partition your disk(s)?", default = False, render = DEFAULT_RENDER):
        disks = get_disks()
        if not len(disks):
            raise Exception("No disks found!")
        disk_to_partition = disks[0] if len(disks) == 1 else list_input("Select the disk you want to partition", choices=disks, render=DEFAULT_RENDER)
        run_cfdisk(disk_to_partition)
        while len(disks):
            if confirm("Do you want to partition your disk(s) again?", default = False, render = DEFAULT_RENDER):
                disks = get_disks()
                if not len(disks):
                    raise Exception("No disks found!")
                disk_to_partition = disks[0] if len(disks) == 1 else list_input("Select the disk you want to partition", choices=disks, render=DEFAULT_RENDER)
                run_cfdisk(disk_to_partition)
            else:
                break

def ask_password(root_password_only):
    root_questions = [
        inquirer.Password(
            "root_password",
            message="Enter your root password",
        ),
        inquirer.Password(
            "confirm_root_password",
            message="Confirm root password",
        ),
    ]
    if root_password_only:
        root_answers = inquirer.prompt(root_questions, render = DEFAULT_RENDER)
        while root_answers["root_password"] != root_answers["confirm_root_password"] or root_answers["root_password"] == "":
            print()
            if root_answers["root_password"] != root_answers["confirm_root_password"]:
                print("Password does not match! Please try again")
            else:
                print("Passwords should not be empty! Try again")
            print()
            root_answers = inquirer.prompt(root_questions, render = DEFAULT_RENDER)
        return {"password": "", "root_password": root_answers["root_password"]}
    else:
        questions = [
            inquirer.Password(
                "password",
                message="Enter your password",
            ),
            inquirer.Password(
                "confirm_password",
                message="Confirm password",
            ),
        ]
        answers = inquirer.prompt(questions, render = DEFAULT_RENDER)
        while answers["password"] != answers["confirm_password"] or answers["password"] == "":
            print()
            if answers["password"] != answers["confirm_password"]:
                print("Password does not match! Please try again")
            else:
                print("Passwords should not be empty! Try again")
            print()
            answers = inquirer.prompt(questions, render = DEFAULT_RENDER)
        print()
        if confirm("Do you want to change the root password?", render = DEFAULT_RENDER, default = False):
            root_answers = inquirer.prompt(root_questions, render = DEFAULT_RENDER)
            while root_answers["root_password"] != root_answers["confirm_root_password"] or root_answers["root_password"] == "":
                print()
                if root_answers["root_password"] != root_answers["confirm_root_password"]:
                    print("Password does not match! Please try again")
                else:
                    print("Passwords should not be empty! Try again")
                print()
                root_answers = inquirer.prompt(root_questions, render = DEFAULT_RENDER)
            answers["root_password"] = root_answers["root_password"]
        else:
            answers["root_password"] = answers["password"]
        return {"password": answers["password"], "root_password": answers["root_password"]}

def ask_timezone():
    zones_dir = "/usr/share/zoneinfo/"
    region = list_input("Select Region", choices = os.listdir(zones_dir), default = "Asia", render = DEFAULT_RENDER)
    region_dir = os.path.join(zones_dir, region)
    timezone = list_input("Select Region", choices = os.listdir(region_dir), default = "Kolkata", render = DEFAULT_RENDER)
    return os.path.join(region_dir, timezone)

def ask_choices():
    return inquirer.prompt(choices_questions, render = DEFAULT_RENDER)
    # return inquirer.prompt(choices_questions)
