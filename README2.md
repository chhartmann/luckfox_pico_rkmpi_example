This fork is intended to tailor the yolo-rtsp example to my use case.

As I work with macos, the first step is to create an multiarch environment to build locally with UTM and Ubuntu, because the rockchip compiler seems only to be available for x86.
- As there is a bug in Rosetta which prevents working with the latest Ubuntu, 24.04 is recommended.
- For 24.04 the server installation needs to be setup with Rosetta support.
- Transform installation to desktop version via "sudo apt install ubuntu-desktop"
- Edit /etc/apt/sources.list.d/ubuntu.sources and clone the arm64 section there and exchange arm64 with amd64 in the cloned section.
- Add new architecture "sudo dpkg --add-architecture amd64".
- Update package list "sudo apt update"
- Install libc for amd "sudo apt install libc6:amd64"

Changes in this repo:
- Modify build.sh to download rockchip compiler if not already available.
- Remove glibc support.
