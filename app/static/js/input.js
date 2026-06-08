// /static/js/input.js
window.addEventListener("DOMContentLoaded", async () => {
    // =====================
    // 状態管理（★最重要）
    // =====================
    let selectedCategory = "";
    let selectedType = "expense";

    // =====================
    // DOM取得
    // =====================
    const tabExpense = document.getElementById("tabExpense");
    const tabIncome = document.getElementById("tabIncome");
    const saveBtn = document.getElementById("saveBtn");

    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategory");
    const customWrapper = customInput.closest("div");

    // 初期は隠す
    customWrapper.classList.add("hidden");
    select.classList.add("hidden");

    const CATEGORY_MAP = {
        expense:[
            "食費", "消耗品費", "旅費交通費",
            "交際費", "通信費", "水道光熱費",
            "地代家賃", "広告宣伝費", "会議費", "雑費"
        ],
        income: [
            "給与", "副業収入", "賞与", "雑収入"
        ]
    };

    // =====================
    // 🌟 変更：関数名を initCategoryUI に変更
    // =====================
    function initCategoryUI(categories) {
        const categoryArea = document.getElementById("categoryArea");
        categoryArea.innerHTML = "";

        // 初期化
        selectedCategory = "";
        select.innerHTML = '<option value="">選択してください</option>';
        customInput.value = "";

        // =====================
        // ★タイプ別UI制御
        // =====================
        if (selectedType === "expense") {

            // ▼ ボタン用（少数）
            const mainCategories = ["食費", "消耗品費", "雑費"];

            // ▼ select（残り）
            categories.forEach(cat => {
                if (!mainCategories.includes(cat)) {
                    select.add(new Option(cat, cat));
                }
            });

            // ▼ 初期は隠す
            customWrapper.classList.add("hidden");
            select.classList.add("hidden");

            // ===== ボタン =====
            mainCategories.forEach(cat => {
                const btn = document.createElement("button");
                btn.textContent = cat;
                btn.className =
                    "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant transition-colors hover:bg-secondary hover:text-on-secondary";

                btn.addEventListener("click", () => {
                    selectedCategory = cat;

                    categoryArea.querySelectorAll("button").forEach(b => {
                        b.classList.remove("bg-secondary", "text-on-secondary");
                    });

                    btn.classList.add("bg-secondary", "text-on-secondary");

                    customWrapper.classList.add("hidden");
                    select.classList.add("hidden");
                    customInput.value = "";
                    select.value = "";
                });

                categoryArea.appendChild(btn);
            });

            // ===== その他 =====
            const otherBtn = document.createElement("button");
            otherBtn.textContent = "その他";
            otherBtn.className =
                "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant transition-colors hover:bg-secondary hover:text-on-secondary";

            otherBtn.addEventListener("click", () => {
                selectedCategory = "";

                customWrapper.classList.remove("hidden");
                select.classList.remove("hidden");

                categoryArea.querySelectorAll("button").forEach(b => {
                    b.classList.remove("bg-secondary", "text-on-secondary");
                });

                otherBtn.classList.add("bg-secondary", "text-on-secondary");
                customInput.focus();
            });

            categoryArea.appendChild(otherBtn);

        } else {
            // =====================
            // ★収入モード
            // =====================
            const incomeButtons = ["給与", "賞与", "雑収入", "副業収入"]; // ★「副業収入」を固定枠に追加して統一

            // ▼ selectは使わない
            select.classList.add("hidden");

            // ▼ inputは常に表示
            customWrapper.classList.remove("hidden");

            incomeButtons.forEach(cat => {
                const btn = document.createElement("button");
                btn.textContent = cat;
                btn.className =
                    "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant hover:bg-secondary hover:text-on-secondary";

                btn.addEventListener("click", () => {
                    selectedCategory = cat;

                    categoryArea.querySelectorAll("button").forEach(b => {
                        b.classList.remove("bg-secondary", "text-on-secondary");
                    });

                    btn.classList.add("bg-secondary", "text-on-secondary");

                    // 入力リセット
                    customInput.value = "";
                });

                categoryArea.appendChild(btn);
            });
        }
    }

    // =====================
    // タブ
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
        setActiveTab("expense");
        initCategoryUI(CATEGORY_MAP.expense); // 🌟 変更を反映
    });

    tabIncome.addEventListener("click", () => {
        selectedType = "income";
        setActiveTab("income");
        initCategoryUI(CATEGORY_MAP.income); // 🌟 変更を反映
    });

    // 初期表示
    setActiveTab("expense");
    initCategoryUI(CATEGORY_MAP.expense); // 🌟 変更を反映

    // =====================
    // select / input
    // =====================
    select.addEventListener("change", (e) => {
        selectedCategory = e.target.value;
        customInput.value = "";
        // 「その他」の中に隠れているセレクトボックスを選んだらボタンの光をリセット
        document.getElementById("categoryArea").querySelectorAll("button").forEach(b => {
            if(b.textContent !== "その他") b.classList.remove("bg-secondary", "text-on-secondary");
        });
    });

    customInput.addEventListener("input", (e) => {
        selectedCategory = e.target.value;
        select.value = "";
        document.getElementById("categoryArea").querySelectorAll("button").forEach(b => {
            if(b.textContent !== "その他") b.classList.remove("bg-secondary", "text-on-secondary");
        });
    });

    // =====================
    // 保存
    // =====================
    saveBtn.addEventListener("click", async () => {
        const amountInput = document.getElementById("amount").value.trim();

        if (!amountInput) {
            alert("金額を入力してください");
            return;
        }

        if (isNaN(amountInput)) {
            alert("金額は数字で入力してください");
            return;
        }

        if (!selectedCategory) {
            alert("カテゴリを選択してください");
            return;
        }

        const payload = {
            store_name: document.getElementById("storeName").value,
            date: document.getElementById("date").value,
            amount: Number(amountInput),
            category: selectedCategory,
            type: selectedType
        };

        const res = await fetch("/transaction/create_expense", {
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
    });
});