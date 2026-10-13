# NavPlotter installer

A web page that installs the NavPlotter firmware on a board straight from the browser, for people who do not want to deal with repositories and compilers. It uses [ESP Web Tools](https://esphome.github.io/esp-web-tools/): Chrome or Edge on a computer, a USB cable, one button per board.

The Raspberry Pi Pico W is not an ESP board: the page offers its `.uf2` file, to be dragged onto the `RPI-RP2` drive.

## Files

- `index.html`: the page, in English and Italian.
- `firmware/<board>.bin`: one image per board, with boot loader, partition table and application merged, written at address 0.
- `firmware/<board>.json`: the manifest ESP Web Tools reads.
- `firmware/versions.json`: the versions shown on the page.
- `tools/build.py`: builds every firmware with PlatformIO from the projects next to this folder and fills `firmware/`.

## Updating

```
python3 tools/build.py
```

## Trying it

Web Serial only works on `https` or on `localhost`:

```
python3 -m http.server 8010 --bind 127.0.0.1
```

then open `http://localhost:8010` in Chrome. To put it on line the folder can be served as it is by any static host, for example GitHub Pages.

## Checked so far

The merged image for the Heltec V2 was written at address 0 with esptool, which is what the page does, and the board started. The page itself has been seen loading, with its buttons; an installation started from the page has not been tried yet.
