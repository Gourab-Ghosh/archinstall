import os, subprocess, time
from GPUtil import getGPUs

def run_command(command, get_output = False):
    if get_output:
        return subprocess.getoutput(command)
    print(f"\nRunning command: {command}\n")
    time.sleep(5)
    os.system(command)

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

def get_disks():
    output = run_command("lsblk -d -o name", get_output = True)
    disks = ["/dev/" + disk.strip() for disk in output.splitlines()[1:]]
    disks.sort()
    return disks

def get_partitons():
    disks = get_disks()
    output = run_command("lsblk -l", get_output = True)
    partitions = []
    for line in output.splitlines()[1:]:
        line = line[:line.index(" ")].strip()
        if line:
            partition = "/dev/" + line
            if partition not in disks:
                partitions.append(partition)
    return partitions

def is_ssd(disk):
    output = run_command(f"lsblk -d -o name,rota {disk}", get_output = True)
    if "not a block device" in output:
        raise Exception("Device not found!")
    rot_value = int(output.splitlines()[1].split()[-1].strip())
    return not rot_value

def get_gpu_types():
    gpu_types = set()
    gpus = getGPUs()
    for gpu in gpus:
        gpu_name = gpu.name.lower()
        for _type in ["amd", "nvidia", "intel"]:
            if _type in gpu_name:
                gpu_types.add(_type.upper())
    gpu_types = sorted(list(gpu_types))
    return gpu_types
