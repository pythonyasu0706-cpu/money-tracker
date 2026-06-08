// /static/history.js 
document.addEventListener("DOMContentLoaded", () => {
    // document：ページ全体（HTMLそのもの）
    // DOMContentLoaded：HTMLの読み込みが終わったタイミング
    // addEventListener：イベント（出来事）が起きたときに処理する
    // 「HTMLが全部読み込まれた後に、この中の処理を実行する」
    // 用語 querySelectorAll：指定したクラスの要素を全部取る
    const buttons = document.querySelectorAll(".filter-btn");
    const cards = document.querySelectorAll(".expense-card");
    // 用語 getElementById：IDで1つだけ取る
    const searchInput = document.getElementById("searchInput");
    // buttons等最初に取得しておくと後で何度も使えるから最初に

    // letは変数　初期値をallにする
    let currentFilter = "all";

    // カテゴリごとの色（フラスク関数で決めたカードの色と揃える）
    const colorMap = {
        "食費": "bg-amber-300 text-on-tertiary-fixed-variant",
        "旅費交通費": "bg-purple-300 text-on-secondary-fixed-variant",
        "消耗品費": "bg-tertiary-fixed text-on-surface-variant",
        "その他": "bg-secondary-fixed text-on-surface-variant",
        "all": "bg-secondary-container text-on-secondary-container"
    };


    // 月ごとの非表示処理
    // 用語 functkon：処理をまとめて名前つける
    function updateEmptyMonths() {

        document.querySelectorAll(".month-section").forEach(section => {
            // 用語 :not(.hidden)：hiddenクラスがついてないものだけ。sectionの<a>タグのリンクごと消す
            const visibleCards = section.querySelectorAll("a:not(.hidden)");
            // 三項演算子 条件 ? trueのとき : falseのとき
            // 0個→false 1個以上→true
            // visibleCardsが1個以上あるなら → 表示する。CSSのデフォルトに戻す。つまり普通に表示される
            // 0個なら → 非表示にする
            // JavaScriptの.は「中身にアクセス」 CSSはクラス指定
            // section(HTML要素)のstyle(CSSスタイル部分)の中のdisplay(プロパティ)を触っている
            section.style.display = visibleCards.length ? "" : "none";
        });
    }

    function applyFilter() {
        // 用語 ?.：存在しなくてもエラーにしない(オプショナルチェーン)
        // 用語 toLowerCase()：小文字に変換
        // 入力された検索文字を取得
        // ||""：もし値がなければ空文字にする
        // 検索欄の文字(入力値)を安全に取得して、小文字にして、なければ空にする
        const keyword = searchInput?.value?.toLowerCase() || "";
        const filter = currentFilter;
        // 除外カテゴリ
        const excludeCategories = ["食費", "消耗品費", "旅費交通費"];
            
        // 全カードを1つずつ判定
        cards.forEach(card => {
            // cardの一番近い親の<a>タグを探して取る
            // 自分card→親div→さらに親div→見つけた<a>
            const link = card.closest("a");
            // 用語 querySelector：条件に合う要素を探して取ってくる道具
            // 用語 ?.innerText：もしh3が存在するなら実行してね(オプショナルチェーン)
            // カードの中のh3(店名)を取り出して、小文字にして、なければ空文字にする
            const shopName = card.querySelector("h3")?.innerText.toLowerCase() || "";
            // 用語 dataset：data-〇〇というHTML属性をJSで扱うための仕組み。data-が消えて、キャメルケースでアクセスできる
            // cardのdata-categoryを安全に取り出して、空白を削除する
            const category = (card.dataset.category || "").trim();

            // 店名orカテゴリーどちらかにキーワードがあれば一致
            // A||（OR）B　AかBどっちかがtrueならtrue
            const matchKeyword = 
                shopName.includes(keyword) || category.includes(keyword);

            // currentFilter === "all" 「全部表示モードか？」
            // category === currentFilter 「カードのカテゴリと選択が一致しているか？」
            // 全部表示ならOK,またはカテゴリー一致ならOK
            // const matchCategory = 
            //     currentFilter === "all" || category === currentFilter;

            let matchCategory;

                if (currentFilter === "all") {
                    matchCategory = true;
                } 
                else if (currentFilter === "その他") {
                    matchCategory = !excludeCategories.includes(category);
                } 
                else {
                    matchCategory = category === currentFilter;
                }

            // ?. 存在チェックして安全にアクセスする(途中がなくてもエラーにしないで進む)
            // && 条件がtrueなら次を実行する
            // キーワードもカテゴリも両方OKなら表示する
            const show = matchKeyword && matchCategory;

            // link；<a>タグ(リンク要素)
            // classList：クラス(CSSのclass)を操作する機能
            // toggle("hidden", 条件)：条件によってクラスをつけたり外したりする
            // showがtrueなら表示、falseならhiddenクラスを付けて非表示
            link.classList.toggle("hidden", !show); // ★divじゃなくaを消す
        });

        updateEmptyMonths();
    }

    // buttonsの中の要素を1個ずつ取り出して処理する
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            // クリックされたボタンのフィルター条件を currentFilter に保存している
            currentFilter = btn.dataset.filter;
            // すべてのフィルターボタンの見た目を同じ状態に戻す（初期化する)
            buttons.forEach(b => {
                b.className =
                    "filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap bg-surface-container-high text-on-surface-variant";
            });

            // 今選ばれているフィルターに応じて、ボタンの色（スタイル）を切り替えている
            const activeColor = colorMap[currentFilter] || colorMap["その他"];
            // || → 条件の「または」・保険（デフォルト
            // $ → 文字列の中に変数を入れる記号（テンプレート文字列）
            // ${} → 変数を埋め込む場所
            btn.className = `filter-btn px-4 py-2 rounded-full font-label-caps whitespace-nowrap ${activeColor}`;

            applyFilter();
        });
    });

    // 検索欄に文字が入力されるたびにapplyFilter を実行する
    searchInput?.addEventListener("input", applyFilter);

    applyFilter(); // 初期表示
    updateEmptyMonths();

});

