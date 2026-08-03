async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const status = document.getElementById("status");

    // Validate file selection
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload");
        return;
    }

    const file = fileInput.files[0];

    // Prepare multipart form data
    const formData = new FormData();
    formData.append("file", file);

    // UI feedback
    status.innerText = "⏳ Uploading and processing file...";

    try {
        // Same-origin request (frontend + backend on same server)
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        // Check backend response
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        // Receive ZIP file
        const blob = await response.blob();

        // Trigger download
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "doctor_email_files.zip";

        document.body.appendChild(a);
        a.click();

        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        // Success message
        status.innerText = "✅ File processed successfully. Download started.";

    } catch (error) {
        console.error("Frontend upload error:", error);
        status.innerText =
            "❌ Upload failed on frontend. Backend logs may still show success.";
    }
}
