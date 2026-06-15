const releaseApi = "https://api.github.com/repos/Oleksii1221/Ye-ruka/releases/latest";

async function loadLatestRelease() {
  try {
    const response = await fetch(releaseApi, {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!response.ok) return;

    const release = await response.json();
    const installer = release.assets?.find((asset) =>
      /Windows-x64-Setup\.exe$/i.test(asset.name),
    );
    const target = installer?.browser_download_url || release.html_url;

    document.querySelectorAll("[data-download]").forEach((link) => {
      link.href = target;
    });
    document.querySelectorAll("[data-version]").forEach((label) => {
      label.textContent = `Версія ${release.tag_name.replace(/^v/, "")}`;
    });
  } catch {
    // The static fallback remains usable when GitHub API is unavailable.
  }
}

loadLatestRelease();
