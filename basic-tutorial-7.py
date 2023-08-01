import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# Initialize GStreamer
Gst.init(None)

# Create the elements
audio_source = Gst.ElementFactory.make("audiotestsrc", "audio_source")
tee = Gst.ElementFactory.make("tee", "tee")
audio_queue = Gst.ElementFactory.make("queue", "audio_queue")
audio_convert = Gst.ElementFactory.make("audioconvert", "audio_convert")
audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
video_queue = Gst.ElementFactory.make("queue", "video_queue")
visual = Gst.ElementFactory.make("wavescope", "visual")
video_convert = Gst.ElementFactory.make("videoconvert", "csp")
video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")

# Create the empty pipeline
pipeline = Gst.Pipeline.new("test-pipeline")

if not pipeline or not audio_source or not tee or not audio_queue or not audio_convert or not audio_resample or not audio_sink or not video_queue or not visual or not video_convert or not video_sink:
    print("Not all elements could be created.")
    sys.exit(-1)

# Configure elements
audio_source.set_property("freq", 215.0)
visual.set_property("shader", 0)
visual.set_property("style", 1)

# Link all elements that can be automatically linked because they have "Always" pads
pipeline.add(audio_source)
pipeline.add(tee)
pipeline.add(audio_queue)
pipeline.add(audio_convert)
pipeline.add(audio_resample)
pipeline.add(audio_sink)
pipeline.add(video_queue)
pipeline.add(visual)
pipeline.add(video_convert)
pipeline.add(video_sink)

if not audio_source.link(tee) or not audio_queue.link(audio_convert) or not audio_convert.link(audio_resample) or not audio_resample.link(audio_sink) or not video_queue.link(visual) or not visual.link(video_convert) or not video_convert.link(video_sink):
    print("Elements could not be linked.")
    sys.exit(-1)

# Manually link the Tee, which has "Request" pads
tee_audio_pad = tee.get_request_pad("src_%u")
queue_audio_pad = audio_queue.get_static_pad("sink")
tee_video_pad = tee.get_request_pad("src_%u")
queue_video_pad = video_queue.get_static_pad("sink")
tee_audio_pad.link(queue_audio_pad)
tee_video_pad.link(queue_video_pad)

# Start playing the pipeline
pipeline.set_state(Gst.State.PLAYING)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Free resources
pipeline.set_state(Gst.State.NULL)
