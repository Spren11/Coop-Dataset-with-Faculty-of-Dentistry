document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("uploadForm");
    const fileInput = document.getElementById("fileInput");
    const previewContainer = document.getElementById("preview");
    const resultsContainer = document.getElementById("results");
    const fullscreenOverlay = document.createElement("div");

    // Fullscreen overlay
    fullscreenOverlay.id = "fullscreenOverlay";
    fullscreenOverlay.style.position = "fixed";
    fullscreenOverlay.style.top = "0";
    fullscreenOverlay.style.left = "0";
    fullscreenOverlay.style.width = "100%";
    fullscreenOverlay.style.height = "100%";
    fullscreenOverlay.style.backgroundColor = "rgba(0, 0, 0, 0.8)";
    fullscreenOverlay.style.display = "none";
    fullscreenOverlay.style.justifyContent = "center";
    fullscreenOverlay.style.alignItems = "center";
    fullscreenOverlay.style.zIndex = "9999";
    fullscreenOverlay.addEventListener("click", () => {
        fullscreenOverlay.style.display = "none";
    });

    const fullscreenImage = document.createElement("img");
    fullscreenImage.style.maxWidth = "90%";
    fullscreenImage.style.maxHeight = "90%";
    fullscreenOverlay.appendChild(fullscreenImage);
    document.body.appendChild(fullscreenOverlay);

    // Function to open image in fullscreen
    function openFullscreen(imageSrc) {
        fullscreenImage.src = imageSrc;
        fullscreenOverlay.style.display = "flex";
    }

    // Preview images
    fileInput.addEventListener("change", () => {
        previewContainer.innerHTML = ""; // Clear previous previews
        const files = fileInput.files;

        Array.from(files).forEach((file) => {
            if (file.type.startsWith("image/")) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.createElement("img");
                    img.src = e.target.result;
                    img.alt = file.name;
                    img.style.width = "200px";
                    img.style.margin = "10px";
                    img.style.border = "1px solid #ccc";
                    img.style.borderRadius = "8px";
                    img.addEventListener("click", () => openFullscreen(e.target.result));
                    previewContainer.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Function to display sector previews
    function displaySectorPreviews(results) {
        const sectorPreviewContainer = document.getElementById("sectorPreview");
        sectorPreviewContainer.innerHTML = ""; // Clear previous previews

        results.forEach(result => {
            const img = document.createElement("img");
            img.src = `/plotted/${result.filename.replace('.png', '.jpg')}`;
            img.alt = result.filename;
            img.style.width = "200px";
            img.style.margin = "10px";
            img.style.border = "1px solid #ccc";
            img.style.borderRadius = "8px";
            img.addEventListener("click", () => openFullscreen(`/plotted/${result.filename.replace('.png', '.jpg')}`));
            sectorPreviewContainer.appendChild(img);
        });
    }

    // Function to display detection results
    function displayDetectionResults(results) {
        resultsContainer.innerHTML = ""; // Clear previous results

        results.forEach(result => {
            const img = document.createElement("img");
            img.src = `/results/${result.filename}`;
            img.alt = result.filename;
            img.style.width = "200px";
            img.style.margin = "10px";
            img.style.border = "1px solid #ccc";
            img.style.borderRadius = "8px";
            img.addEventListener("click", () => openFullscreen(`/results/${result.filename}`));
            resultsContainer.appendChild(img);
        });
    }

    const modelButtons = document.querySelectorAll(".model-button");
    let selectedModel = "best (1).pt"; // Default model

    modelButtons.forEach(button => {
        button.addEventListener("click", () => {
            modelButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");
            selectedModel = button.dataset.model;
        });
    });

    // Handle form submission and result rendering
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        formData.append("model", selectedModel);

        try {
            const response = await fetch("/upload", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                resultsContainer.innerHTML = `<p style="color:red;">${data.error}</p>`;
            } else {
                resultsContainer.innerHTML = `<p style="color:green;">Files processed successfully.</p>`;
                displayDetectionResults(data.results);
            }
        } catch (error) {
            resultsContainer.innerHTML = `<p style="color:red;">An error occurred: ${error.message}</p>`;
        }
    });

    // Handle deploy sectors button click
    document.getElementById("deploy-sectors-button").addEventListener("click", async () => {
        try {
            const response = await fetch("/process", {
                method: "POST",
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                displaySectorPreviews(data.results);
            }
        } catch (error) {
            alert(`An error occurred: ${error.message}`);
        }
    });

    document.getElementById("edit-button").addEventListener("click", () => {
        window.location.href = "/edit.html";
    });
});

async function downloadAllResults() {
    const zip = new JSZip();
    const resultsContainer = document.getElementById("results");
    const images = resultsContainer.getElementsByTagName("img");

    for (const img of images) {
        const response = await fetch(img.src);
        const blob = await response.blob();
        const fileName = img.src.split('/').pop();
        zip.file(fileName, blob);
    }

    zip.generateAsync({ type: 'blob' }).then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'results.zip';
        a.click();
    });
}