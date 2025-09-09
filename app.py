import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
import os
from datetime import datetime, date, timedelta
import re
import hashlib
import itertools

# --- A. コア理論・計算エンジン要件 ---
# A-0. 定数と基本設定
st.set_page_config(layout="wide", page_title="Harmony Navigator")

DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP = {
    'health': '1. 健康', 'relationships': '2. 人間関係', 'meaning': '3. 意味・貢献',
    'autonomy': '4. 自律・成長', 'finance': '5. 経済', 'leisure': '6. 余暇・心理', 'competition': '7. 競争'
}
SHORT_ELEMENTS = {
    'health': ['睡眠と休息', '身体的な快調さ'], 'relationships': ['親密な関係', '利他性・貢献'],
    'meaning': ['仕事・学業の充実感', '価値との一致'], 'autonomy': ['自己決定感', '自己成長の実感'],
    'finance': ['経済的な安心感', '職業的な達成感'], 'leisure': ['心の平穏', '楽しさ・喜び'],
    'competition': ['優越感・勝利']
}
LONG_ELEMENTS = {
    'health': ['睡眠', '食事', '運動', '身体的快適さ', '感覚的快楽', '性的満足'],
    'relationships': ['家族', 'パートナー・恋愛', '友人', '社会的承認', '利他性・貢献', '共感・繋がり'],
    'meaning': ['やりがい', '達成感', '信念との一致', 'キャリアの展望', '社会への貢献', '有能感'],
    'autonomy': ['自由・自己決定', '挑戦・冒険', '自己成長の実感', '変化の享受', '独立・自己信頼', '好奇心'],
    'finance': ['経済的安定', '経済的余裕', '労働環境', 'ワークライフバランス', '公正な評価', '職業的安定性'],
    'leisure': ['心の平穏', '自己肯定感', '創造性の発揮', '感謝', '娯楽・楽しさ', '芸術・自然'],
    'competition': ['優越感・勝利']
}
Q_COLS = ['q_' + d for d in DOMAINS]
S_COLS = ['s_' + d for d in DOMAINS]
CSV_FILE_TEMPLATE = 'harmony_data_{}.csv'
USERS_FILE = 'users.csv'
SLIDER_HELP_TEXT = """0: 全く当てはまらない

25: あまり当てはまらない

50: どちらとも言えない

75: やや当てはまる

100: 完全に当てはまる"""

ELEMENT_DEFINITIONS = {
    '睡眠と休息': '心身ともに、十分な休息が取れたと感じる度合い。例：朝、すっきりと目覚められたか。',
    '身体的な快調さ': '活力を感じ、身体的な不調（痛み、疲れなど）がなかった度合い。',
    '睡眠': '質の良い睡眠がとれ、朝、すっきりと目覚められた度合い。',
    '食事': '栄養バランスの取れた、美味しい食事に満足できた度合い。',
    '運動': '体を動かす習慣があり、それが心身の快調さに繋がっていた度合い。',
    '身体的快適さ': '慢性的な痛みや、気になる不調がなく、快適に過ごせた度合い。',
    '感覚的快楽': '五感を通じて、心地よいと感じる瞬間があった度合い。例：温かいお風呂、心地よい音楽。',
    '性的満足': '自身の性的な欲求や、パートナーとの親密さに対して、満足感があった度合い。',
    '親密な関係': '家族やパートナー、親しい友人との、温かい、あるいは安心できる繋がりを感じた度合い。',
    '利他性・貢献': '自分の行動が、誰かの役に立った、あるいは喜ばれたと感じた度合い。例：「ありがとう」と言われた。',
    '家族': '家族との間に、安定した、あるいは温かい関係があった度合い。',
    'パートナー・恋愛': 'パートナーとの間に、愛情や深い理解、信頼があった度合い。',
    '友人': '気軽に話せたり、支え合えたりする友人がおり、良い関係を築けていた度合い。',
    '社会的承認': '周囲の人々（職場、地域など）から、一員として認められ、尊重されていると感じた度合い。',
    '共感・繋がり': '他者の気持ちに寄り添ったり、逆に寄り添ってもらったりして、人との深い繋がりを感じた度合い。',
    '仕事・学業の充実感': '自分の仕事や学びに、やりがいや達成感を感じた度合い。',
    '価値との一致': '自分の大切にしている価値観や信念に沿って、行動できたと感じられる度合い。',
    'やりがい': '自分の仕事や活動（学業、家事、趣味など）に、意義や目的を感じ、夢中になれた度合い。',
    '達成感': '何か具体的な目標を達成したり、物事を最後までやり遂げたりする経験があった度合い。',
    '信念との一致': '自分の「こうありたい」という価値観や、倫理観に沿った行動ができた度合い。',
    'キャリアの展望': '自分の将来のキャリアに対して、希望や前向きな見通しを持てていた度合い。',
    '社会への貢献': '自分の活動が、所属するコミュニティや、より大きな社会に対して、良い影響を与えていると感じられた度合い。',
    '有能感': '自分のスキルや能力を、うまく発揮できているという感覚があった度合い。',
    '自己決定感': '今日の自分の行動は、自分で決めたと感じられる度合い。',
    '自己成長の実感': '何かを乗り越え、自分が成長した、あるいは新しいことを学んだと感じた度合い。',
    '自由・自己決定': '自分の人生における重要な事柄を、他者の圧力ではなく、自分自身の意志で選択・決定できていると感じた度合い。',
    '挑戦・冒険': '新しいことに挑戦したり、未知の経験をしたりして、刺激や興奮を感じた度合い。',
    '変化の享受': '環境の変化や、新しい考え方を、ポジティブに受け入れ、楽しむことができた度合い。',
    '独立・自己信頼': '自分の力で物事に対処できるという、自分自身への信頼感があった度合い。',
    '好奇心': '様々な物事に対して、知的な好奇心を持ち、探求することに喜びを感じた度合い。',
    '経済的な安心感': '日々の生活や将来のお金について、過度な心配をせず、安心して過ごせた度合い。',
    '職業的な達成感': '仕事や学業において、物事をうまくやり遂げた、あるいは目標に近づいたと感じた度合い。',
    '経済的安定': '「来月の支払いは大丈夫かな…」といった、短期的なお金の心配がない状態。',
    '経済的余裕': '生活必需品だけでなく、趣味や自己投資など、人生を豊かにすることにもお金を使える状態。',
    '労働環境': '物理的にも、精神的にも、安全で、健康的に働ける環境があった度合い。',
    'ワークライフバランス': '仕事（あるいは学業）と、プライベートな生活との間で、自分が望むバランスが取れていた度合い。',
    '公正な評価': '自分の働きや成果が、正当に評価され、報酬に反映されていると感じられた度合い。',
    '職業的安定性': '「この先も、この仕事を続けていけるだろうか」といった、長期的なキャリアや収入に対する不安がない状態。',
    '心の平穏': '過度な不安やストレスなく、精神的に安定していた度合い。',
    '楽しさ・喜び': '純粋に「楽しい」と感じたり、笑ったりする瞬間があった度合い。',
    '自己肯定感': '自分の長所も短所も含めて、ありのままの自分を、肯定的に受け入れることができた度合い。',
    '創造性の発揮': '何かを創作したり、新しいアイデアを思いついたりして、創造的な喜びを感じた度合い。',
    '感謝': '日常の小さな出来事や、周りの人々に対して、自然と「ありがたい」という気持ちが湧いた度合い。',
    '娯楽・楽しさ': '趣味に没頭したり、友人と笑い合ったり、純粋に「楽しい」と感じる時間があった度合い。',
    '芸術・自然': '美しい音楽や芸術、あるいは雄大な自然に触れて、心が動かされたり、豊かになったりする経験があった度合い。',
    '優越感・勝利': '他者との比較や、スポーツ、仕事、学業などにおける競争において、優位に立てたと感じた度合い。'
}

