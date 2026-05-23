// /static/history.js 
document.addEventListener("DOMContentLoaded", () => {
    console.log(cards[0].dataset);
    const buttons = document.querySelectorAll(".filter-btn");
    const cards = document.querySelectorAll(".expense-card");
    const searchInput = document.getElementById("searchInput");

    let currentFilter = "all";

    // カテゴリごとの色（Jinjaと揃える）
    const colorMap = {
        "食費": "bg-amber-300 text-on-tertiary-fixed-variant",
        "交通費": "bg-purple-300 text-on-secondary-fixed-variant",
        "消耗品費": "bg-tertiary-fixed text-on-surface-variant",
        "その他": "bg-secondary-fixed text-on-surface-variant",
        "all": "bg-secondary-container text-on-secondary-container"
    };


// 結合版
    function updateEmptyMonths() {
        document.querySelectorAll(".month-section").forEach(section => {
            const visibleCards = section.querySelectorAll("a:not(.hidden)");
            section.style.display = visibleCards.length ? "" : "none";
        });
    }

    function applyFilter() {
        const keyword = searchInput?.value?.toLowerCase() || "";
        const filter = currentFilter;
            
        cards.forEach(card => {
            const link = card.closest("a");
            const shopName = card.querySelector("h3")?.innerText.toLowerCase() || "";
            const category = (card.dataset.category || "").trim();

            const matchKeyword = 
                shopName.includes(keyword) || category.includes(keyword);

            const matchCategory = 
                currentFilter === "all" || category === currentFilter;

            const show = matchKeyword && matchCategory;

            link.classList.toggle("hidden", !show); // ★divじゃなくaを消す
        });

        updateEmptyMonths();
    }

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            currentFilter = btn.dataset.filter;

            buttons.forEach(b => {
                b.className =
                    "filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap bg-surface-container-high text-on-surface-variant";
            });

            const activeColor = colorMap[currentFilter] || colorMap["その他"];
            btn.className = `filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap ${activeColor}`;

            applyFilter();
        });
    });

    searchInput?.addEventListener("input", applyFilter);

    applyFilter(); // 初期表示
    updateEmptyMonths();

});

