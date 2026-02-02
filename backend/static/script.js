// ==============================
// Upload Daily Excel
// ==============================
async function uploadExcel() {
    const fileInput = document.getElementById("excelFile");
    const status = document.getElementById("excelStatus");

    if (!fileInput.files.length) {
        alert("Please select the Excel file");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    status.innerText = "⏳ Processing Excel...";

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Excel upload failed");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "doctor_email_files.zip";
        a.click();

        status.innerText = "✅ Emails generated & ZIP downloaded";

    } catch (err) {
        console.error(err);
        status.innerText = "❌ Excel upload failed";
    }
}


// ==============================
// Upload No Review CSV
// ==============================
async function uploadNoReview() {
    const fileInput = document.getElementById("noReviewFile");
    const status = document.getElementById("noReviewStatus");

    if (!fileInput.files.length) {
        alert("Please select the No-Review CSV file");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    status.innerText = "⏳ Processing No-Review file...";

    try {
        const response = await fetch("/upload-no-review", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("No-review upload failed");
        }

        const data = await response.json();

        status.innerText = "✅ Master sheet updated from No-Review file";

    } catch (err) {
        console.error(err);
        status.innerText = "❌ No-review upload failed";
    }
}
