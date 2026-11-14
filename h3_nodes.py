from comfy_api.latest import io


RESOLUTIONS = {
    "320": (576, 320),
    "480": (864, 480),
    "720": (1280, 736),
    "1080": (1920, 1088),
}
DELIVERY_SIZES = {
    "320": (568, 320),
    "480": (854, 480),
    "720": (1280, 720),
    "1080": (1920, 1080),
}
ORIENTATIONS = ["横屏", "竖屏"]


def oriented(size, orientation):
    return size[::-1] if orientation == "竖屏" else size


class H3VideoPreset(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="H3VideoPreset",
            display_name="H3 尺寸与时长",
            category="H3/中文工具",
            description="选择画质、横竖屏和时长，输出H3可用的32像素对齐尺寸与24fps帧数。720档实际为1280×736，1080档为1920×1088，可在成片后裁切。",
            inputs=[
                io.Combo.Input("resolution", options=[*RESOLUTIONS, "352（旧预览）"], default="480", display_name="分辨率"),
                io.Combo.Input("orientation", options=ORIENTATIONS, default="横屏", display_name="画面方向"),
                io.Combo.Input("duration", options=["5秒", "10秒", "15秒"], default="5秒", display_name="时长"),
            ],
            outputs=[
                io.Int.Output("width", display_name="宽度 width"),
                io.Int.Output("height", display_name="高度 height"),
                io.Int.Output("length", display_name="帧数 length"),
                io.Float.Output("seconds", display_name="设定秒数 duration"),
                io.String.Output("info", display_name="参数说明"),
            ],
        )

    @classmethod
    def execute(cls, resolution, orientation, duration):
        size = (608, 352) if resolution == "352（旧预览）" else RESOLUTIONS[resolution]
        width, height = oriented(size, orientation)
        seconds = {"5秒": 5, "10秒": 10, "15秒": 15}[duration]
        # H3 uses 24fps and frame counts of 17k+5; align upward like H3 Extender.
        frames = ((seconds * 24 - 5 + 16) // 17) * 17 + 5
        info = f"{width}×{height} | 24fps | {frames}帧 | 实际{frames / 24:.3f}秒；width/height接宽高，length接帧数，duration接秒数。"
        return io.NodeOutput(width, height, frames, float(seconds), info)


class H3LongVideoSize(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="H3LongVideoSize",
            display_name="H3 长视频画幅",
            category="H3/中文工具",
            inputs=[
                io.Combo.Input("resolution", options=list(RESOLUTIONS), default="720", display_name="分辨率"),
                io.Combo.Input("orientation", options=ORIENTATIONS, default="横屏", display_name="画面方向"),
            ],
            outputs=[
                io.Int.Output("width", display_name="生成宽度"),
                io.Int.Output("height", display_name="生成高度"),
                io.Int.Output("delivery_width", display_name="成片宽度"),
                io.Int.Output("delivery_height", display_name="成片高度"),
            ],
        )

    @classmethod
    def execute(cls, resolution, orientation):
        return io.NodeOutput(*oriented(RESOLUTIONS[resolution], orientation),
                             *oriented(DELIVERY_SIZES[resolution], orientation))


class H3CenterCropVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="H3CenterCropVideo",
            display_name="H3 成片居中裁切",
            category="H3/中文工具",
            inputs=[
                io.Video.Input("video"),
                io.Int.Input("width", default=1280, min=2, force_input=True),
                io.Int.Input("height", default=720, min=2, force_input=True),
            ],
            outputs=[io.Video.Output()],
        )

    @classmethod
    def execute(cls, video, width, height):
        source_width, source_height = video.get_dimensions()
        if width > source_width or height > source_height:
            raise ValueError(f"目标 {width}×{height} 超过视频 {source_width}×{source_height}。")
        if (width, height) == (source_width, source_height):
            return io.NodeOutput(video)
        return io.NodeOutput(video.as_cropped(
            (source_width - width) // 2, (source_height - height) // 2, width, height
        ))
