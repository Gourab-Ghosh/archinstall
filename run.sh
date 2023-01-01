pacman -S archlinux-keyring --noconfirm
pacman -S python-rich python-pip --noconfirm
pip3 install inquirer
export EDITOR=nano
cd archinstall
python3 main.py
