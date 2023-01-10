import os, sys, subprocess
from rich import print
from rich.console import Console
from inquirer.render.console import ConsoleRender
from inquirer.themes import BlueComposure
from inquirer.shortcuts import confirm, editor

class CustomTheme(BlueComposure):
    def __init__(self):
        super().__init__()
        self.Checkbox.selection_icon = ">"
        self.Checkbox.selected_icon = "[*]"
        self.Checkbox.unselected_icon = "[ ]"
        self.List.selection_cursor = ">"

DEFAULT_RENDER = ConsoleRender(theme = CustomTheme())

console = Console()

def add_breakpoint():
    print("\nPress <ENTER> to continue")
    try:
        input()
    except KeyboardInterruprt:
        sys.exit()

def run_command(command, get_output = False):
    if get_output:
        return subprocess.getoutput(command)
    console.log(f"Running command: {command}")
    exec_code = os.system(command)
    while exec_code:
        print(f"\nError occured executing the command: {command}")
        if confirm("Edit command and run?", default=True, render = DEFAULT_RENDER):
            command = editor(message = "", default = command, render = DEFAULT_RENDER).strip()
            console.log(f"Running command: {command}")
            exec_code = os.system(command)
        else:
            if confirm("Do you want to quit? (Pressing n will continue the script ignoring this command)", default=True, render = DEFAULT_RENDER):
                sys.exit(exec_code)
            else:
                return

def get_locales():
    with open("/etc/locale.gen", "r") as rf:
        text = rf.read()
    lines = text.splitlines()
    locales = []
    for line in lines:
        line = line.strip()
        if line in ["", "#"] or line.startswith("# "):
            continue
        if line.startswith("#"):
            locales.append(line[1:])
        if not line.startswith("#"):
            locales.append(line)
    locales.sort()
    return locales

def get_blk_types(type):
    output = run_command("lsblk -l -o name,type", get_output = True).strip()
    blks = []
    for line in output.splitlines():
        line = line.strip()
        if line.endswith(type):
            blks.append("/dev/" + line.split()[0].strip())
    blks.sort()
    return blks

def get_disks():
    return get_blk_types("disk")

def get_partitons():
    return get_blk_types("part")

def is_ssd(disk):
    output = run_command(f"lsblk -d -o name,rota {disk}", get_output = True)
    if "not a block device" in output:
        raise Exception("Device not found!")
    rot_value = int(output.splitlines()[1].split()[-1].strip())
    return not rot_value

def get_optional_dependencies(package):
    output = run_command(f"pacman -Qi {package}", get_output = True).strip()
    is_optional_dep = False
    optional_deps = set()
    for line in output.splitlines():
        if line.startswith("Optional Deps"):
            is_optional_dep = True
            package = line[line.index(":")+1:].strip()
            optional_deps.add(package)
            continue
        if is_optional_dep and not line.startswith(" "):
            break
        if is_optional_dep:
            optional_deps.add(line.strip())
    return optional_deps

def get_gpu_types():
    return
