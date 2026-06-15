const releaseApi = "https://api.github.com/repos/Oleksii1221/Ye-ruka/releases/latest";

async function loadLatestRelease() {
  try {
    const response = await fetch(releaseApi, {
      headers: { Accept: "application/vnd.github+json" },
    });
    if (!response.ok) return;

    const release = await response.json();
    const windowsInstaller = release.assets?.find((asset) =>
      /Windows-x64-Setup\.exe$/i.test(asset.name),
    );
    const ubuntuArchive = release.assets?.find((asset) =>
      /Ubuntu-x64\.tar\.gz$/i.test(asset.name),
    );
    const windowsTarget = windowsInstaller?.browser_download_url || release.html_url;
    const ubuntuTarget = ubuntuArchive?.browser_download_url || release.html_url;

    document.querySelectorAll("[data-download='windows']").forEach((link) => {
      link.href = windowsTarget;
    });
    document.querySelectorAll("[data-download='ubuntu']").forEach((link) => {
      link.href = ubuntuTarget;
    });
    document.querySelectorAll("[data-version]").forEach((label) => {
      label.textContent = `Версія ${release.tag_name.replace(/^v/, "")}`;
    });
  } catch {
    // The static fallback remains usable when GitHub API is unavailable.
  }
}

loadLatestRelease();