EXPANDER_TEXTS = {
    'q_t': """
        ここでは、あなたが人生で**何を大切にしたいか（理想＝情報秩序）**を数値で表現します。
        
        **どう入力する？**
        合計100点となるよう、7つのテーマ（ドメイン）に、あなたにとっての重要度をスライダーで配分してください。正解はありません。あなたの直感が、今のあなたにとっての答えです。
        
        **なぜ入力する？**
        この設定が、あなたの日々の経験を評価するための**個人的な『ものさし』**となります。この「ものさし」がなければ、自分の航海が順調なのか、航路から外れているのかを知ることはできません。
        
        （週に一度など、定期的に見直すのがおすすめです）
        """,
    's_t': """
        ここでは、あなたの**現実の経験（実践秩序）**を記録します。
        
        **どう入力する？**
        頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を、各項目のスライダーで直感的に評価してください。
        
        **なぜ入力する？**
        この「現実」の記録と、先ほど設定した「理想」の羅針盤とを比べることで、両者の間に存在する**『ズレ』**を初めて発見できます。この『ズレ』に気づくことこそが、自己理解と成長の第一歩です。
        """,
    'g_t': """
        この項目は、**あなたの直感的な全体評価**です。
        
        **どう入力する？**
        細かいことは一度忘れて、「で、色々あったけど、今日の自分、全体としては何点だったかな？」という感覚を、一つのスライダーで表現してください。
        
        **なぜ入力する？**
        アプリが計算したスコア（H）と、あなたの直感（G）がどれだけ一致しているか、あるいは**ズレているか**を知るための、非常に重要な手がかりとなります。
        
        **『計算上は良いはずなのに、なぜか気分が晴れない』**といった、言葉にならない違和感や、**『予想外に楽しかった！』**という嬉しい発見など、貴重な自己発見のきっかけになります。
        """,
    'event_log': """
        これは、あなたの航海の**物語**を記録する場所です。
        
        **どう入力するのがおすすめ？**
        **『誰と会った』『何をした』『何を感じた』**といった具体的な出来事や感情を、一言でも良いので書き留めてみましょう。
        
        **なぜ書くのがおすすめ？**
        後でグラフを見たときに、数値だけでは分からない、**幸福度の浮き沈みの『なぜ？』**を解き明かす鍵となります。グラフの「山」や「谷」と、この記録を結びつけることで、あなたの幸福のパターンがより鮮明に見えてきます。
        """,
    'dashboard': """
        ここでは、記録されたデータから、あなたの幸福の**パターンと構造**を可視化します。
        - **💡 インサイト・エンジン:** モデルの計算値(H)とあなたの実感(G)のズレから、自己発見のヒントを提示します。
        - **📈 期間分析とリスク評価 (RHI):** あなたの幸福の**平均点**だけでなく、その**安定性や持続可能性（リスク）**を評価します。
        - **📊 調和度の推移:** あなたの幸福度の時間的な**『物語』**です。グラフの山や谷が、いつ、なぜ起きたのかを探ってみましょう。
        - **📋 全記録データ:** あなたの航海の**『詳細な航海日誌』**です。
        """
}

# --- 1. 計算ロジック & ユーティリティ関数 ---

