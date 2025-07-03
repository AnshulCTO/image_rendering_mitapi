import os
import re
from svgpathtools import svg2paths2


def generate_animated_html(svg_path, output_html_folder):
    svg_filename = os.path.basename(svg_path)
    animate_filename = f"animate_{svg_filename.replace('.svg', '.html')}"
    output_html_path = os.path.join(output_html_folder, animate_filename)

    # Ensure output folder exists
    os.makedirs(output_html_folder, exist_ok=True)

    # Load SVG and clean up paths with empty d=""
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Remove <path d=""> or whitespace only
    svg_content = re.sub(
        r'<path\b[^>]*\bd\s*=\s*["\']\s*["\'][^>]*?>\s*</path\s*>',
        "",
        svg_content,
        flags=re.IGNORECASE,
    )
    svg_content = re.sub(
        r'<path\b[^>]*\bd\s*=\s*["\']\s*["\'][^>]*/?>',
        "",
        svg_content,
        flags=re.IGNORECASE,
    )

    # Save temporary cleaned SVG
    cleaned_svg_path = os.path.join(output_html_folder, "cleaned_temp.svg")
    with open(cleaned_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Parse and calculate path lengths
    paths, attributes, svg_attr = svg2paths2(cleaned_svg_path)
    for i, attr in enumerate(attributes):
        if "d" in attr and attr["d"].strip():
            length = paths[i].length()
            attr["data-length"] = f"{length:.2f}"

    # Rebuild SVG with data-length
    svg_head = f"""<svg xmlns="http://www.w3.org/2000/svg" {" ".join([f'{k}="{v}"' for k, v in svg_attr.items()])}>\n"""
    svg_body = ""
    for attr in attributes:
        if "d" in attr:
            tag = "<path " + " ".join(f'{k}="{v}"' for k, v in attr.items()) + " />"
            svg_body += tag + "\n"
    svg_content = svg_head + svg_body + "</svg>"

    # Build HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SVG Animation</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      width: 100%;
      overflow: hidden;
      background: #fff;
      font-family: sans-serif;
    }}
    .svg-wrapper {{
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    svg {{
      width: 98vw;
      height: 98vh;
      background: white;
    }}
    .controls {{
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      gap: 10px;
      background: rgba(255, 255, 255, 0.9);
      padding: 10px 20px;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      z-index: 10;
    }}
    .controls button {{
      background: none;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: #333;
    }}
    .controls input[type="range"] {{
      width: 150px;
    }}
  </style>
</head>
<body>
<div class="svg-wrapper">
  {svg_content}
</div>
<div class="controls">
  <button id="replayBtn" title="Replay"><i class="fas fa-rotate-right"></i></button>
  <button id="playPauseBtn" title="Play"><i class="fas fa-play"></i></button>
  <button id="backwardBtn" title="Backward 5 Strokes">⏮</button>
  <button id="forwardBtn" title="Forward 5 Strokes">⏭</button>
  <select id="speedSelect" title="Speed">
    <option value="0.5">0.5x</option>
    <option value="1">1.0x</option>
    <option value="2">2.0x</option>
    <option value="3">3.0x</option>
    <option value="5">5.0x</option>
    <option value="10" selected>10.0x</option>
  </select>
  <input type="range" id="progressBar" value="0" min="0" max="100">
</div>
<script>
document.addEventListener("DOMContentLoaded", () => {{
  const paths = document.querySelectorAll("path");
  const playPauseBtn = document.getElementById("playPauseBtn");
  const replayBtn = document.getElementById("replayBtn");
  const progressBar = document.getElementById("progressBar");
  const forwardBtn = document.getElementById("forwardBtn");
  const backwardBtn = document.getElementById("backwardBtn");
  const speedSelect = document.getElementById("speedSelect");

  let isPlaying = false;
  let elapsedTime = 0;
  let animationFrameId;
  let speed = parseFloat(speedSelect.value) || 10.0;

  const pathDelay = 500;
  const totalAnimationDuration = paths.length * pathDelay;

  paths.forEach(path => {{
    const length = parseFloat(path.dataset.length);
    path.style.strokeDasharray = length;
    path.style.strokeDashoffset = length;
    path.style.fillOpacity = 0;
  }});

  function setProgress(progress) {{
    paths.forEach((path, index) => {{
      const length = parseFloat(path.dataset.length);
      const startTime = index * pathDelay;
      const endTime = startTime + pathDelay;
      const time = progress * totalAnimationDuration;

      if (time < startTime) {{
        path.style.strokeDashoffset = length;
        path.style.fillOpacity = 0;
      }} else if (time <= endTime) {{
        const localProgress = (time - startTime) / pathDelay;
        path.style.strokeDashoffset = length * (1 - localProgress);
        path.style.fillOpacity = localProgress;
      }} else {{
        path.style.strokeDashoffset = 0;
        path.style.fillOpacity = 1;
      }}
    }});
  }}

  function setElapsedTime(newTime) {{
    elapsedTime = Math.max(0, Math.min(newTime, totalAnimationDuration));
    setProgress(elapsedTime / totalAnimationDuration);
    progressBar.value = (elapsedTime / totalAnimationDuration) * 100;
  }}

  function playAnimation() {{
    isPlaying = true;
    playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    let startTime = null;

    function animate(currentTime) {{
      if (!startTime) startTime = currentTime - elapsedTime / speed;
      elapsedTime = (currentTime - startTime) * speed;

      const progress = elapsedTime / totalAnimationDuration;
      setProgress(progress);
      progressBar.value = Math.min(progress * 100, 100);

      if (progress < 1 && isPlaying) {{
        animationFrameId = requestAnimationFrame(animate);
      }} else {{
        isPlaying = false;
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        elapsedTime = 0;
      }}
    }}

    animationFrameId = requestAnimationFrame(animate);
  }}

  function pauseAnimation() {{
    isPlaying = false;
    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    cancelAnimationFrame(animationFrameId);
  }}

  playPauseBtn.addEventListener("click", () => {{
    if (isPlaying) pauseAnimation();
    else playAnimation();
  }});

  replayBtn.addEventListener("click", () => {{
    elapsedTime = 0;
    setProgress(0);
    progressBar.value = 0;
    cancelAnimationFrame(animationFrameId);
    playAnimation();
  }});

  progressBar.addEventListener("input", () => {{
    const progress = parseFloat(progressBar.value) / 100;
    elapsedTime = progress * totalAnimationDuration;
    setProgress(progress);
    pauseAnimation();
  }});

  forwardBtn.addEventListener("click", () => {{
    setElapsedTime(elapsedTime + 5 * pathDelay);
  }});

  backwardBtn.addEventListener("click", () => {{
    setElapsedTime(elapsedTime - 5 * pathDelay);
  }});

  speedSelect.addEventListener("change", () => {{
    speed = parseFloat(speedSelect.value);
    if (isPlaying) {{
      pauseAnimation();
      playAnimation();
    }}
  }});
}});
</script>
</body>
</html>"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_html_path
