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
    // カテゴリ描画（これが本体）
    // =====================
    function renderCategories(categories) {

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
                    "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant hover:bg-secondary hover:text-on-secondary";

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
                "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant";

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

            const incomeButtons = ["給与", "賞与", "雑収入"];

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
        renderCategories(CATEGORY_MAP.expense);
    });

    tabIncome.addEventListener("click", () => {
        selectedType = "income";
        setActiveTab("income");
        renderCategories(CATEGORY_MAP.income);
    });
    // 初期表示
    setActiveTab("expense");
    renderCategories(CATEGORY_MAP.expense);

    // =====================
    // select / input
    // =====================
    select.addEventListener("change", (e) => {
        selectedCategory = e.target.value;
        customInput.value = "";
    });

    customInput.addEventListener("input", (e) => {
        selectedCategory = e.target.value;
        select.value = "";
    });

    // =====================
    // 保存
    // =====================
    saveBtn.addEventListener("click", async () => {

        const payload = {
            store_name: document.getElementById("storeName").value,
            date: document.getElementById("date").value,
            amount: document.getElementById("amount").value,
            category: selectedCategory,
            type: selectedType
        };

        const res = await fetch("/create_expense", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            alert("保存失敗");
            return;
        }

        alert("保存成功！");
        window.location.href = "/history";
    });
});