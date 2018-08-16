
import pip
pkgs = [p.key for p in pip.get_installed_distributions()]
for pkg in pkgs:
    pip.main(['install', '--upgrade', pkg])