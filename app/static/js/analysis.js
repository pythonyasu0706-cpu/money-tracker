// static/js/analysis.js
document.addEventListener("DOMContentLoaded", () => {
    // const buttons = document.querySelectorAll(".filter-btn");
    const rows = document.querySelectorAll("tbody tr");
    const searchInput = document.getElementById("searchInput");
    const ctx = document.getElementById("categoryChart");
    const dailyCtx = document.getElementById("dailyChart");
    const monthlyCtx = document.getElementById("monthlyChart");

    const colorMap = {
        "食費": "bg-amber-300 text-on-tertiary-fixed-variant",
        "交通費": "bg-purple-300 text-on-secondary-fixed-variant",
        "消耗品費": "bg-tertiary-fixed text-on-surface-variant",
        "その他": "bg-secondary-fixed text-on-surface-variant",
        "all": "bg-secondary-container text-on-secondary-container"
    };

    const monthSelect = document.getElementById("monthSelect");

    monthSelect?.addEventListener("change", (e) => {
        const month = e.target.value;
        window.location.href = `/analysis/analysis?month=${month}`;
    });

    Chart.register(ChartDataLabels);

    // =====================
    // フィルター
    // =====================
    // let currentFilter = "all";

    // function updateEmptyMonths() {
    //     document.querySelectorAll(".month-section").forEach(section => {
    //         const visibleRows = section.querySelectorAll("tbody tr:not(.hidden)");
    //         section.style.display = visibleRows.length ? "" : "none";
    //     });
    // }

    // function applyFilter() {
    //     const keyword = searchInput?.value?.toLowerCase() || "";

    //     rows.forEach(row => {
    //         const shopName = row.children[1]?.innerText.toLowerCase() || "";
    //         const category = row.children[2]?.innerText.trim().toLowerCase();

    //         const matchKeyword =
    //             shopName.includes(keyword) || category.includes(keyword);

    //         const matchCategory =
    //             currentFilter === "all" || category === currentFilter;

    //         const show = matchKeyword && matchCategory;

    //         row.classList.toggle("hidden", !show);
    //     });

    //     updateEmptyMonths();

    // }

    // buttons.forEach(btn => {
    //     btn.addEventListener("click", () => {
    //         currentFilter = btn.dataset.filter;

    //         buttons.forEach(b => {
    //             b.className =
    //                 "filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap bg-surface-container-high text-on-surface-variant";
    //         });

    //         const activeColor = colorMap[currentFilter] || colorMap["その他"];
    //         btn.className = `filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap ${activeColor}`;

    //         applyFilter();
    //     });
    // });

    // searchInput?.addEventListener("input", applyFilter);

    // applyFilter();
    // updateEmptyMonths();

     // =====================
    // カテゴリー円グラフ
    // =====================
    if (ctx && typeof CATEGORY_DATA !== "undefined") {
        const categories = Object.keys(CATEGORY_DATA);
        const values = Object.values(CATEGORY_DATA);

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: categories,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        "#6edbb3", // muted green
                        "#f59e5b", // muted orange
                        "#8aa8ff", // muted blue
                        "#4fd1c5", // muted teal
                        "#f2c66d", // muted amber
                        "#b39df3", // muted purple
                        "#f78aa0"  // muted pink
                    ]
                }]
            },
            options: {
                plugins: {
                    datalabels: {
                        display: false
                    }
                }
            }
        });
    }

    // =====================
    // 収支バーチャート
    // =====================
    if (monthlyCtx && typeof MONTHLY_SUMMARY !== "undefined") {

        new Chart(monthlyCtx, {
            type: "bar",
            data: {
                labels: ["支出", "収入"],
                datasets: [{
                    data: [
                        MONTHLY_SUMMARY.expense,
                        MONTHLY_SUMMARY.income
                    ],
                    backgroundColor: ["#fd7c7c", "#3ec8ff"]
                }]
            },
            options: {
                plugins: {
                    legend: {display: false},
                    tooltip: {enabled: true},
                    datalabels: {
                        display: false
                    }
                },
                indexAxis: "y", // ←横棒の核心
                responsive: true,
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // =====================
    // 日別グラフ
    // =====================
    if (dailyCtx && typeof DAILY_DATA !== "undefined") {

        const labels = Object.keys(DAILY_DATA);
        const expenseData = Object.values(DAILY_DATA);

        new Chart(dailyCtx, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "支出",
                        data: expenseData,
                        backgroundColor: "#79ade9"
                    }
                ]
            },
            options: {
                plugins: {
                    legend: {display: false},
                    tooltip: {enabled: true},
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        formatter: function(value) {
                            return value.toLocaleString() + '円';
                        }
                    }
                },
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grace: '10%'
                    }
                }
            }
        });
    }
});