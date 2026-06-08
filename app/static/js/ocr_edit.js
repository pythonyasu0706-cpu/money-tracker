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
        const store = document.getElementById("storeName");
        const dateInput = document.getElementById("date");
        const amount = document.getElementById("amount");
        if (data.result) {
            if (store) store.value = data.result.store_name || "";
            if (amount) amount.value = data.result.total_amount || "";
        }

        // 2. 日付のセット（最優先：DBに保存された日付 ➔ 次点：AIの解析結果 ➔ 最終保険：今日）
        if (dateInput) {
            // routes.py から渡ってきた「data.date」（2026-06-08 形式）を最優先にする
            if (data.date) {
                dateInput.value = data.date;
            } 
            // もし無ければ、AIの生データからパースを試みる
            else if (data.result && data.result.date) {
                dateInput.value = formatDate(data.result.date);
            } 
            // どちらも完全に空っぽの場合だけ、今日の入力日にする
            else {
                dateInput.value = new Date().toISOString().split("T")[0];
            }
        }

        // =====================
        // カテゴリ生成
        // =====================
        renderCategories(data.categories || []);

        function renderCategories(categories) {
            const categoryArea = document.getElementById("categoryArea");
            const select = document.getElementById("categorySelect");
            const customInput = document.getElementById("customCategory");

            // 前回のブレ対策を適用して「旅費」を「旅費交通費」に
            const allCategories = [
                "食費", "消耗品費", "旅費交通費",
                "交際費", "通信費", "水道光熱費",
                "地代家賃", "広告宣伝費", "会議費", "雑費"
            ];

            if (!categoryArea || !customInput || !select) return;

            // UIリセット
            categoryArea.innerHTML = "";

            // 初期状態は、前回保存されたカテゴリー（あれば）をセット
            const savedCategory = data.category || "";
            selectedCategory = savedCategory;
            
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
            function setActive(btn, value) {
                selectedCategory = value;

                // selectとinputをリセット
                select.value = "";
                customInput.value = "";

                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });

                if (btn) {
                    btn.classList.add("bg-secondary", "text-on-secondary");
                    btn.classList.remove("hover:bg-secondary", "hover:text-on-secondary");
                }
            }

            // =====================
            // AI候補ボタン生成
            // =====================
            let matchedBtn = null;

            categories.forEach((cat) => {
                // 表記ゆれ補正
                if (cat === "交通費" || cat === "旅費") {
                    cat = "旅費交通費";
                }

                const btn = document.createElement("button");
                btn.textContent = cat;
                btn.className =
                    "px-4 py-2 rounded-full font-body-sm border border-outline-variant text-on-surface-variant transition-colors hover:bg-secondary hover:text-on-secondary";
                
                btn.addEventListener("click", () => {
                    setActive(btn, cat);
                });

                categoryArea.appendChild(btn);

                // もしこのボタンの文字が「前回保存されたカテゴリー」と一致したらキープ
                if (savedCategory && cat === savedCategory) {
                    matchedBtn = btn;
                }
            });

            // =====================
            // 初期選択の復元ロジック（★ここがポイント）
            // =====================
            if (savedCategory) {
                // パターンA: 前回保存した値がAIのボタン候補の中にある場合
                if (matchedBtn) {
                    setActive(matchedBtn, savedCategory);
                } 
                // パターンB: 固定セレクトボックスの中にある基本カテゴリーの場合
                else if (allCategories.includes(savedCategory)) {
                    select.value = savedCategory;
                } 
                // パターンC: それ以外（ユーザーオリジナルの手入力カテゴリ）の場合
                else {
                    customInput.value = savedCategory;
                }
            } else if (categories.length > 0) {
                // 初回登録時（保存されたカテゴリがまだ無い）は、今まで通りAI候補の1個目を選択
                const firstBtn = categoryArea.querySelector("button");
                if (firstBtn) {
                    setActive(firstBtn, categories[0] === "交通費" || categories[0] === "旅費" ? "旅費交通費" : categories[0]);
                }
            }

            // =====================
            // select変更
            // =====================
            select.addEventListener("change", () => {
                selectedCategory = select.value;
                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });
                if (select.value) customInput.value = ""; // 入力欄をクリア
            });

            // =====================
            // 手入力変更
            // =====================
            customInput.addEventListener("input", () => {
                selectedCategory = customInput.value;
                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                    b.classList.add("hover:bg-secondary", "hover:text-on-secondary");
                });
                select.value = "";
            });
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