import ensurepip
ensurepip.bootstrap()
from pip._internal.cli.main import main as pip_main
pip_main(["install", "rich", "inquirer", "-q"])

import sys
from rich import print
from rich.traceback import install
from questions import ask_choices, ask_for_partition, ask_password, ask_timezone
from utils import run_command
from config import IS_TESTING
from installer import ArchInstaller
install()

def initialize():
    run_command("pacman -Syy")
    run_command("pacman -S archlinux-keyring --noconfirm")
    run_command("timedatectl set-ntp true")

def main():
    run_command("export EDITOR=nano")
    testing_mode_warning_message = "WARNING: you are running the script in testing mode. No changes will be made on your pc. If you want to run the script in development mode, change IS_TESTING to False in config.py."
    development_mode_warning_message = "WARNING: you are running the script in development mode. Changes will be made on your pc. If you want to run the script in testing mode, change IS_TESTING to True in config.py."
    print()
    print(testing_mode_warning_message if IS_TESTING else development_mode_warning_message)
    print()
    ask_for_partition()
    print()
    response = ask_choices()
    if not response:
        sys.exit()
    response["packages_to_install"] = [package[:-23] if package.endswith(" [Requires Chaotic AUR]") else package for package in response["packages_to_install"]]
    swap_size = response["swap_file_size"]
    try:
        swap_size_float = float(swap_size)
    except ValueError:
        response["swap_file_size"] = None
    else:
        response["swap_file_size"] = None if swap_size_float == float("inf") else swap_size_float
    passwords = ask_password(not response["username"])
    response.update(passwords)
    response["timezone"] = ask_timezone()
    if response["pc_name"] == "":
        response["pc_name"] = "archbtrfs" if response["filesystem"] == "BTRFS" else "arch"
    if IS_TESTING:
        print(response)
        print()
    installer = ArchInstaller(response)
    installer.install()

if __name__ == "__main__":
    main()

# Check Later:
# https://gist.github.com/fjpalacios/441f2f6d27f25ee238b9bfcb068865db