def calculate_metrics(dataframe: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    dataframe_copy = dataframe.copy()
    if dataframe_copy.empty:
        return dataframe_copy

    for column_name in Q_COLS + S_COLS:
        if column_name in dataframe_copy.columns:
            dataframe_copy[column_name] = pd.to_numeric(dataframe_copy[column_name], errors='coerce').fillna(0)

    s_vectors_normalized = dataframe_copy[S_COLS].values / 100.0
    q_vectors = dataframe_copy[Q_COLS].values
    dataframe_copy['S'] = np.sum(q_vectors * s_vectors_normalized, axis=1)

    def calculate_unity(row):
        q_vec = np.array([float(row[col]) for col in Q_COLS], dtype=float)
        s_vec_raw = np.array([float(row[col]) for col in S_COLS], dtype=float)
        q_sum = np.sum(q_vec)
        if q_sum == 0:
            return 0.0
        # 正規化して分布にする
        q_vec = q_vec / q_sum
        s_sum = np.sum(s_vec_raw)
        if s_sum == 0:
            return 0.0
        s_tilde = s_vec_raw / s_sum
        jsd_sqrt = jensenshannon(q_vec, s_tilde)
        jsd = float(jsd_sqrt) ** 2
        unity = 1.0 - jsd
        return unity

    dataframe_copy['U'] = dataframe_copy.apply(calculate_unity, axis=1)
    dataframe_copy['H'] = alpha * dataframe_copy['S'] + (1 - alpha) * dataframe_copy['U']
    return dataframe_copy


def analyze_discrepancy(dataframe_processed: pd.DataFrame, threshold: int = 20):
    if dataframe_processed.empty:
        return
    latest_record = dataframe_processed.iloc[-1]
    latest_h_normalized = float(latest_record['H'])
    latest_g = float(latest_record.get('g_happiness', 0))
    latest_h = latest_h_normalized * 100.0
    gap = latest_g - latest_h

    st.subheader("💡 インサイト・エンジン")
    with st.expander("▼ これは、モデルの計算値(H)とあなたの実感(G)の『ズレ』に関する分析です", expanded=True):
        if gap > threshold:
            st.info(f"""
                **【幸福なサプライズ！🎉】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく上回りました。
                
                これは、あなたが**まだ言葉にできていない、新しい価値観**を発見したサインかもしれません。
                
                **問い：** 今日の記録を振り返り、あなたが設定した価値観（q_t）では捉えきれていない、予期せぬ喜びの源泉は何だったでしょうか？
                """)
        elif gap < -threshold:
            st.warning(f"""
                **【隠れた不満？🤔】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく下回りました。

                価値観に沿った生活のはずなのに、何かが満たされていないようです。見過ごしている**ストレス要因や、理想と現実の小さなズレ**があるのかもしれません。

                **問い：** 今日の記録を振り返り、あなたの幸福感を静かに蝕んでいた「見えない重り」は何だったでしょうか？
                """)
        else:
            st.success(f"""
                **【順調な航海です！✨】**

                あなたの**実感（G = {int(latest_g)}点）**と、モデルの計算値（H = {int(latest_h)}点）は、よく一致しています。
                
                あなたの自己認識と、現実の経験が、うまく調和している状態です。素晴らしい！
                """)


def calculate_rhi_metrics(dataframe_period: pd.DataFrame, lambda_rhi: float, gamma_rhi: float, tau_rhi: float) -> dict:
    if dataframe_period.empty:
        return {}
    mean_H = dataframe_period['H'].mean()
    std_H = dataframe_period['H'].std(ddof=0)
    frac_below = (dataframe_period['H'] < tau_rhi).mean()
    rhi = mean_H - (lambda_rhi * std_H) - (gamma_rhi * frac_below)
    return {'mean_H': mean_H, 'std_H': std_H, 'frac_below': frac_below, 'RHI': rhi}


def safe_filename(name: str) -> str:
    # ファイル名に使えない文字だけを置換し、空文字列になったらハッシュを使う
    if name is None:
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    name_str = str(name).strip()
    # Windows/Unix のファイル名に悪影響を与える文字を置換
    name_str = re.sub(r'[\/:*?"<>|]+', '_', name_str)
    # 先頭末尾の空白やドットを取り除く
    name_str = name_str.strip(' .')
    if name_str == '':
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    # 長すぎる場合は切り詰める
    return name_str[:120]


def hash_password(password: str) -> str:
    return hashlib.sha256(str(password).encode()).hexdigest()


def check_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == str(hashed_password)


def load_users() -> pd.DataFrame:
    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=['username', 'password_hash']).to_csv(USERS_FILE, index=False)
    try:
        users_df = pd.read_csv(USERS_FILE)
        # 旧ファイルで列が欠けている場合に備える
        if 'username' not in users_df.columns or 'password_hash' not in users_df.columns:
            users_df = pd.DataFrame(columns=['username', 'password_hash'])
        return users_df
    except Exception:
        pd.DataFrame(columns=['username', 'password_hash']).to_csv(USERS_FILE, index=False)
        return pd.read_csv(USERS_FILE)


def save_users(df_users: pd.DataFrame):
    df_users.to_csv(USERS_FILE, index=False)


def calculate_ahp_weights(comparisons: dict, items: list) -> np.ndarray:
    n = len(items)
    matrix = np.ones((n, n), dtype=float)
    item_map = {item: i for i, item in enumerate(items)}

    for (item1, item2), winner in comparisons.items():
        i, j = item_map[item1], item_map[item2]
        if winner == item1:
            matrix[i, j] = 3.0
            matrix[j, i] = 1.0 / 3.0
        elif winner == item2:
            matrix[i, j] = 1.0 / 3.0
            matrix[j, i] = 3.0

    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_eigenvalue_index = np.argmax(np.real(eigenvalues))
    principal_eigenvector = np.real(eigenvectors[:, max_eigenvalue_index])
    weights = principal_eigenvector / np.sum(principal_eigenvector)
    weights = np.clip(weights, 0, None)
    if weights.sum() == 0:
        weights = np.ones_like(weights) / len(weights)
    return (weights * 100).round().astype(int)


