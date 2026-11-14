import { app } from "../../scripts/app.js";

const widgetNames = [
    "plan", "reference_mode", "filename_prefix", "steps", "seed",
    "control_after_generate", "frame_window", "video_denoise",
];

app.registerExtension({
    name: "JSNodes.DigitalHumanWidgets",
    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "DemoInfiniteTalkClips") return;

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            onConfigure?.call(this, info);
            const saved = info.widgets_values_named ?? Object.fromEntries(
                widgetNames.map((name, index) => [name, info.widgets_values?.[index]])
            );
            // Restore by name after ComfyUI restores the positional values.
            for (const widget of this.widgets ?? []) {
                if (widgetNames.includes(widget.name) && saved[widget.name] !== undefined) {
                    widget.value = saved[widget.name];
                }
            }
        };
    },
});
