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
        self.convert = None
        self.sink = None


# Handler for the pad-added signal
def pad_added_handler(src, new_pad, data):
    # Retrieve our sink pad
    sink_pad = data.convert.get_static_pad("sink")
    print("Received new pad {} from {}".format(new_pad.get_name(), src.get_name()))

    # If our converter is already linked, we have nothing to do here
    if sink_pad.is_linked():
        print("Sink pad from {} is already linked. Ignoring.".format(src.get_name()))
        return

    # Check the new pad's type
    new_pad_type = new_pad.query_caps(None).to_string()
    print(new_pad_type)
    if not new_pad_type.startswith("video/x-raw"):
        print("It has type {} which is not raw video. Ignoring.".format(new_pad_type))
        return

    # Attempt the link
    ret = new_pad.link(sink_pad)
    if ret != Gst.PadLinkReturn.OK:
        print("Linking failed.")
    else:
        print("Linking succeeded.")


def main(args):
    data = CustomData()

    # Create the elements
    data.source = Gst.ElementFactory.make("uridecodebin", "source")
    data.convert = Gst.ElementFactory.make("videoconvert", "convert")
    data.sink = Gst.ElementFactory.make("autovideosink", "sink")

    # Create the empty pipeline
    data.pipeline = Gst.Pipeline.new("test-pipeline")

    if not data.pipeline or not data.source or not data.convert or not data.sink:
        print("Not all elements could be created.")
        return -1

    # Build the pipeline
    data.pipeline.add(data.source)
    data.pipeline.add(data.convert)
    data.pipeline.add(data.sink)

    if not data.convert.link(data.sink):
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