def show_welcome_and_guide():
    st.header("ようこそ、最初の航海士へ！「Harmony Navigator」取扱説明書")
    st.markdown("---")
    st.subheader("1. このアプリは、あなたの人生の「航海日誌」です")
    st.markdown("""
    「もっと幸せになりたい」と願いながらも、漠然とした不安や、**「理想（こうありたい自分）」**と**「現実（実際に経験した一日）」**の間の、言葉にならない『ズレ』に、私たちはしばしば悩まされます。
    
    このアプリは、その『ズレ』の正体を可視化し、あなた自身が人生の舵を取るための、**実践的な「航海術」**を提供する目的で開発されました。
    
    これは、あなただけの**「海図（チャート）」**です。この海図を使えば、
    - **自分の現在地**（今の心の状態、つまり『実践秩序』）を客観的に知り、
    - **目的地**（自分が本当に大切にしたいこと、つまり『情報秩序』）を明確にし、
    - **航路**（日々の選択）を、あなた自身で賢明に調整していくことができます。
    
    あなたの人生という、唯一無二の航海。その冒険のパートナーとして、このアプリは生まれました。
    """)
    st.markdown("---")
    st.subheader("2. 最初の航海の進め方（クイックスタート）")
    st.markdown("""
    1.  **乗船手続き（ユーザー登録 / ログイン）:**
        - サイドバーで、あなたの**「船長名（ニックネーム）」**を決め、乗船してください。二回目以降は「ログイン」から、あなたの船を選びます。
    2.  **羅針盤のセット（価値観 `q_t` の設定）:**
        - サイドバーで、あなたが人生で**「何を大切にしたいか」**を、合計100点になるよう配分します。これがあなたの航海の**目的地**を示す、最も重要な羅針盤です。
    3.  **航海日誌の記録（充足度 `s_t` の記録）:**
        - メイン画面で、今日一日を振り返り、**「実際にどう感じたか」**を記録します。日々の**現在地**を確認する作業です。
    4.  **海図の分析（ダッシュボード）:**
        - 記録を続けると、あなたの幸福度の**物語（グラフ）**が見えてきます。羅針盤（理想）と、日々の航路（現実）の**ズレ**から、次の一手を見つけ出しましょう。
    """)
    st.markdown("---")
    st.subheader("🛡️【最重要】あなたのデータとプライバシーは、絶対的に保護されます")
    with st.expander("▼ 解説：クラウド上の「魔法のレストラン」の、少し詳しいお話"):
        st.markdown("""
        「私の個人的な記録が、開発者に見られてしまうのでは？」という不安は、当然のものです。その不安を完全に取り除くために、このアプリがどういう仕組みで動いているのか、少し詳しくお話しさせてください。
        
        このアプリを、**「魔法のレストラン」**に例えてみましょう。
        
        - **あなた（ユーザー）は「お客さん」です。**
        - **私（開発者）は、このレストランで提供される料理の「レシピ（`app.py`）」を考案した、シェフです。**
        - **Streamlit Cloudは、そのレシピ通りに、24時間365日、全自動で料理を提供してくれる「レストランそのもの（サーバー）」です。**
        
        **【あなたの来店と、プライベートな記録ノート】**
        
        あなたがレストランに来店し、「Taroです」と名乗ると、レストランの賢い受付係（アプリの認証ロジック）が、裏手にある巨大で安全な**「顧客ノート保管庫」**へ向かいます。
        
        そして、保管庫の中から**「Taro様専用」と書かれた、あなただけのプライベートな記録ノート（CSVファイル）**を探し出します。もし初めての来店であれば、新しい真っ白なノートに「Taro様専用」と書いて、あなたに渡してくれます。
        
        あなたはそのノートに、その日の食事の感想（日々の記録）を自由に書き込みます。このノートは、他の誰にも見せる必要はありません。
        
        **【シェフ（私）と、レストランの関係】**
        
        ここが最も重要な点です。私は、このレストランの**「レシピを考案したシェフ」**ではありますが、**「レストランの日常業務には一切関与していない」**のです。
        
        私は、レストランの厨房にいませんし、顧客ノート保管庫の鍵も持っていません。したがって、私は**「どの時間に、どのお客さんが来店し、そのプライベートなノートに何を書いたのか」を、知る手段が一切ありません。**
        
        **【結論】**
        - **あなたのデータは、私のPCには一切保存されません。**
        - あなたが入力したデータは、あなたが登録した**「船長名」だけが知っている、あなた専用の「金庫（データファイル）」**に、クラウド上で安全に保管されます。
        - **私を含め、他の誰も、あなたの個人的な記録を、あなたの許可なく見ることは絶対にできません。**
        
        どうぞ、安心して、あなたの心の航海を記録してください。
        """)
    st.markdown("---")
    st.subheader("🧑‍🔬 あなたは、ただのユーザーじゃない。「科学の冒険者」です！")
    st.markdown("""
    最後にお伝えしたい、とても大切なことがあります。あなたがこのアプリを使ってくれることは、単なるテスト協力以上の、大きな意味を持っています。
    
    このアプリの背後にある理論は、まだ**「壮大な仮説」**の段階です。あなたが記録してくれる一つ一つのデータは、**「人間の幸福は、本当に『理想と現実のズレ』の調整プロセスで説明できるのか？」**という、人類の新しい問いを検証するための、**世界で最も貴重な科学的データ**になります。
    """)
    
    st.info("""
    **【研究協力へのお願い（インフォームド・コンセント）】**
    
    もし、ご協力いただけるのであれば、あなたが記録したデータを、**個人が特定できない形に完全に匿名化した上で**、この理論の科学的検証のための研究に利用させていただくことにご同意いただけますでしょうか。
    
    - **約束1：プライバシーの絶対保護**
        - あなたのユーザー名や、個人を特定しうる自由記述（イベントログ）は、研究データから**完全に削除**されます。研究者は、どのデータが誰のものであるかを知ることは絶対にできません。私たちが手にするのは、**誰のものか分からない、完全にランダムなIDが付与された、純粋な数値データだけ**です。
    - **約束2：目的の限定**
        - 収集された統計データは、この幸福理論の検証と発展という、**学術的な目的のためだけ**に利用され、論文や学会発表などで（統計情報として）公開される可能性があります。
    - **約束3：自由な意思**
        - この研究協力は、完全に任意です。同意しない場合でも、アプリの全ての機能を、何ら不利益なくご利用いただけます。あなたの意思が、最も尊重されます。
    
    あなたが記録する一つ一つの航海日誌が、未来の人々のための、新しい「幸福の海図」作りに繋がるかもしれません。
    """)
    st.markdown("---")


