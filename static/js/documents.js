const uploadForm = document.getElementById("uploadForm");
const documentFile = document.getElementById("documentFile");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = documentFile.files[0];

    if (!file) {
        uploadStatus.textContent = "Lütfen bir dosya seçin.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadStatus.textContent = "Doküman yükleniyor...";

    try {
        const response = await fetch("/documents/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Yükleme başarısız.");
        }

        uploadStatus.textContent =
            `✅ ${result.filename} yüklendi. Doküman işleme başlatıldı.`;

        uploadForm.reset();

    } catch (error) {
        uploadStatus.textContent = `❌ ${error.message}`;
    } finally {
        uploadButton.disabled = false;
    }
});