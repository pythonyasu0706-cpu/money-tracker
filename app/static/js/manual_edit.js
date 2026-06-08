// /static/js/manual_edit.js
window.addEventListener("DOMContentLoaded", () => {
    const deleteBtn = document.getElementById("deleteBtn");
    const data = window.INIT_DATA;
    if (!data) return;

    // =====================
    // 状態管理
    // =====================
    let selectedCategory = data.category || "";
    let selectedType = data.type || "expense";

    // 表記ゆれ補正（念のため初期ロード時に「旅費」を「旅費交通費」へ）
    if (selectedCategory === "交通費" || selectedCategory === "旅費") {
        selectedCategory = "旅費交通費";
    }

    // =====================
    // DOM
    // =====================
    const tabExpense = document.getElementById("tabExpense");
    const tabIncome = document.getElementById("tabIncome");
    const saveBtn = document.getElementById("saveBtn");

    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategory");

    const categoryArea = document.getElementById("categoryArea");

    // =====================
    // 初期値セット（★重要）
    // =====================
    document.getElementById("storeName").value = data.store_name || "";
    document.getElementById("date").value = data.date || "";
    document.getElementById("amount").value = data.amount || "";

    const CATEGORY_MAP = {
        expense: [
            "食費","消耗品費","旅費交通費","交際費","通信費",
            "水道光熱費","地代家賃","広告宣伝費","会議費","雑費"
        ],
        income: ["給与","副業収入","賞与","雑収入"]
    };

    // =====================
    // 🌟 変更：関数名を setupCategoryUI に変更
    // =====================
    function setupCategoryUI(categories) {
        categoryArea.innerHTML = "";
        select.innerHTML = '<option value="">選択してください</option>';
        customInput.value = ""; // タブ切り替え時用にリセット

        // =====================
        // 支出タブの処理
        // =====================
        if (selectedType === "expense") {
            const main = ["食費", "消耗品費", "雑費"];

            // クイックボタンにないものをセレクトボックスに追加
            categories.forEach(cat => {
                if (!main.includes(cat)) {
                    select.add(new Option(cat, cat));
                }
            });

            // メインカテゴリをボタンとして配置
            main.forEach(cat => {
                const btn = createBtn(cat);
                categoryArea.appendChild(btn);

                if (selectedCategory === cat) {
                    activateButton(btn, cat);
                }
            });

            // セレクトボックス、または手入力への値の復元
            if (!main.includes(selectedCategory) && selectedCategory) {
                if (categories.includes(selectedCategory)) {
                    select.value = selectedCategory;
                } else {
                    customInput.value = selectedCategory;
                }
            }

        } else {
            // =====================
            // 収入タブの処理
            // =====================
            const incomeBtns = ["給与", "賞与", "雑収入", "副業収入"];

            incomeBtns.forEach(cat => {
                const btn = createBtn(cat);
                categoryArea.appendChild(btn);

                if (selectedCategory === cat) {
                    activateButton(btn, cat);
                }
            });

            // 固定ボタンに無い場合は手入力欄に復元
            if (!incomeBtns.includes(selectedCategory) && selectedCategory) {
                customInput.value = selectedCategory;
            }
        }

        // 🌟【バグガード】ボタンの文字と完全一致する状態があれば確実に光らせる
        if (selectedCategory) {
            const buttons = categoryArea.querySelectorAll("button");
            buttons.forEach(btn => {
                if (btn.textContent === selectedCategory) {
                    btn.classList.add("bg-secondary", "text-on-secondary");
                }
            });
        }
    }

    // =====================
    // 共通UIヘルパー
    // =====================
    function createBtn(cat) {
        const btn = document.createElement("button");
        btn.textContent = cat;
        btn.className =
            "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant transition-colors hover:bg-secondary hover:text-on-secondary";

        btn.addEventListener("click", () => {
            activateButton(btn, cat);
        });

        return btn;
    }

    // 🌟 変更：関数名を明確に（activate -> activateButton）
    function activateButton(btn, value) {
        selectedCategory = value;
        select.value = ""; 
        customInput.value = "";

        clearActiveButtons();
        if (btn) {
            btn.classList.add("bg-secondary", "text-on-secondary");
        }
    }

    // 🌟 変更：関数名を明確に（clearActive -> clearActiveButtons）
    function clearActiveButtons() {
        categoryArea.querySelectorAll("button").forEach(b => {
            b.classList.remove("bg-secondary", "text-on-secondary");
        });
    }

    // =====================
    // タブ切り替えイベント
    // =====================
    function setActiveTab(type) {
        if (type === "expense") {
            tabExpense.classList.add("bg-secondary", "text-on-secondary");
            tabIncome.classList.remove("bg-secondary", "text-on-secondary");
        } else {
            tabIncome.classList.add("bg-secondary", "text-on-secondary");
            tabExpense.classList.remove("bg-secondary", "text-on-secondary");
        }
    }

    tabExpense.addEventListener("click", () => {
        selectedType = "expense";
        selectedCategory = ""; // タブを切り替えたら選択中カテゴリはリセット
        setActiveTab("expense");
        setupCategoryUI(CATEGORY_MAP.expense); // 🌟 関数名変更を反映
    });

    tabIncome.addEventListener("click", () => {
        selectedType = "income";
        selectedCategory = ""; // タブを切り替えたら選択中カテゴリはリセット
        setActiveTab("income");
        setupCategoryUI(CATEGORY_MAP.income); // 🌟 関数名変更を反映
    });

    // 初期描画
    setActiveTab(selectedType);
    setupCategoryUI(CATEGORY_MAP[selectedType]); // 🌟 関数名変更を反映

    // =====================
    // セレクト・手入力の連動イベント
    // =====================
    select.addEventListener("change", (e) => {
        selectedCategory = e.target.value;
        customInput.value = "";
        clearActiveButtons(); // セレクトを選んだらボタンの光を消す
    });

    customInput.addEventListener("input", (e) => {
        selectedCategory = e.target.value;
        select.value = "";
        clearActiveButtons(); // 手入力したらボタンの光を消す
    });

    // =====================
    // 保存（UPDATE）
    // =====================
    saveBtn.addEventListener("click", async () => {
        const payload = {
            id: data.id,
            store_name: document.getElementById("storeName").value,
            date: document.getElementById("date").value,
            amount: document.getElementById("amount").value,
            category: selectedCategory,
            type: selectedType
        };

        const res = await fetch("/transaction/update_expense", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            alert("保存失敗");
            return;
        }

        alert("保存成功！");
        window.location.href = "/transaction/history";
    });

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
});