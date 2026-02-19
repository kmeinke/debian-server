# CIS 2.2.x — Remove unwanted client packages

unwanted_client_packages:
  pkg.purged:
    - pkgs:
      - nis
      - rsh-client
      - talk
      - telnet
      - ldap-utils
      - ftp
      - strace

# GUI / desktop — task meta-packages
unwanted_desktop_tasks:
  pkg.purged:
    - pkgs:
      - task-desktop
      - task-gnome-desktop
      - task-gnome-flashback-desktop
      - task-kde-desktop
      - task-xfce-desktop
      - task-lxde-desktop
      - task-lxqt-desktop
      - task-cinnamon-desktop
      - task-mate-desktop

# X.org / X11
unwanted_xorg:
  pkg.purged:
    - pkgs:
      - xorg
      - xserver-xorg
      - xserver-xorg-core
      - xserver-xorg-input-all
      - xserver-xorg-video-all
      - x11-common
      - desktop-base

# Display managers
unwanted_display_managers:
  pkg.purged:
    - pkgs:
      - gdm3
      - sddm
      - lightdm
      - xdm
      - lxdm
      - slim

# Desktop-pulled services (also CIS 2.2.x items)
unwanted_desktop_services:
  pkg.purged:
    - pkgs:
      - avahi-daemon
      - cups
      - cups-browsed

# Audio
unwanted_audio:
  pkg.purged:
    - pkgs:
      - pulseaudio
      - pipewire
      - pipewire-pulse
      - wireplumber
      - alsa-utils
      - alsa-base

# Bluetooth
unwanted_bluetooth:
  pkg.purged:
    - pkgs:
      - bluetooth
      - bluez
      - blueman
