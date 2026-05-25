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

    // =====================
    // DOM
    // =====================
    const tabExpense = document.getElementById("tabExpense");
    const tabIncome = document.getElementById("tabIncome");
    const saveBtn = document.getElementById("saveBtn");

    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategory");
    const customWrapper = customInput.closest("div");

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
    // カテゴリ描画
    // =====================
    function renderCategories(categories) {

        categoryArea.innerHTML = "";

        select.innerHTML = '<option value="">選択してください</option>';

        // =====================
        // 支出
        // =====================
        if (selectedType === "expense") {

            const main = ["食費","消耗品費","雑費"];

            categories.forEach(cat => {
                if (!main.includes(cat)) {
                    select.add(new Option(cat, cat));
                }
            });


            main.forEach(cat => {

                const btn = createBtn(cat);
                categoryArea.appendChild(btn);

                if (selectedCategory === cat) {
                    activate(btn, cat);
                }
            });


            // ★既存カテゴリがmainじゃない場合
            if (!main.includes(selectedCategory) && selectedCategory) {

                if (categories.includes(selectedCategory)) {
                    select.value = selectedCategory;
                } else {
                    customInput.value = selectedCategory;
                }
            }

        } else {

            // =====================
            // 収入
            // =====================
            const incomeBtns = ["給与","賞与","雑収入","副業収入"];


            incomeBtns.forEach(cat => {

                const btn = createBtn(cat);
                categoryArea.appendChild(btn);

                if (selectedCategory === cat) {
                    activate(btn, cat);
                }
            });

            // ★既存が手入力なら
            if (!incomeBtns.includes(selectedCategory)) {
                customInput.value = selectedCategory || "";
            }
        }
        // 初期選択を反映
        if (selectedCategory) {
            const buttons = document.querySelectorAll("#categoryArea button");

            buttons.forEach(btn => {
                if (btn.textContent === selectedCategory) {
                    btn.classList.add("bg-secondary", "text-on-secondary");
                }
            });

            // ボタンに無い場合 → 手入力へ
            if (![...buttons].some(b => b.textContent === selectedCategory)) {
                customInput.value = selectedCategory;
            }
        }
    }

    // =====================
    // 共通UI
    // =====================
    function createBtn(cat) {
        const btn = document.createElement("button");
        btn.textContent = cat;

        btn.className =
            "px-4 py-2 rounded-full border border-outline-variant text-on-surface-variant hover:bg-secondary hover:text-on-secondary";

        btn.addEventListener("click", () => {
            activate(btn, cat);
        });

        return btn;
    }

    function activate(btn, value) {
        selectedCategory = value;
        select.value = ""; //

        clearActive();

        btn.classList.add("bg-secondary","text-on-secondary");

        customInput.value = "";
    }

    function clearActive() {
        categoryArea.querySelectorAll("button").forEach(b => {
            b.classList.remove("bg-secondary","text-on-secondary");
        });
    }

    // =====================
    // タブ
    // =====================
    function setActiveTab(type) {
        if (type === "expense") {
            tabExpense.classList.add("bg-secondary","text-on-secondary");
            tabIncome.classList.remove("bg-secondary","text-on-secondary");
        } else {
            tabIncome.classList.add("bg-secondary","text-on-secondary");
            tabExpense.classList.remove("bg-secondary","text-on-secondary");
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

    // 初期描画
    setActiveTab(selectedType);
    renderCategories(CATEGORY_MAP[selectedType]);

    // =====================
    // 入力変更
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