Windows Subsystem for Linux Install
===================================

Microsoft has instructions for installing [WSL](https://learn.microsoft.com/en-us/windows/wsl/install), but on most systems, this simply involves running `wsl --install` from *PowerShell* (not `cmd`).

Once installed, run:

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-virtualenvwrapper git
```