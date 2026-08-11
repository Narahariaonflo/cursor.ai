"""Minimal UI HTML."""


def render_home_page() -> str:
    """Return the MVP landing page."""
    return """
    <html>
      <head><title>ORCA MVP</title></head>
      <body>
        <h1>AI Website Health Orchestrator</h1>
        <form id="scan-form">
          <label>URL <input name="target_url" value="https://example.com" /></label><br>
          <label>Max pages <input name="max_pages" type="number" value="1" /></label><br>
          <label>Max depth <input name="max_depth" type="number" value="1" /></label><br>
          <button type="submit">Create run</button>
        </form>
        <pre id="output"></pre>
        <script>
          const form = document.getElementById("scan-form");
          form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const body = {
              target_url: form.target_url.value,
              max_pages: Number(form.max_pages.value),
              max_depth: Number(form.max_depth.value)
            };
            const created = await fetch("/api/runs", {
              method: "POST",
              headers: {"Content-Type": "application/json"},
              body: JSON.stringify(body)
            }).then((r) => r.json());
            const published = await fetch(`/api/runs/${created.run_id}/publish`, {
              method: "POST"
            }).then((r) => r.json());
            document.getElementById("output").textContent =
              JSON.stringify({created, published}, null, 2);
          });
        </script>
      </body>
    </html>
    """
