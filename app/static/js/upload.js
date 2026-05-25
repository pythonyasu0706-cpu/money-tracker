// static/js/upload/js
document.addEventListener("DOMContentLoaded", () => {

    const fileInput = document.getElementById("fileInput");
    const previewArea = document.getElementById("previewArea");
    const uploadBtn = document.getElementById("uploadBtn");

    let compressedFile = null;
    let previewUrl = null;

    fileInput.addEventListener("change", async () => {
        const file = fileInput.files[0];
        if (!file) return;

        if (previewUrl) URL.revokeObjectURL(previewUrl);

        previewUrl = URL.createObjectURL(file);

        previewArea.innerHTML = "";
        const img = document.createElement("img");
        img.src = previewUrl;
        img.className = "w-full h-auto object-contain max-h-[500px]";
        previewArea.appendChild(img);

        compressedFile = await compressImage(file);
        console.log("compressed:", compressedFile.size);
    });

    function compressImage(file) {
        return new Promise(resolve => {
            const img = new Image();
            const reader = new FileReader();

            reader.onload = e => img.src = e.target.result;

            img.onload = () => {
                const canvas = document.createElement("canvas");

                const MAX_WIDTH = 1000;
                const scale = MAX_WIDTH / img.width;

                canvas.width = MAX_WIDTH;
                canvas.height = img.height * scale;

                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                canvas.toBlob(blob => resolve(blob), "image/jpeg", 0.7);
            };

            reader.readAsDataURL(file);
        });
    }

    uploadBtn.addEventListener("click", async () => {

        if (!compressedFile) {
            alert("画像を選択してください");
            return;
        }

        uploadBtn.disabled = true;
        uploadBtn.textContent = "解析中...";

        const formData = new FormData();
        formData.append("image", compressedFile, "receipt.jpg");

        try {
            const res = await fetch("/process_receipt", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (!res.ok) {
                alert(data.error || "エラー");
                // ← エラー時だけ戻す
                uploadBtn.disabled = false;
                uploadBtn.textContent = "OCR解析する";
                return;
            }

            // 成功時は戻さず遷移
            window.location.href = data.redirect;

        } catch (err) {
            console.error(err);
            alert("通信エラー");

            // ← 通信エラー時も戻す
            uploadBtn.disabled = false;
            uploadBtn.textContent = "OCR解析する";
        }
    });
});