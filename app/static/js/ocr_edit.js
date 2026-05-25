// /static/js/ocr_edit.js
window.addEventListener("DOMContentLoaded", async () => {
    try {
        const data = window.INIT_DATA;
        if (!data) return;

        // =====================
        // 状態管理（★最重要）
        // =====================
        let selectedCategory = "";

        // =====================
        // 初期処理
        // =====================
        const isEditMode = !!data?.id;
        const deleteBtn = document.getElementById("deleteBtn");

        // デバッグ
        // console.log("data:", data);
        // console.log(data.id)

        if (deleteBtn) {
            const showDelete = data?.status === "confirmed";
            deleteBtn.classList.toggle("hidden", !showDelete);
        }
        
        // =====================
        // DOM取得
        // =====================
        const resultArea = document.getElementById("resultArea");
        const ocrText = document.getElementById("ocrText");
        // const formArea = document.getElementById("formArea");
        const saveBtn = document.getElementById("saveBtn");
        // const resultImage = document.getElementById("resultImage");
        const resultImage = document.querySelector("img[alt='Receipt image']");

        // =====================
        // 画面表示
        // =====================
        if (resultArea) resultArea.classList.remove("hidden");
        if (ocrText) ocrText.textContent = data.ocr_text ?? "（OCRなし）";
        // if (formArea) formArea.classList.remove("hidden");
        if (saveBtn) saveBtn.classList.remove("hidden");


        console.log("INIT_DATA:", data);

        // =====================
        // OCR結果反映
        // =====================
        if (data.result) {
            const store = document.getElementById("storeName");
            const date = document.getElementById("date");
            const amount = document.getElementById("amount");

            if (store) store.value = data.result.store_name || "";
            if (date) {
                const formatted = formatDate(data.result.date);
                date.value = formatted || new Date().toISOString().split("T")[0];
            }
            if (amount) amount.value = data.result.total_amount || "";
        }

        // =====================
        // カテゴリ生成
        // =====================
        renderCategories(data.categories || []);

        function renderCategories(categories) {

            const categoryArea = document.getElementById("categoryArea");
            const select = document.getElementById("categorySelect");
            const customInput = document.getElementById("customCategory");

            const allCategories = [
                "食費", "消耗品費", "旅費交通費",
                "交際費", "通信費", "水道光熱費",
                "地代家賃", "広告宣伝費", "会議費", "雑費"
            ];

            if (!categoryArea || !customInput || !select) return;

            // UIリセット
            categoryArea.innerHTML = "";

            // 初期状態
            selectedCategory = "";
            select.options.length = 0;
            select.add(new Option("選択してください", ""));
            select.value = "";
            customInput.value = "";

            allCategories.forEach(cat => {
                select.add(new Option(cat, cat));
            });

            // =====================
            // ボタン選択処理
            // =====================
            function setActive(btn,value) {
                selectedCategory = value;

                // ★追加：selectとinputをリセット
                select.value = "";
                customInput.value = "";

                categoryArea.querySelectorAll("button").forEach(b => {
                    // 全部リセット
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    // hover時
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });

                // 選択ボタン
                btn.classList.add("bg-secondary", "text-on-secondary");

                 // ★重要：hoverを消す（これやらないと色ぶれる）
                btn.classList.remove("hover:bg-secondary", "hover:text-on-secondary");
            }

            // =====================
            // AI候補ボタン
            // =====================
            categories.forEach((cat, index) => {

                const btn = document.createElement("button");
                btn.textContent = cat;

                btn.className =
                    "px-4 py-2 rounded-full font-body-sm border border-outline-variant text-on-surface-variant transition-colors hover:bg-secondary hover:text-on-secondary";
                btn.addEventListener("click", () => {
                    setActive(btn,cat);
                });

                categoryArea.appendChild(btn);
            });

            // 1個目を選択状態
            if (categories.length > 0) {
                const firstBtn = categoryArea.querySelector("button");
                if (firstBtn) {
                    setActive(firstBtn, categories[0]);
                }
            }

            // =====================
            // select変更
            // =====================
            select.addEventListener("change", () => {
                selectedCategory = select.value;

                // ★ここ追加（ボタン見た目リセット）
                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });
            });

            // =====================
            // 手入力変更
            // =====================
            customInput.addEventListener("input", () => {
                selectedCategory = customInput.value;

                // ボタン見た目リセット
                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });
                // selectもリセット
                select.value = "";
            });


            // デバッグ
            // console.log("categories:", categories);

        }

        // =====================
        // 日付フォーマット
        // =====================
        function formatDate(dateStr) {
            if (!dateStr) return "";
            if (dateStr.includes("-")) return dateStr;

            const match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
            if (!match) return "";

            return `${match[1]}-${match[2].padStart(2,"0")}-${match[3].padStart(2,"0")}`;
        }

        // =====================
        // 保存ボタン
        // =====================
        if (saveBtn) {
            saveBtn.addEventListener("click", async function () {

                const payload = {
                    id: data.id, 
                    store_name: document.getElementById("storeName").value,
                    date: document.getElementById("date").value,
                    amount: document.getElementById("amount").value,
                    category: selectedCategory
                };

                try {
                    const res = await fetch("/transaction/update_expense", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) {
                        alert("保存失敗");
                        return;
                    }

                    alert("保存成功！");
                    window.location.href = "/transaction/history";

                } catch (err) {
                    console.error(err);
                    alert("通信エラー");
                }
            });
        }
        // =====================
        // 削除
        // =====================

        if (deleteBtn) {
            deleteBtn.addEventListener("click", async () => {
                if (!confirm("本当に削除しますか？")) return;

                const res = await fetch(`/transaction/delete_expense/${data.id}`, {
                    method: "DELETE"
                });

                if (res.ok) {
                    alert("削除しました");
                    window.location.href = "/transaction/history";
                } else {
                    alert("削除失敗");
                }
            });
        }

    } catch (err) {
        console.error(err);
        alert("初期ロードエラー");
    }
});