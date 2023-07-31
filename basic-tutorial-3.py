import sys

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


# Initialize GStreamer
Gst.init(None)


class CustomData:
    def __init__(self):
        self.pipeline = None
        self.source = None
        self.videoconvert = None
        self.audioconvert = None
        self.resample = None
        self.videosink = None
        self.audiosink = None


# Handler for the pad-added signal
def pad_added_handler(src, new_pad, data: CustomData):
    # Retrieve our sink pad
    video_sink_pad = data.videoconvert.get_static_pad("sink")
    audio_sink_pad = data.audioconvert.get_static_pad("sink")
    print("Received new pad {} from {}".format(new_pad.get_name(), src.get_name()))

    # # If our converter is already linked, we have nothing to do here
    # if video_sink_pad.is_linked():
    #     print("Sink pad from {} is already linked. Ignoring.".format(src.get_name()))
    #     return

    # if audio_sink_pad.is_linked():
    #     print("Sink pad from {} is already linked. Ignoring.".format(src.get_name()))
    #     return

    new_pad_type = new_pad.query_caps(None).to_string()
    print(new_pad_type)
    ret = None
    if new_pad_type.startswith("video/x-raw"):
        ret = new_pad.link(video_sink_pad)
    elif new_pad_type.startswith("audio/x-raw"):
        ret = new_pad.link(audio_sink_pad)
    else:
        print("unknown pad type")
        return

    if ret != Gst.PadLinkReturn.OK:
        print("Linking failed.")
    else:
        print("Linking succeeded.")


def main(args):
    data = CustomData()

    # Create the elements
    data.source = Gst.ElementFactory.make("uridecodebin", "source")

    data.videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
    data.audioconvert = Gst.ElementFactory.make("audioconvert", "audioconvert")

    data.resample = Gst.ElementFactory.make("audioresample", "resample")

    data.videosink = Gst.ElementFactory.make("autovideosink", "videosink")
    data.audiosink = Gst.ElementFactory.make("autoaudiosink", "audiosink")

    # Create the empty pipeline
    data.pipeline = Gst.Pipeline.new("test-pipeline")

    if not data.pipeline or not data.source or not data.videoconvert or not data.audioconvert \
        or not data.resample or not data.videosink or not data.audiosink:
        print("Not all elements could be created.")
        return -1

    # Build the pipeline
    data.pipeline.add(data.source)
    data.pipeline.add(data.videoconvert)
    data.pipeline.add(data.audioconvert)
    data.pipeline.add(data.resample)
    data.pipeline.add(data.videosink)
    data.pipeline.add(data.audiosink)

    if not data.videoconvert.link(data.videosink):
        print("Elements could not be linked.")
        return -1

    if not data.audioconvert.link(data.resample) or not data.resample.link(data.audiosink):
        print("Elements could not be linked.")
        return -1

    # Set the URI to play
    data.source.set_property("uri", "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")

    # Connect to the pad-added signal
    data.source.connect("pad-added", pad_added_handler, data)

    # Start playing
    ret = data.pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    # Wait until error or EOS
    bus = data.pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # Parse message
    if msg:
        if msg.type == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print("Error received from element %s: %s" % (msg.src.get_name(), err))
            print("Debugging information: %s" % debug)
        elif msg.type == Gst.MessageType.EOS:
            print("End-Of-Stream reached.")
        else:
            # This should not happen. We only want error and EOS.
            print("Unexpected message received.")

    # Free resources
    data.pipeline.set_state(Gst.State.NULL)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