# --- 2. メインのアプリケーションロジック ---

def main():
    st.title('🧭 Harmony Navigator (MVP v3.0.0)')
    st.caption('あなたの「理想」と「現実」のズレを可視化し、より良い人生の航路を見つけるための道具')

    # --- ユーザー認証 ---
    st.sidebar.header("👤 ユーザー認証")
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'username_safe' not in st.session_state:
        st.session_state['username_safe'] = None
    if 'consent' not in st.session_state:
        st.session_state['consent'] = False

    users_dataframe = load_users()

    # 既存ユーザー名一覧（そのまま保存されている文字列）
    existing_usernames = users_dataframe['username'].tolist() if not users_dataframe.empty else []
    # 既存ユーザーを safe にした一覧（ファイル名用）
    existing_safe_usernames = users_dataframe['username'].apply(safe_filename).tolist() if not users_dataframe.empty else []

    auth_mode = st.sidebar.radio("モードを選択してください:", ("ログイン", "新規登録"))

    def find_user_row_for_login(login_name: str, users_df: pd.DataFrame):
        # 1) 完全一致で探す（保存されているそのままの名前と比較）
        if login_name in users_df['username'].values:
            return users_df[users_df['username'] == login_name].iloc[0]
        # 2) 入力名を safe に変換して保存名と比較
        login_name_safe = safe_filename(login_name)
        if login_name_safe in users_df['username'].values:
            return users_df[users_df['username'] == login_name_safe].iloc[0]
        # 3) 保存されている名前をすべて safe に変換して、入力の safe 名と比較
        safe_series = users_df['username'].apply(safe_filename)
        mask = (safe_series == login_name) | (safe_series == login_name_safe)
        if mask.any():
            return users_df[mask].iloc[0]
        # 見つからなかったら None を返す
        return None

    if auth_mode == "ログイン":
        if not existing_usernames:
            st.sidebar.warning("登録済みのユーザーがいません。まずは新規登録してください。")
        else:
            login_username = st.sidebar.text_input("ユーザー名:", key="login_username")
            login_password = st.sidebar.text_input("パスワード:", type="password", key="login_password")
            if st.sidebar.button("ログイン", key="login_button"):
                found_user_row = None
                try:
                    found_user_row = find_user_row_for_login(login_username, users_dataframe)
                except Exception:
                    found_user_row = None

                if found_user_row is not None:
                    if check_password(login_password, found_user_row['password_hash']):
                        # 表示用のユーザー名は、保存されている表示名をそのまま使う
                        stored_display_name = str(found_user_row['username'])
                        st.session_state['username'] = stored_display_name
                        st.session_state['username_safe'] = safe_filename(stored_display_name)
                        st.rerun()
                    else:
                        st.sidebar.error("パスワードが間違っています。")
                else:
                    st.sidebar.error("そのユーザー名は存在しません。")

    elif auth_mode == "新規登録":
        new_username_raw = st.sidebar.text_input("新しいユーザー名を入力してください:", key="new_username_input")
        new_password = st.sidebar.text_input("パスワード:", type="password", key="new_password")
        new_password_confirm = st.sidebar.text_input("パスワード（確認用）:", type="password", key="new_password_confirm")
        consent_checkbox = st.sidebar.checkbox("研究協力に関する説明を読み、その内容に同意します。")

        if st.sidebar.button("登録", key="register_button"):
            new_username = new_username_raw.strip()
            if new_username == '':
                st.sidebar.error("ユーザー名を入力してください。")
            else:
                # 既存ユーザーとの重複チェックは safe 名で比較することで
                # 以前のバージョンで保存された safe 名と衝突するケースにも対応する
                new_username_safe = safe_filename(new_username)
                existing_safe_set = set(users_dataframe['username'].apply(safe_filename).tolist()) if not users_dataframe.empty else set()
                if new_username in users_dataframe['username'].values or new_username_safe in existing_safe_set:
                    st.sidebar.error("その名前はすでに使われています。別の名前を選んでください。")
                elif new_password != new_password_confirm:
                    st.sidebar.error("パスワードが一致しません。")
                elif len(new_password) < 8:
                    st.sidebar.error("パスワードは8文字以上で設定してください。")
                else:
                    hashed_password = hash_password(new_password)
                    new_user_row = pd.DataFrame([{'username': new_username, 'password_hash': hashed_password}])
                    users_dataframe = pd.concat([users_dataframe, new_user_row], ignore_index=True)
                    save_users(users_dataframe)
                    st.session_state['username'] = new_username
                    st.session_state['username_safe'] = new_username_safe
                    st.session_state['consent'] = consent_checkbox
                    st.sidebar.success(f"ようこそ、{new_username}さん！登録が完了しました。")
                    st.rerun()

    # --- メインアプリの表示 ---
    if st.session_state.get('username'):
        display_username = st.session_state['username']
        CSV_FILE = CSV_FILE_TEMPLATE.format(st.session_state.get('username_safe', safe_filename(display_username)))

        tab1, tab2, tab3 = st.tabs(["**✍️ 今日の記録**", "**📊 ダッシュボード**", "**🔧 設定とガイド**"])

        # 以降の処理は既存の実装に従って継続されます。
        # （ここから下のタブの処理ブロックは、既にドキュメント内に存在する同一のコードをそのまま使用します）
        
        # --- タブ: 今日の記録 ---
        with tab1:
            st.header(f"ようこそ、{display_username} さん！")

            # データの読み込み（安全に）
            try:
                if os.path.exists(CSV_FILE):
                    dataframe_data = pd.read_csv(CSV_FILE, parse_dates=['date'])
                    if 'date' in dataframe_data.columns:
                        try:
                            dataframe_data['date'] = pd.to_datetime(dataframe_data['date']).dt.date
                        except Exception:
                            pass

                    # 古い形式（個別要素列）からのマイグレーション
                    if 's_health' not in dataframe_data.columns and any(c.startswith('s_element_') for c in dataframe_data.columns):
                        st.info("古いバージョンのデータを検出しました。新しいデータ構造に自動で移行します。")
                        for domain in DOMAINS:
                            element_cols = [c for c in dataframe_data.columns if c.startswith('s_element_') and any(e in c for e in LONG_ELEMENTS.get(domain, []))]
                            if element_cols:
                                dataframe_data['s_' + domain] = dataframe_data[element_cols].mean(axis=1).round()
                        for col in S_COLS:
                            if col not in dataframe_data.columns:
                                dataframe_data[col] = 50
                else:
                    # 初回起動時のカラム定義
                    columns = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log']
                    for elements in LONG_ELEMENTS.values():
                        for element in elements:
                            columns.append(f's_element_{element}')
                    dataframe_data = pd.DataFrame(columns=columns)
            except Exception as e:
                st.error(f"データファイルの読み込み中に予期せぬエラーが発生しました。開発者にご報告ください: {e}")
                dataframe_data = pd.DataFrame()

            today = date.today()

            st.sidebar.subheader('クイックアクセス')
            if not dataframe_data.empty and not dataframe_data[dataframe_data['date'] == today].empty:
                st.sidebar.success(f"✅ 今日の記録 ({today.strftime('%Y-%m-%d')}) は完了しています。")
            else:
                st.sidebar.info(f"ℹ️ 今日の記録 ({today.strftime('%Y-%m-%d')}) はまだありません。")
            st.sidebar.markdown('---')

            st.sidebar.header('⚙️ 価値観 (q_t) の設定')
            st.sidebar.caption('あなたの「理想のコンパス」です。')

            if 'wizard_mode' not in st.session_state:
                st.session_state.wizard_mode = False
            if 'q_wizard_step' not in st.session_state:
                st.session_state.q_wizard_step = 0
            if 'q_comparisons' not in st.session_state:
                st.session_state.q_comparisons = {}
            if 'q_values_from_wizard' not in st.session_state:
                st.session_state.q_values_from_wizard = None

            with st.sidebar.expander("▼ 価値観の配分が難しいと感じる方へ"):
                st.markdown(
                    "合計100点の配分は難しいと感じることがあります。簡単な比較質問に答えるだけで、あなたの価値観のたたき台を提案します。"
                )
                if st.button("対話で価値観を発見する（21の質問）"):
                    st.session_state.wizard_mode = True
                    st.session_state.q_wizard_step = 1
                    st.session_state.q_comparisons = {}
                    st.rerun()

            if st.session_state.wizard_mode:
                pairs = list(itertools.combinations(DOMAINS, 2))
                if 0 < st.session_state.q_wizard_step <= len(pairs):
                    pair = pairs[st.session_state.q_wizard_step - 1]
                    domain1, domain2 = pair
                    st.sidebar.subheader(f"質問 {st.session_state.q_wizard_step}/{len(pairs)}")
                    st.sidebar.write("あなたの人生がより充実するために、今、より重要なのはどちらですか？")
                    col1, col2 = st.sidebar.columns(2)
                    if col1.button(DOMAIN_NAMES_JP[domain1], key=f"btn_{domain1}"):
                        st.session_state.q_comparisons[pair] = domain1
                        st.session_state.q_wizard_step += 1
                        st.rerun()
                    if col2.button(DOMAIN_NAMES_JP[domain2], key=f"btn_{domain2}"):
                        st.session_state.q_comparisons[pair] = domain2
                        st.session_state.q_wizard_step += 1
                        st.rerun()
                else:
                    st.sidebar.success("診断完了！あなたの価値観の推定値です。")
                    estimated_weights = calculate_ahp_weights(st.session_state.q_comparisons, DOMAINS)
                    diff = 100 - np.sum(estimated_weights)
                    if diff != 0:
                        estimated_weights[np.argmax(estimated_weights)] += diff
                    st.session_state.q_values_from_wizard = {domain: weight for domain, weight in zip(DOMAINS, estimated_weights)}
                    st.session_state.wizard_mode = False
                    st.rerun()
            else:
                # 直近の保存値を表示するロジック：保存済みデータがあれば、直近行の q_* を利用してスライダーの初期値を決める
                if st.session_state.q_values_from_wizard is not None:
                    default_q_values = st.session_state.q_values_from_wizard
                    st.session_state.q_values_from_wizard = None
                elif not dataframe_data.empty and all(col in dataframe_data.columns for col in Q_COLS):
                    # 最終行の q_* の値を取り出し、0..1 の正規化値か 0..100 の百分率かを判定してスライダー用に 0..100 に揃える
                    row_q = dataframe_data[Q_COLS].iloc[-1].to_dict()
                    default_q_values = {}
                    for key, val in row_q.items():
                        try:
                            numeric_val = float(val)
                        except Exception:
                            numeric_val = 0.0
                        if numeric_val <= 1.1:
                            display_val = numeric_val * 100.0
                        else:
                            display_val = numeric_val
                        default_q_values[key.replace('q_', '')] = int(round(display_val))
                else:
                    default_q_values = {'health': 15, 'relationships': 15, 'meaning': 15, 'autonomy': 15, 'finance': 15, 'leisure': 15, 'competition': 10}

                # スライダーの初期値をセッションステートに設定します。
                username_safe_for_init = st.session_state.get('username_safe', '')
                init_flag_key = f"q_values_initialized_for_{username_safe_for_init}"
                if not st.session_state.get(init_flag_key, False):
                    for domain in DOMAINS:
                        key_name = f"q_{domain}"
                        default_for_domain = int(default_q_values.get(domain, 14))
                        if key_name not in st.session_state or st.session_state.get(key_name) is None:
                            st.session_state[key_name] = default_for_domain
                    st.session_state[init_flag_key] = True

                # 実際のスライダーを表示します。スライダーは session_state の既定値を優先して表示します。
                q_values = {}
                for domain in DOMAINS:
                    key_name = f"q_{domain}"
                    slider_default = st.session_state.get(key_name, int(default_q_values.get(domain, 14)))
                    q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP[domain], 0, 100, int(slider_default), key=key_name)

                q_total = sum(q_values.values())
                st.sidebar.metric(label="現在の合計値", value=q_total)
                if q_total != 100:
                    st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
                else:
                    st.sidebar.success("合計は100です。入力準備OK！")

            # --- 今日の記録入力 ---
            st.subheader('今日の航海日誌を記録する')
            with st.expander("▼ これは、何のために記録するの？"):
                st.markdown(EXPANDER_TEXTS['s_t'])
            st.markdown("##### 記録する日付")
            target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
            if not dataframe_data.empty and not dataframe_data[dataframe_data['date'] == target_date].empty:
                st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")

            st.markdown("##### 記録モード")
            input_mode = st.radio("記録モード:", ('🚀 クイック・ログ', '🔬 ディープ・ダイブ'), label_visibility="collapsed")
            if 'クイック' in input_mode:
                active_elements = SHORT_ELEMENTS
                mode_string = 'quick'
            else:
                active_elements = LONG_ELEMENTS
                mode_string = 'deep'

            with st.form(key='daily_input_form'):
                st.markdown(f'**{input_mode.split("（")[0]}**')
                s_values = {}
                s_element_values = {}
                col1, col2 = st.columns(2)
                domain_containers = {'health': col1, 'relationships': col1, 'meaning': col1, 'autonomy': col2, 'finance': col2, 'leisure': col2}

                if not dataframe_data.empty and any(c.startswith('s_element_') for c in dataframe_data.columns):
                    latest_s_elements = dataframe_data.filter(like='s_element_').iloc[-1]
                else:
                    # すべてのサブ要素列名を作成してデフォルト値を設定
                    all_element_keys = []
                    for elements in LONG_ELEMENTS.values():
                        for e in elements:
                            all_element_keys.append(f's_element_{e}')
                    latest_s_elements = pd.Series(50, index=all_element_keys)

                for domain, container in domain_containers.items():
                    with container:
                        elements_to_show = active_elements.get(domain, [])
                        if elements_to_show:
                            with st.expander(f"**{DOMAIN_NAMES_JP[domain]}**"):
                                element_scores = []
                                for element in elements_to_show:
                                    default_val = int(latest_s_elements.get(f's_element_{element}', 50))
                                    element_help_text = ELEMENT_DEFINITIONS.get(element, "")
                                    score = st.slider(element, 0, 100, default_val, key=f"s_element_{element}", help=element_help_text)
                                    element_scores.append(score)
                                    s_element_values[f's_element_{element}'] = int(score)
                                if element_scores:
                                    s_values[domain] = int(round(np.mean(element_scores)))

                # competition ドメインは右カラムに表示
                with col2:
                    domain = 'competition'
                    elements_to_show = active_elements.get(domain, [])
                    if elements_to_show:
                        with st.expander(f"**{DOMAIN_NAMES_JP[domain]}**"):
                            default_val = int(latest_s_elements.get(f's_element_{elements_to_show[0]}', 50))
                            element_help_text = ELEMENT_DEFINITIONS.get(elements_to_show[0], "")
                            score = st.slider(elements_to_show[0], 0, 100, default_val, key=f"s_element_{elements_to_show[0]}", help=element_help_text)
                            s_values[domain] = int(score)
                            s_element_values[f's_element_{elements_to_show[0]}'] = int(score)

                st.markdown('**総合的な幸福感 (Gt)**')
                with st.expander("▼ これはなぜ必要？"):
                    st.markdown(EXPANDER_TEXTS['g_t'])
                g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
                st.markdown('**今日の出来事や気づきは？**')
                with st.expander("▼ なぜ書くのがおすすめ？"):
                    st.markdown(EXPANDER_TEXTS['event_log'])
                event_log = st.text_area('', height=100, label_visibility="collapsed")
                submitted = st.form_submit_button('今日の記録を保存する')

            if submitted:
                # フォーム送信時に、表示されているスライダーの実際の値を必ず取得するため、
                # session_state から q_* を再取得して q_values を作り直します。
                # これにより、ウィザード経由でスライダー表示が変わっていても、保存時に
                # 画面上の実際の値が確実に保存されます。
                q_values = {d: int(st.session_state.get(f"q_{d}", 0)) for d in DOMAINS}
                q_total = sum(q_values.values())

                if q_total != 100:
                    st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
                else:
                    # CSV には 0..1 に正規化した q_* を保存します
                    q_normalized = {f'q_{d}': float(v) / 100.0 for d, v in q_values.items()}
                    s_domain_scores = {f's_{d}': int(s_values.get(d, 0)) for d in DOMAINS}
                    consent_status = st.session_state.get('consent', False)
                    new_record = {'date': target_date, 'mode': mode_string, 'consent': consent_status}
                    new_record.update(q_normalized)
                    new_record.update(s_domain_scores)
                    new_record.update(s_element_values)
                    new_record['g_happiness'] = int(g_happiness)
                    new_record['event_log'] = event_log

                    new_dataframe_row = pd.DataFrame([new_record])
                    # 既存の日付行を除去して追加する（上書き）
                    if not dataframe_data.empty and 'date' in dataframe_data.columns:
                        dataframe_data = dataframe_data[dataframe_data['date'] != target_date]
                    dataframe_data = pd.concat([dataframe_data, new_dataframe_row], ignore_index=True, sort=False)

                    # 必要なカラムを確実に揃える
                    all_element_cols = []
                    for elements in LONG_ELEMENTS.values():
                        for e in elements:
                            all_element_cols.append(f's_element_{e}')
                    all_cols = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log'] + all_element_cols
                    for col in all_cols:
                        if col not in dataframe_data.columns:
                            dataframe_data[col] = pd.NA

                    dataframe_data = dataframe_data.sort_values(by='date').reset_index(drop=True)
                    # CSV に保存
                    dataframe_data.to_csv(CSV_FILE, index=False)
                    st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を保存（または上書き）しました！')

                    with st.expander("▼ 保存された記録のサマリー", expanded=True):
                        st.write(f"**総合的幸福感 (G): {g_happiness} 点**")
                        for domain in DOMAINS:
                            st.write(f"- {DOMAIN_NAMES_JP[domain]}: {s_domain_scores.get(domain, 'N/A')} 点")

                    st.balloons()
                    st.rerun()

        # --- タブ: ダッシュボード ---
        with tab2:
            st.header('📊 あなたの航海チャート')
            with st.expander("▼ このチャートの見方"):
                st.markdown(EXPANDER_TEXTS['dashboard'])

            if dataframe_data.empty:
                st.info('まだ記録がありません。まずは「今日の記録」タブから、最初の日誌を記録してみましょう！')
            else:
                dataframe_processed = calculate_metrics(dataframe_data.fillna(0).copy())

                st.subheader("📈 期間分析とリスク評価 (RHI)")
                with st.expander("▼ これは、あなたの幸福の『持続可能性』を評価する指標です", expanded=False):
                    st.markdown("""
                    - **平均調和度 (H̄):** この期間の、あなたの幸福の平均点です。
                    - **変動リスク (σ):** 幸福度の浮き沈みの激しさです。値が小さいほど、安定した航海だったことを示します。
                    - **不調日数割合:** 幸福度が、あなたが設定した「不調」のラインを下回った日の割合です。
                    - **RHI (リスク調整済・幸福指数):** 平均点から、変動と不調のリスクを差し引いた、真の『幸福の実力値』です。この値が高いほど、あなたの幸福が持続可能で、逆境に強いことを示します。
                    """)

                period_options = [7, 30, 90]
                if len(dataframe_processed) < 7:
                    st.info("期間分析には最低7日分のデータが必要です。記録を続けてみましょう！")
                else:
                    default_index = 1 if len(dataframe_processed) >= 30 else 0
                    selected_period = st.selectbox("分析期間を選択してください（日）:", period_options, index=default_index)

                    if len(dataframe_processed) >= selected_period:
                        dataframe_period = dataframe_processed.tail(selected_period)

                        st.markdown("##### あなたのリスク許容度を設定")
                        col1, col2, col3 = st.columns(3)
                        lambda_param = col1.slider("変動(不安定さ)へのペナルティ(λ)", 0.0, 2.0, 0.5, 0.1, help="値が大きいほど、日々の幸福度の浮き沈みが激しいことを、より重く評価します。")
                        gamma_param = col2.slider("下振れ(不調)へのペナルティ(γ)", 0.0, 2.0, 1.0, 0.1, help="値が大きいほど、幸福度が低い日が続くことを、より深刻な問題として評価します。")
                        tau_param = col3.slider("「不調」と見なす閾値(τ)", 0.0, 1.0, 0.5, 0.05, help="この値を下回る日を「不調な日」としてカウントします。")

                        rhi_results = calculate_rhi_metrics(dataframe_period, lambda_param, gamma_param, tau_param)

                        st.markdown("##### 分析結果")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("平均調和度 (H̄)", f"{rhi_results['mean_H']:.3f}")
                        col2.metric("変動リスク (σ)", f"{rhi_results['std_H']:.3f}")
                        col3.metric("不調日数割合", f"{rhi_results['frac_below']:.1%}")
                        col4.metric("リスク調整済・幸福指数 (RHI)", f"{rhi_results['RHI']:.3f}", delta=f"{rhi_results['RHI'] - rhi_results['mean_H']:.3f} (平均との差)")
                    else:
                        st.warning(f"分析には最低{selected_period}日分のデータが必要です。現在の記録は{len(dataframe_processed)}日分です。")

                analyze_discrepancy(dataframe_processed)
                st.subheader('調和度 (H) の推移')
                dataframe_chart = dataframe_processed.copy()
                if 'date' in dataframe_chart.columns:
                    dataframe_chart['date'] = pd.to_datetime(dataframe_chart['date'], errors='coerce')
                    dataframe_chart = dataframe_chart.sort_values('date')
                    st.line_chart(dataframe_chart.set_index('date')['H'])
                else:
                    st.line_chart(dataframe_chart['H'])

                st.subheader('全記録データ')
                st.dataframe(dataframe_processed.round(3))

        # --- タブ: 設定とガイド ---
        with tab3:
            st.header("🔧 設定とガイド")
            st.subheader("アカウント設定")
            st.write(f"ログイン中のユーザー: **{display_username}**")
            if st.button("ログアウト"):
                st.session_state['username'] = None
                st.session_state['username_safe'] = None
                st.rerun()

            st.markdown('---')
            st.subheader("データのエクスポート")
            if not dataframe_data.empty:
                st.download_button(
                    label="📥 全データをダウンロード",
                    data=dataframe_data.to_csv(index=False).encode('utf-8'),
                    file_name=f'harmony_data_{st.session_state.get("username_safe","data")}_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv',
                )

            st.markdown('---')
            st.subheader("アカウント削除")
            st.warning("この操作は取り消せません。あなたの全ての記録データが、サーバーから完全に削除されます。")
            password_for_delete = st.text_input("削除するには、パスワードを入力してください:", type="password", key="delete_password")
            if st.button("このアカウントと全データを完全に削除する", key='delete_account'):
                users_df = load_users()
                if display_username in users_df['username'].values:
                    user_row = users_df[users_df['username'] == display_username].iloc[0]
                    if check_password(password_for_delete, user_row['password_hash']):
                        users_df = users_df[users_df['username'] != display_username]
                        save_users(users_df)
                        try:
                            if os.path.exists(CSV_FILE):
                                os.remove(CSV_FILE)
                        except Exception:
                            pass
                        st.session_state['username'] = None
  
