"""
app.py - Cartoonization Machine
CIS450 Final Project - Brec Feehan
A Flask web app that applies a cartoon effect to uploaded images using OpenCV. The app displays the before and after (side by side)
and allows users to adjust parameters like edge strength, color smoothness, palette size, and detail boost to customize the effect. Users can also download the cartoonized image. 
The app is designed to be simple and intuitive, with a clean UI and responsive design.

AI Usage: Claude was used to brainstorm ideas and assist in the researching process. Codex was used to help make the final code more efficient and clean, and to help with debugging. 
The HTML and CSS were written by hand, but I used Codex to help optimize the Python code and make it more concise.
I also used Codex to help with the image processing logic, particularly the posterization step which was a bit tricky to implement efficiently. 
Overall, the AI tools were a helpful aid in the development process, but the core ideas and implementation were my own work.

Build instructions:
    docker build -t app .
    docker run -p 8080:8080 -e PORT=8080 app
"""

from flask import Flask, render_template_string, request
import os
import socket
import uuid

import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")

hostname = socket.gethostname()
os.makedirs(STATIC_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "edge_strength": 9,
    "color_smoothness": 6,
    "palette_size": 10,
    "detail_boost": 7,
}

UI_RANGE = (1, 10)
INTERNAL_RANGES = {
    "edge_strength": (3, 12),
    "color_smoothness": (2, 10),
    "palette_size": (4, 18),
    "detail_boost": (1, 10),
}

HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cartoonization Machine</title>
    <style>
        :root {
            --bg: #f3f1ed;
            --panel: #fbfaf8;
            --panel-strong: #ffffff;
            --ink: #1f1f1c;
            --muted: #73716b;
            --accent: #2f2f2b;
            --accent-soft: #d8d4cd;
            --track: #dfdcd5;
            --border: #e5e1da;
            --shadow: 0 18px 42px rgba(31, 31, 28, 0.06);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: "SF Pro Display", "Avenir Next", "Helvetica Neue", sans-serif;
            color: var(--ink);
            background:
                linear-gradient(180deg, #f7f5f1 0%, #f1efea 100%);
        }

        .page-shell {
            width: min(980px, calc(100vw - 32px));
            margin: 0 auto;
            padding: 40px 0 56px;
        }

        .editor-shell,
        .results-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 28px;
            box-shadow: var(--shadow);
        }

        .editor-shell {
            padding: 32px;
        }

        .site-header {
            margin-bottom: 28px;
        }

        h1 {
            margin: 0;
            font-size: clamp(2rem, 4vw, 2.7rem);
            line-height: 1;
            letter-spacing: -0.05em;
            font-weight: 700;
        }

        .subtitle {
            margin: 10px 0 0;
            color: var(--muted);
            line-height: 1.6;
            font-size: 0.98rem;
        }

        form {
            display: grid;
            gap: 24px;
        }

        .upload-zone {
            padding: 24px;
            border-radius: 24px;
            background: var(--panel-strong);
            border: 1px solid var(--border);
        }

        .section-title {
            margin: 0 0 6px;
            font-size: 0.94rem;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        .section-copy {
            margin: 0 0 16px;
            color: var(--muted);
            line-height: 1.5;
            font-size: 0.94rem;
        }

        .upload-zone input[type="file"] {
            width: 100%;
            padding: 14px;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: #f6f4f0;
            color: var(--ink);
        }

        .controls-grid {
            display: grid;
            gap: 14px;
        }

        .slider-row {
            padding: 18px 20px;
            border-radius: 22px;
            background: var(--panel-strong);
            border: 1px solid var(--border);
        }

        .slider-meta {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 6px;
        }

        .slider-meta label {
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        .slider-value {
            font-weight: 700;
            color: var(--accent);
            min-width: 34px;
            text-align: right;
        }

        .slider-row p {
            margin: 0 0 14px;
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .slider-shell {
            display: grid;
            gap: 8px;
        }

        .slider-range {
            display: flex;
            justify-content: space-between;
            color: var(--muted);
            font-size: 0.82rem;
            font-variant-numeric: tabular-nums;
        }

        input[type="range"] {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 4px;
            border-radius: 999px;
            background: linear-gradient(90deg, #d9d5ce 0%, #c8c3bb 100%);
            outline: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ffffff;
            border: 1px solid rgba(31, 31, 28, 0.12);
            box-shadow: 0 3px 10px rgba(31, 31, 28, 0.16);
            cursor: pointer;
        }

        input[type="range"]::-moz-range-track {
            height: 4px;
            border-radius: 999px;
            background: linear-gradient(90deg, #d9d5ce 0%, #c8c3bb 100%);
        }

        input[type="range"]::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ffffff;
            border: 1px solid rgba(31, 31, 28, 0.12);
            box-shadow: 0 3px 10px rgba(31, 31, 28, 0.16);
            cursor: pointer;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 4px;
        }

        button,
        .ghost-link {
            appearance: none;
            border-radius: 999px;
            padding: 14px 22px;
            font: inherit;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: transform 180ms ease, background 180ms ease, border-color 180ms ease;
        }

        button {
            border: 1px solid var(--accent);
            background: var(--accent);
            color: white;
        }

        button:hover,
        .ghost-link:hover {
            transform: translateY(-1px);
        }

        .ghost-link {
            border: 1px solid var(--border);
            background: #f6f4f0;
            color: var(--ink);
        }

        .results-card {
            margin-top: 20px;
            padding: 28px;
            display: grid;
            gap: 18px;
        }

        .results-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .results-card h2 {
            margin: 0;
            font-size: 1.1rem;
            letter-spacing: -0.02em;
        }

        .results-copy {
            margin: 6px 0 0;
            color: var(--muted);
            line-height: 1.5;
            font-size: 0.93rem;
        }

        .results-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }

        .image-card {
            padding: 18px;
            border-radius: 22px;
            background: var(--panel-strong);
            border: 1px solid var(--border);
        }

        .image-card h3 {
            margin: 0 0 12px;
            font-size: 1rem;
        }

        .image-frame {
            border-radius: 18px;
            overflow: hidden;
            background: #f5f3ee;
            border: 1px solid #ece8e0;
        }

        .image-frame img {
            display: block;
            width: 100%;
            height: min(42vw, 460px);
            object-fit: contain;
            background: white;
        }

        .empty-state {
            display: grid;
            place-items: center;
            min-height: 420px;
            padding: 32px;
            border-radius: 24px;
            border: 1px dashed #d7d2ca;
            background: #f8f6f2;
            text-align: center;
            color: var(--muted);
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .chip-row span {
            padding: 9px 12px;
            border-radius: 999px;
            background: #f4f1eb;
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 600;
        }

        @media (max-width: 980px) {
            .results-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <main class="page-shell">
        <section class="editor-shell">
            <header class="site-header">
                <h1>Cartoonization Machine</h1>
                <p class="subtitle">Upload a photo (JPG or PNG), slide to desired effect, and view output below!</p>
            </header>

            <section>
                <form method="POST" action="/cartoonize" enctype="multipart/form-data">
                    <div class="upload-zone">
                        <h2 class="section-title">Choose Photo</h2>
                        <p class="section-copy">Select a JPG or PNG. If you leave this empty, the app keeps using your most recent image so you can keep adjusting the effect.</p>
                        <input id="file" type="file" name="file" accept=".jpg,.jpeg,.png,.webp">
                    </div>

                    <div class="controls-grid">
                        <div class="slider-row">
                            <div class="slider-meta">
                                <label for="edge_strength">Edge strength</label>
                                <span class="slider-value" data-output="edge_strength">{{ ui_settings.edge_strength }}</span>
                            </div>
                            <p>Controls how strongly the outlines are carved into the image.</p>
                            <div class="slider-shell">
                                <input id="edge_strength" name="edge_strength" type="range" min="1" max="10" value="{{ ui_settings.edge_strength }}">
                                <div class="slider-range">
                                    <span>1</span>
                                    <span>10</span>
                                </div>
                            </div>
                        </div>

                        <div class="slider-row">
                            <div class="slider-meta">
                                <label for="color_smoothness">Color smoothness</label>
                                <span class="slider-value" data-output="color_smoothness">{{ ui_settings.color_smoothness }}</span>
                            </div>
                            <p>Higher values smooth textures into cleaner painted surfaces.</p>
                            <div class="slider-shell">
                                <input id="color_smoothness" name="color_smoothness" type="range" min="1" max="10" value="{{ ui_settings.color_smoothness }}">
                                <div class="slider-range">
                                    <span>1</span>
                                    <span>10</span>
                                </div>
                            </div>
                        </div>

                        <div class="slider-row">
                            <div class="slider-meta">
                                <label for="palette_size">Palette size</label>
                                <span class="slider-value" data-output="palette_size">{{ ui_settings.palette_size }}</span>
                            </div>
                            <p>Lower values create flatter posterized color blocks.</p>
                            <div class="slider-shell">
                                <input id="palette_size" name="palette_size" type="range" min="1" max="10" value="{{ ui_settings.palette_size }}">
                                <div class="slider-range">
                                    <span>1</span>
                                    <span>10</span>
                                </div>
                            </div>
                        </div>

                        <div class="slider-row">
                            <div class="slider-meta">
                                <label for="detail_boost">Detail boost</label>
                                <span class="slider-value" data-output="detail_boost">{{ ui_settings.detail_boost }}</span>
                            </div>
                            <p>Balances local contrast so the result stays crisp without feeling harsh.</p>
                            <div class="slider-shell">
                                <input id="detail_boost" name="detail_boost" type="range" min="1" max="10" value="{{ ui_settings.detail_boost }}">
                                <div class="slider-range">
                                    <span>1</span>
                                    <span>10</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="actions">
                        <button type="submit">Render Cartoon Effect</button>
                        {% if processed %}
                        <a class="ghost-link" href="{{ processed }}" download="cartoon-output.jpg">Download Output</a>
                        {% endif %}
                    </div>
                </form>
            </section>
        </section>

        <section class="results-card">
            <div class="results-head">
                <div>
                    <h2>Before & After</h2>
                    <p class="results-copy">Compare the original image with the current cartoon effect output.</p>
                </div>
                <div class="chip-row">
                    <span>Edges {{ ui_settings.edge_strength }}</span>
                    <span>Smoothness {{ ui_settings.color_smoothness }}</span>
                    <span>Palette {{ ui_settings.palette_size }}</span>
                    <span>Detail {{ ui_settings.detail_boost }}</span>
                </div>
            </div>

            {% if original and processed %}
            <div class="results-grid">
                <article class="image-card">
                    <h3>Original</h3>
                    <div class="image-frame">
                        <img src="{{ original }}" alt="Original upload">
                    </div>
                </article>

                <article class="image-card">
                    <h3>Cartoonized</h3>
                    <div class="image-frame">
                        <img src="{{ processed }}" alt="Cartoonized image">
                    </div>
                </article>
            </div>
            {% else %}
            <div class="empty-state">
                <div>
                    <h3>No render yet</h3>
                    <p>Upload a photo and run the processor to see the before and after here.</p>
                </div>
            </div>
            {% endif %}
        </section>
    </main>

    <script>
        // Update slider value display in real time as user drags
        document.querySelectorAll('input[type="range"]').forEach((input) => {
            const output = document.querySelector(`[data-output="${input.name}"]`);
            if (!output) return;
            input.addEventListener("input", () => {
                output.textContent = input.value;
            });
        });
    </script>
</body>
</html>
"""


def _odd_kernel(value, minimum=3):
    """Ensures kernel size is odd and meets minimum value. OpenCV requires odd kernel sizes."""
    value = max(minimum, int(value))
    return value if value % 2 == 1 else value + 1


def _posterize(image, palette_size):
    """Reduces image to a limited color palette using k-means clustering for a flat cartoon look."""
    pixel_data = image.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 18, 0.8)
    _, labels, centers = cv2.kmeans(
        pixel_data,
        int(palette_size),
        None,
        criteria,
        4,
        cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(centers)
    return centers[labels.flatten()].reshape(image.shape)


def create_cartoon(input_path, output_path, settings):
    """
    Applies the full cartoon effect pipeline to an image.
    Steps: grayscale conversion, edge detection, bilateral filtering,
    color posterization, detail enhancement, and bitwise combination.
    """
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError("Could not read uploaded image.")

    edge_strength = int(settings["edge_strength"])
    color_smoothness = int(settings["color_smoothness"])
    palette_size = int(settings["palette_size"])
    detail_boost = int(settings["detail_boost"])

    # Convert to grayscale for edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Blur to reduce noise before detecting edges
    gray = cv2.medianBlur(gray, _odd_kernel(detail_boost))

    block_size = max(3, edge_strength * 2 + 1)
    if block_size % 2 == 0:
        block_size += 1

    # Detect edges and create bold outline mask
    edge_mask = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        block_size,
        detail_boost,
    )
    # Smooth colors while preserving edges
    smoothed = image.copy()
    for _ in range(max(1, color_smoothness // 2)):
        smoothed = cv2.bilateralFilter(
            smoothed,
            d=9,
            sigmaColor=40 + color_smoothness * 8,
            sigmaSpace=30 + color_smoothness * 6,
        )
 
    # Reduce color palette for flat cartoon look
    posterized = _posterize(smoothed, palette_size)
    
    # Enhance local detail contrast
    sharpened = cv2.detailEnhance(
        posterized,
        sigma_s=10 + detail_boost * 2,
        sigma_r=max(0.05, min(0.6, 0.12 + detail_boost * 0.03)),
    )
    # Combine color image with edge mask to produce final cartoon
    cartoon = cv2.bitwise_and(sharpened, sharpened, mask=edge_mask)
    # Save result as high quality JPEG
    cv2.imwrite(output_path, cartoon, [int(cv2.IMWRITE_JPEG_QUALITY), 95])


def _map_value(value, source_range, target_range):
    """Maps a value from one range to another. Used to convert between UI slider values and internal OpenCV ranges."""
    source_min, source_max = source_range
    target_min, target_max = target_range
    if source_max == source_min:
        return target_min

    clamped = max(source_min, min(source_max, int(value)))
    ratio = (clamped - source_min) / (source_max - source_min)
    mapped = target_min + ratio * (target_max - target_min)
    return int(round(mapped))


def to_ui_settings(settings):
    """Converts internal settings back to 1-10 UI range for display in the sliders."""
    ui_settings = {}
    for key, value in settings.items():
        ui_settings[key] = _map_value(value, INTERNAL_RANGES[key], UI_RANGE)
    return ui_settings


def get_settings(form_data):
    """Reads slider values from submitted form data and maps them to internal OpenCV ranges."""
    settings = {}
    for key, default in DEFAULT_SETTINGS.items():
        ui_default = _map_value(default, INTERNAL_RANGES[key], UI_RANGE)
        ui_value = form_data.get(key, default=ui_default, type=int)
        settings[key] = _map_value(ui_value, UI_RANGE, INTERNAL_RANGES[key])
    return settings


def build_image_paths():
    """Generates file paths for saving images. Adds a random token to URLs to prevent browser caching."""
    token = uuid.uuid4().hex[:8]
    return (
        os.path.join(STATIC_DIR, "original.jpg"),
        os.path.join(STATIC_DIR, "output.jpg"),
        f"/static/original.jpg?v={token}",
        f"/static/output.jpg?v={token}",
    )


@app.route("/")
def home():
    """Renders the home page with default settings. Shows existing images if available."""
    original_exists = os.path.exists(os.path.join(STATIC_DIR, "original.jpg"))
    output_exists = os.path.exists(os.path.join(STATIC_DIR, "output.jpg"))
    ui_settings = to_ui_settings(DEFAULT_SETTINGS)
    return render_template_string(
        HTML,
        hostname=hostname,
        settings=DEFAULT_SETTINGS,
        ui_settings=ui_settings,
        original="/static/original.jpg" if original_exists else None,
        processed="/static/output.jpg" if output_exists else None,
    )


@app.route("/cartoonize", methods=["POST"])
def cartoonize():
    """Handles form submission, saves uploaded image, runs cartoon pipeline, and returns updated page."""
    settings = get_settings(request.form)
    ui_settings = to_ui_settings(settings)
    file = request.files.get("file")
    original_path, output_path, original_url, output_url = build_image_paths()

    if file and file.filename:
        file.save(original_path)

    if not os.path.exists(original_path):
        return render_template_string(
            HTML,
            hostname=hostname,
            settings=settings,
            ui_settings=ui_settings,
            original=None,
            processed=None,
        )

    create_cartoon(original_path, output_path, settings)

    return render_template_string(
        HTML,
        hostname=hostname,
        settings=settings,
        ui_settings=ui_settings,
        original=original_url,
        processed=output_url,
    )
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port)
