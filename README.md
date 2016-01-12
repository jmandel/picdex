# picdex: an index. of your pics.

Create a JSON index from JPEG metadata. Incrementally so it should be easy to
run this on a large (and growing) collection of photos. Goal: support a pure
client-side image browser that lets you fly through your whole catalog.

## Use it

```
apt-get install python3
apt-get install exiftool
python3 picdex.py /path/to/photos
```
