import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

def print_field(field, value, pfx):
    # some gstreamer types such as GstValueList, GstFraction... can not be serialize in python.
    # there may appears error like 'TypeError: unknown type GstValueList'
    str = Gst.value_serialize(value)
    print('%s  %15s: %s' % (pfx, GLib.quark_to_string(field), str))
    return True

def print_caps(caps, pfx):
    if caps is None:
        print('%sNONE' % pfx)
        return
    if caps.is_any():
        print('%sANY' % pfx)
        return
    if caps.is_empty():
        print('%sEMPTY' % pfx)
        return

    for i in range(caps.get_size()):
        structure = caps.get_structure(i)
        print('%s%s' % (pfx, structure.get_name()))
        structure.foreach(print_field, pfx)

def print_pad_templates_information(factory):
    print('Pad Templates for %s:' % factory.get_metadata('long-name'))
    if factory.get_num_pad_templates() == 0:
        print('  none')
        return

    pads = factory.get_static_pad_templates()
    for padtemplate in pads:
        if padtemplate.direction == Gst.PadDirection.SRC:
            print("  SRC template: '%s'" % padtemplate.name_template)
        elif padtemplate.direction == Gst.PadDirection.SINK:
            print("  SINK template: '%s'" % padtemplate.name_template)
        else:
            print("  UNKNOWN!!! template: '%s'" % padtemplate.name_template)

        if padtemplate.presence == Gst.PadPresence.ALWAYS:
            print("    Availability: Always")
        elif padtemplate.presence == Gst.PadPresence.SOMETIMES:
            print("    Availability: Sometimes")
        elif padtemplate.presence == Gst.PadPresence.REQUEST:
            print("    Availability: On request")
        else:
            print("    Availability: UNKNOWN!!!")

        if padtemplate.static_caps.string is not None:
            print("    Capabilities:")
            caps = padtemplate.get_caps()
            print_caps(caps, "      ")

def print_pad_capabilities(element, pad_name):
    pad = element.get_static_pad(pad_name)
    if not pad:
        print("Could not retrieve pad '%s'" % pad_name)
        return

    caps = pad.get_current_caps()
    if not caps:
        caps = pad.query_caps(None)

    print("Caps for the %s pad:" % pad_name)
    print_caps(caps, "      ")

def main():
    Gst.init(None)

    source_factory = Gst.ElementFactory.find("videotestsrc")
    sink_factory = Gst.ElementFactory.find("autovideosink")
    if not source_factory or not sink_factory:
        print("Not all element factories could be created.")
        return -1

    print_pad_templates_information(source_factory)
    print_pad_templates_information(sink_factory)

    source = source_factory.create("source")
    sink = sink_factory.create("sink")

    pipeline = Gst.Pipeline.new("test-pipeline")

    if not pipeline or not source or not sink:
        print("Not all elements could be created.")
        return -1

    pipeline.add(source)
    pipeline.add(sink)
    if not Gst.Element.link(source, sink):
        print("Elements could not be linked.")
        return -1

    print("In NULL state:")
    print_pad_capabilities(sink, "sink")

    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    bus = pipeline.get_bus()

    terminate = False
    while not terminate:
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.STATE_CHANGED)

        if msg:
            if msg.type == Gst.MessageType.ERROR:
                err, debug_info = msg.parse_error()
                print("Error received from element %s: %s" % (msg.src.get_name(), err.message))
                print("Debugging information: %s" % (debug_info if debug_info else "none"))
                terminate = True
            elif msg.type == Gst.MessageType.EOS:
                print("End-Of-Stream reached.")
                terminate = True
            elif msg.type == Gst.MessageType.STATE_CHANGED:
                if msg.src == pipeline:
                    old_state, new_state, pending_state = msg.parse_state_changed()
                    print("\nPipeline state changed from %s to %s:" % (Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))
                    print_pad_capabilities(sink, "sink")

    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()
