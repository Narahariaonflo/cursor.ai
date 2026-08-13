"""Minimal UI HTML."""


def render_home_page() -> str:
    """Return the MVP landing page."""
    return """
    <html>
      <head>
        <title>ORCA MVP</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
          }

          input {
            width: 400px;
            padding: 6px;
            margin: 4px 0;
          }

          button {
            padding: 8px 16px;
            cursor: pointer;
            margin-top: 8px;
          }

          #output {
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            white-space: pre-wrap;
          }

          .status {
            margin-top: 15px;
            font-weight: bold;
          }
        </style>
      </head>

      <body>
        <h1>AI Website Health Orchestrator</h1>

        <form id="scan-form">
          <label>
            URL
            <input
              name="target_url"
              type="url"
              value="https://www.onflotech.com/"
              required
            />
          </label>
          <br>

          <label>
            Max pages
            <input
              name="max_pages"
              type="number"
              value="1"
              min="1"
              required
            />
          </label>
          <br>

          <label>
            Max depth
            <input
              name="max_depth"
              type="number"
              value="1"
              min="0"
              required
            />
          </label>
          <br>

          <button type="submit" id="submit-button">
            Create run
          </button>
        </form>

        <div id="status" class="status"></div>
        <pre id="output"></pre>

        <script>
          const form = document.getElementById("scan-form");
          const output = document.getElementById("output");
          const status = document.getElementById("status");
          const submitButton = document.getElementById("submit-button");

          async function getJson(url, options = {}) {
            const response = await fetch(url, options);

            let data;

            try {
              data = await response.json();
            } catch {
              data = {
                error: {
                  message: "Server returned a non-JSON response"
                }
              };
            }

            if (!response.ok) {
              throw new Error(
                data?.error?.message ||
                data?.detail ||
                `Request failed with status ${response.status}`
              );
            }

            return data;
          }

          async function waitForRun(runId) {
            const maxAttempts = 120;

            for (let attempt = 0; attempt < maxAttempts; attempt++) {
              const run = await getJson(
                `/api/v1/analysis-runs/${encodeURIComponent(runId)}`
              );

              output.textContent = JSON.stringify(run, null, 2);

              if (run.report_ready === true) {
                return run;
              }

              if (
                run.state === "failed" ||
                run.state === "error"
              ) {
                throw new Error(
                  `Analysis failed. Current state: ${run.state}`
                );
              }

              status.textContent =
                `Analysis running... (${attempt + 1}/${maxAttempts})`;

              await new Promise(resolve => setTimeout(resolve, 2000));
            }

            throw new Error("Timed out waiting for analysis to finish.");
          }

          form.addEventListener("submit", async (event) => {
            event.preventDefault();

            submitButton.disabled = true;
            status.textContent = "Creating analysis run...";
            output.textContent = "";

            try {
              const body = {
                target_url: form.target_url.value,
                scan_preferences: {
                  max_pages: Number(form.max_pages.value),
                  max_depth: Number(form.max_depth.value)
                }
              };

              const created = await getJson(
                "/api/v1/analysis-runs",
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json"
                  },
                  body: JSON.stringify(body)
                }
              );

              output.textContent =
                JSON.stringify(created, null, 2);

              status.textContent =
                `Run created: ${created.run_id}`;

              const completed = await waitForRun(
                created.run_id
              );

              if (completed.links?.report) {
                const report = await getJson(
                  completed.links.report
                );

                output.textContent =
                  JSON.stringify(report, null, 2);

                status.textContent =
                  "Analysis completed successfully.";
              } else {
                status.textContent =
                  "Analysis completed, but no report link was returned.";
              }

            } catch (error) {
              console.error(error);

              status.textContent = "Request failed.";

              output.textContent = JSON.stringify(
                {
                  error: error.message
                },
                null,
                2
              );
            } finally {
              submitButton.disabled = false;
            }
          });
        </script>
      </body>
    </html>
    """