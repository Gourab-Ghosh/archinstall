# Arch Linux Installation Script

## Overview

This Arch Linux Installation Script is a comprehensive Python-based utility designed to automate the installation and configuration of Arch Linux systems. It supports a variety of filesystems, desktop environments, and additional packages, catering to a customized and efficient setup process.

## Features

- **Filesystem Support**: Handles BTRFS and EXT4 filesystem setups with options for swap files or swap partitions.
- **GPU Compatibility**: Provides configurations for NVIDIA, AMD, and Intel GPUs.
- **Desktop Environment Installation**: Supports multiple environments such as KDE, GNOME, i3, and others.
- **Package Management**: Integrates with both official Arch repositories and external repositories like Chaotic AUR and Blackarch for extensive software availability.
- **Customizability**: Extensive customization through a configuration file and interactive prompts to specify partitions, user details, and additional services.
- **Post-Installation Configuration**: Sets up system locales, timezones, hostname, and initiates essential services.

## Requirements

Ensure that your system meets the following requirements:
- Python 3.x
- The Python packages listed in `requirements.txt`, notably `rich` and `python-inquirer`.

## Installation

1. **Clone the Repository**:
   Download the scripts directly into your local machine where you plan to install Arch Linux.

2. **Prepare the Environment**:
   Run the following command to install necessary Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Installation Script**:
   Navigate to the directory containing the script and execute:
   ```bash
   python main.py
   ```
   Follow the interactive prompts to configure and start the installation.

## Configuration

Edit `config.py` to toggle between testing and deployment modes:
- `IS_TESTING`: Set to `True` for a dry run without making any system changes.
- `ADD_OPTIONAL_PACKAGES`: Enable or disable the installation of optional packages.

## Usage

The script operates through a series of interactive prompts to guide the user through setting up the installation parameters:
- Partitioning: Choose or create partitions for boot, root, and home.
- Filesystem: Select between BTRFS and EXT4, configure swap options.
- Desktop Environment: Choose the preferred GUI, like KDE or GNOME.
- Additional Software: Select from a wide range of additional software and drivers.

After configuring through the prompts, the script automates the following:
- Formats and mounts partitions.
- Installs the base system plus selected software.
- Configures system settings like hostname, timezone, and locale.
- Sets up users and passwords.

## Advanced Configuration

For advanced users, the script supports modifications such as adding new package repositories, customizing kernel options, and enabling/disabling specific systemd services post-installation.

## Contributing

Contributions to the script are welcome. Please ensure to test changes in a controlled environment before submitting a pull request.

## Acknowledgments

Thanks to the Arch Linux community for their extensive documentation and support which greatly aided in the creation of this script.
