import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# 初始化 GStreamer
Gst.init(None)

# 创建元素
element = Gst.ElementFactory.make("webrtcbin", "unique_element_name")

print(element)

# 或者使用元素工厂来创建元素
# factory = Gst.ElementFactory.find("factory_name")
# element = factory.create("unique_element_name")

# 在这里继续编写你的 GStreamer 代码
# 例如构建 pipeline，连接元素等
