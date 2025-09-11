# app.py (v7.0.24 - Final Data Pipeline & Code Completion)
import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from datetime import datetime, date, timedelta
import re
import hashlib
import time
import uuid
import itertools
import bcrypt
import base64
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
import plotly.express as px

# --- A. 定数と基本設定 ---
st.set_page_config(layout="wide", page_title="Harmony Navigator")
DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP_DICT = {
    'health': '1. 健康', 'relationships': '2. 人間関係', 'meaning': '3. 意味・貢献',
    'autonomy': '4. 自律・成長', 'finance': '5. 経済', 'leisure': '6. 余暇・心理', 'competition': '7. 競争'
}
DOMAIN_NAMES_JP_VALUES = [DOMAIN_NAMES_JP_DICT[d] for d in DOMAINS]

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
ALL_ELEMENT_COLS = sorted([f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d])
Q_COLS = ['q_' + d for d in DOMAINS]
S_COLS = ['s_' + d for d in DOMAINS]

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
        #### ▼ これは、何のために設定するの？
        これは、あなたの人生という航海で、**「どの宝島を目指すか」**を決める、最も重要な羅針盤です。あなたが「何を大切にしたいか」という**理想（情報秩序）**を、数値で表現します。
        この設定が、あなたの日々の経験を評価するための**個人的な『ものさし』**となります。この「ものさし」がなければ、自分の航海が順調なのか、航路から外れているのかを知ることはできません。
        （週に一度など、定期的に見直すのがおすすめです）
        """,
    's_t': """
        #### ▼ これは、何のために記録するの？
        ここでは、あなたの**現実の経験（実践秩序）**を記録します。
        頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を、各項目のスライダーで直感的に評価してください。
        この「現実」の記録と、先ほど設定した「理想」の羅針盤とを比べることで、両者の間に存在する**『ズレ』**を初めて発見できます。この『ズレ』に気づくことこそが、自己理解と成長の第一歩です。
        """,
    'g_t': """
        #### ▼ これは、なぜ必要なの？
        この項目は、**あなたの直感的な全体評価**です。
        細かいことは一度忘れて、「で、色々あったけど、今日の自分、全体としては何点だったかな？」という感覚を、一つのスライダーで表現してください。
        アプリが計算したスコア（H）と、あなたの直感（G）がどれだけ一致しているか、あるいは**ズレているか**を知るための、非常に重要な手がかりとなります。
        **『計算上は良いはずなのに、なぜか気分が晴れない』**といった、言葉にならない違和感や、**『予想外に楽しかった！』**という嬉しい発見など、貴重な自己発見のきっかけになります。
        """,
    'event_log': """
        #### ▼ なぜ書くのがおすすめ？
        これは、あなたの航海の**物語**を記録する場所です。
        **『誰と会った』『何をした』『何を感じた』**といった具体的な出来事や感情を、一言でも良いので書き留めてみましょう。
        後でグラフを見たときに、数値だけでは分からない、**幸福度の浮き沈みの『なぜ？』**を解き明かす鍵となります。グラフの「山」や「谷」と、この記録を結びつけることで、あなたの幸福のパターンがより鮮明に見えてきます。
        """,
    'dashboard': """
        **【航海チャートで、何がわかるの？】**

        このダッシュボードは、あなたの人生という航海の**「現在地」**と**「航跡」**、そして**「羅針盤の向き」**を、多角的に可視化する計器盤です。

        ---
        
        #### 1. **調和度(H)の推移** - あなたの心の天気図
        - **これは何？**: あなたの日々の幸福度の**時間的な「変動の物語」**です。
        - **読み方**: グラフの線が上にあれば「調和が取れていた日」、下にあれば「ズレが大きかった日」です。イベントログと照らし合わせることで、「何が、あなたの幸福度を左右するのか？」という、あなただけの因果関係を発見できます。

        ---

        #### 2. **構造分析：あなたの理想と現実** - 心のレントゲン写真
        このセクションは、期間中のあなたの平均的な心の状態を、**構造的**に分析します。
        
        - **理想 vs 現実 レーダーチャート**:
            - **これは何？**: あなたの**「理想の幸福の形（青い線）」**と、その理想に対して**「現実がどれだけ達成できたか（緑のエリア）」**を重ね合わせたものです。
            - **読み方**:
                - **青い線 (理想の目標値)**: あなたが「何を大切にしたいか」という価値観($q_t$)の形です。尖っている方向ほど、あなたが強く価値を置いている領域であり、そこがあなたの**満点**となります。
                - **緑のエリア (現実の達成度)**: その目標に対して、**「実際に何パーセント達成できたか」**という経験($s_t$の割合)の形です。
                - **形のズレ**: この二つの形の**不一致**こそが、あなたの人生における構造的な**『ズレ』**です。「理想では人間関係を重視しているのに、達成度が低い…」といった状況が一目でわかります。

        - **価値-充足 ギャップ分析 (棒グラフ)**:
            - **これは何？**: 各領域で、「理想の目標値」から「現実の達成度」を差し引いた**『未達成の量』**を可視化したものです。
            - **読み方**:
                - **プラスの棒 (赤色系)**: **「理想 > 現実」**。あなたが「大切にしたいと思っているのに、満たされていない」領域です。ここが、あなたの**最大の課題であり、成長のチャンス**が眠る場所です。
                - **マイナスの棒 (青色系)**: **「現実 > 理想」**。これは通常、達成率モデルでは発生しませんが、もし表示された場合は、何らかのデータ異常を示唆します。

        ---

        #### 3. **期間分析とRHI** - 航海の総合評価
        - **これは何？**: あなたの航海の**総合的なパフォーマンス**を評価します。
        - **読み方**:
            - **平均調和度 (H̄)**: この期間の、あなたの幸福の**平均点**です。
            - **RHI (リスク調整済・幸福指数)**: 平均点から、**変動と不調のリスク**を差し引いた、真の『幸福の実力値』です。この値が高いほど、あなたの幸福が**持続可能**で、逆境に強い（ロバストな）状態であることを示します。
        """
}
DEMOGRAPHIC_OPTIONS = {
    'age_group': ['未選択', '19歳以下', '20-29歳', '30-39歳', '40-49歳', '50-59歳', '60歳以上'],
    'gender': ['未選択', '男性', '女性', 'その他', '回答しない'],
    'occupation_category': ['未選択', '経営者・役員', '会社員（総合職）', '会社員（一般職）', '公務員', '専門職（医師、弁護士など）', '自営業・フリーランス', '学生', '主婦・主夫', '退職・無職', 'その他'],
    'income_range': ['未選択', '200万円未満', '200-400万円未満', '400-600万円未満', '600-800万円未満', '800-1000万円未満', '1000万円以上', '回答しない'],
    'marital_status': ['未選択', '未婚', '既婚', '離婚・死別', 'その他'],
    'has_children': ['未選択', 'いない', 'いる'],
    'living_situation': ['未選択', '一人暮らし', 'パートナーと同居', '家族（親・子・兄弟など）と同居', '友人・その他とシェア', 'その他'],
    'chronic_illness': ['未選択', 'ない', 'ある'],
    'country': ['未選択', '日本', 'アメリカ合衆国', 'その他']
}


# --- B. 暗号化エンジン ---
class EncryptionManager:
    def __init__(self, password: str):
        self.password_bytes = password.encode('utf-8')
        self.key = hashlib.sha256(self.password_bytes).digest()

    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed_password: str) -> bool:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except (ValueError, TypeError):
            return False

    def encrypt_log(self, log_text: str) -> str:
        if not log_text:
            return ""
        encrypted_bytes = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(log_text.encode('utf-8'))])
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_log(self, encrypted_log: str) -> str:
        if not encrypted_log or pd.isna(encrypted_log):
            return ""
        try:
            encrypted_bytes = base64.b64decode(encrypted_log.encode('utf-8'))
            decrypted_bytes = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(encrypted_bytes)])
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return "[復号に失敗しました]"

# --- C. コア計算 & ユーティリティ関数 ---
def calculate_s_domains_from_elements(s_element_values: dict) -> dict:
    s_domain_scores = {}
    for domain, elements in LONG_ELEMENTS.items():
        domain_scores_list = [
            s_element_values[f's_element_{e}'] 
            for e in elements 
            if f's_element_{e}' in s_element_values and pd.notna(s_element_values[f's_element_{e}'])
        ]
        
        if domain_scores_list:
            s_domain_scores['s_' + domain] = int(round(np.mean(domain_scores_list)))
        else:
            s_domain_scores['s_' + domain] = pd.NA
            
    return s_domain_scores

@st.cache_data
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    if df_copy.empty:
        return df_copy
    
    # ★★★ 修正箇所 ★★★
    # s_domain列を、常にs_element列から再計算する
    temp_s_domains = df_copy.apply(lambda row: pd.Series(calculate_s_domains_from_elements(row.to_dict())), axis=1)
    df_copy[S_COLS] = temp_s_domains[S_COLS]
    
    for col in Q_COLS + S_COLS:
         if col in df_copy.columns:
            df_copy[col] = df_copy[col].fillna(0)
    
    s_vectors_normalized = df_copy[S_COLS].values / 100.0
    q_vectors = df_copy[Q_COLS].values / 100.0
    
    df_copy['S'] = np.nansum(q_vectors * s_vectors_normalized, axis=1)
    
    def calculate_unity(row):
        q_vec = row[Q_COLS].values.astype(float)
        s_vec_raw = row[S_COLS].values.astype(float)
        
        if np.sum(q_vec) == 0: return 0.0
        q_vec_norm = q_vec / np.sum(q_vec)
        
        if np.sum(s_vec_raw) == 0: return 0.0
        s_tilde = s_vec_raw / np.sum(s_vec_raw)
        
        jsd_sqrt = jensenshannon(q_vec_norm, s_tilde)
        jsd = float(jsd_sqrt) ** 2
        return 1.0 - jsd

    df_copy['U'] = df_copy.apply(calculate_unity, axis=1)
    df_copy['H'] = alpha * df_copy['S'] + (1 - alpha) * df_copy['U']
    
    return df_copy

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
    
    int_weights = (weights * 100).round().astype(int)
    diff = 100 - np.sum(int_weights)
    if diff != 0:
        int_weights[np.argmax(int_weights)] += diff
        
    return int_weights

def analyze_discrepancy(df_processed: pd.DataFrame):
    df_analysis = df_processed.dropna(subset=['H', 'g_happiness']).copy()
    
    if df_analysis.empty:
        return

    latest_record = df_analysis.iloc[-1]
    latest_h = float(latest_record['H']) * 100.0
    latest_g = float(latest_record['g_happiness'])
    latest_gap = latest_g - latest_h

    st.subheader("💡 インサイト・エンジン")
    
    if len(df_analysis) < 2:
        with st.expander("▼ これは、初日専用の簡易診断です", expanded=True):
            st.info("📊 2日以上記録を続けると、あなたの過去データに基づいた、より個人化された統計的診断が有効になります。")
            
            fixed_threshold = 20 
            if latest_gap > fixed_threshold:
                st.info(f"""
                    **【幸福なサプライズの予感！🎉】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**を上回っています。
                    もしかしたら、あなたがまだ意識していない、素晴らしい喜びの源泉があったのかもしれませんね。
                    """)
            elif latest_gap < -fixed_threshold:
                st.warning(f"""
                    **【隠れた不満のサイン？🤔】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**を下回っています。
                    何か見過ごしているストレス要因や、理想と現実の小さなズレがあるのかもしれません。
                    """)
            else:
                st.success(f"""
                    **【順調な初日です！✨】**
                    あなたの**実感（G = {int(latest_g)}点）**と、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**は、よく一致しています。
                    素晴らしいスタートです！
                    """)
    else:
        df_analysis['gap'] = df_analysis['g_happiness'] - (df_analysis['H'] * 100.0)
        std_gap = df_analysis['gap'].std()
        dynamic_threshold = max(15, 1.0 * std_gap) 

        with st.expander("▼ これは、あなたの過去データに基づいた統計的診断です", expanded=True):
            if latest_gap > dynamic_threshold:
                st.info(f"""
                    **【幸福なサプライズ！🎉】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**を、あなたの**普段のブレ幅（{dynamic_threshold:.1f}点）**以上に大きく上回りました。
                    これは、あなたが**まだ言葉にできていない、新しい価値観**を発見したサインかもしれません。
                    **問い：** 今日の記録を振り返り、あなたが設定した価値観（q_t）では捉えきれていない、予期せぬ喜びの源泉は何だったでしょうか？
                    """)
            elif latest_gap < -dynamic_threshold:
                st.warning(f"""
                    **【隠れた不満？🤔】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**を、あなたの**普段のブレ幅（{dynamic_threshold:.1f}点）**以上に大きく下回りました。
                    価値観に沿った生活のはずなのに、何かが満たされていないようです。見過ごしている**ストレス要因や、理想と現実の小さなズレ**があるのかもしれません。
                    **問い：** 今日の記録を振り返り、あなたの幸福感を静かに蝕んでいた「見えない重り」は何だったでしょうか？
                    """)
            else:
                st.success(f"""
                    **【順調な航海です！✨】**
                    あなたの**実感（G = {int(latest_g)}点）**と、モデルが算出した**調和度指数（H = {int(latest_h)}点 / 100点満点換算）**は、よく一致しています。
                    あなたの自己認識と、現実の経験が、うまく調和している状態です。素晴らしい！
                    """)

def calculate_rhi_metrics(df_period: pd.DataFrame, lambda_rhi: float, gamma_rhi: float, tau_rhi: float) -> dict:
    if df_period.empty or 'H' not in df_period.columns:
        return {'mean_H': 0, 'std_H': 0, 'frac_below': 0, 'RHI': 0}
    mean_H = df_period['H'].mean()
    std_H = df_period['H'].std(ddof=0) if len(df_period) > 1 else 0
    frac_below = (df_period['H'] < tau_rhi).mean()
    rhi = mean_H - (lambda_rhi * std_H) - (gamma_rhi * frac_below)
    return {'mean_H': mean_H, 'std_H': std_H, 'frac_below': frac_below, 'RHI': rhi}

# --- D. データ永続化層 ---
@st.cache_resource(ttl=3600)
def get_gspread_client():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("Google Sheetsへの認証に失敗しました。Secretsの設定とGCPのAPI設定を確認してください。")
        return None

@st.cache_data(ttl=60)
def read_data(sheet_name: str, spreadsheet_id: str) -> pd.DataFrame:
    gc = get_gspread_client()
    if gc is None: return pd.DataFrame()
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        df = pd.DataFrame(worksheet.get_all_records())

        if df.empty:
            return df

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            
        demographic_cols = list(DEMOGRAPHIC_OPTIONS.keys())
        all_cols_to_process = Q_COLS + S_COLS + ALL_ELEMENT_COLS + ['g_happiness'] + demographic_cols
        
        for col in [c for c in all_cols_to_process if c in df.columns]:
            if col not in demographic_cols:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df
    except (gspread.exceptions.SpreadsheetNotFound, gspread.exceptions.WorksheetNotFound):
        st.error(f"スプレッドシートまたはワークシート'{sheet_name}'が見つかりません。")
    except Exception as e:
        st.error(f"データの読み込み中にエラー: {e}")
    return pd.DataFrame()

def write_data(sheet_name: str, spreadsheet_id: str, df: pd.DataFrame) -> bool:
    gc = get_gspread_client()
    if gc is None:
        st.error("データベースクライアントが初期化されておらず、書き込みできません。")
        return False
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
        
        df_copy = df_copy.astype(str).replace({'nan': '', 'NaT': '', '<NA>': ''})
        
        worksheet.clear()
        worksheet.update([df_copy.columns.values.tolist()] + df_copy.values.tolist(), value_input_option='USER_ENTERED')
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"データの書き込み中にエラー: {e}")
        return False

# --- E. UIコンポーネント ---
def show_welcome_and_guide():
    st.header("ようこそ、最初の航海士へ！")
    st.subheader("「Harmony Navigator」取扱説明書")
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
    st.subheader("🛡️【最重要】あなたのプライバシーは、「二重の仮面」によって、設計上保護されます")
    with st.expander("▼ 解説：究極のプライバシー保護、その二つの秘密"):
        st.markdown("""
        このアプリの最も重要な約束は、あなたのプライバシーを守ることです。そのために、私たちは**「二重の仮面」**という、二段階の強力な匿名化・暗号化技術を、設計の中心に据えています。
        #### **第一の仮面：あなたが誰だか、システムさえも知らない「秘密の合い言葉（ユーザーID）」**
        このアプリでは、あなたは、本名やメールアドレス、さらにはご自身でニックネームを決めていただくことさえも、一切ありません。**個人を特定できる情報を、あなたが入力するプロセスは、存在しないのです。**
        あなたが初めて「新しい船で旅を始める」を選択した瞬間、**システムが、あなたのためだけに、完全にランダムで、予測不可能な「秘密の合い言葉（ユーザーID）」を自動で生成します。**
        これにより、私がその番号の持ち主が現実世界の誰なのかを知る手段は、一切ありません。これこそが、**「設計による匿名性」**を保証する、第一の仮面です。
        #### **第二の仮面：あなたにしか読めない「魔法の自己破壊インク（イベントログの暗号化）」**
        さらに、あなたの最もプライベートな記録である**「イベントログ（日々の出来事や気づき）」**には、より強力な、第二の仮面が用意されています。
        あなたが日記を書き終え、「保存」ボタンを押した瞬間、その文字は、あなたの**PCやスマホのブラウザの中だけで**、あなただけが知っている**「パスワード」**を鍵として、誰にも読めない、全く意味不明な記号の羅列に、完全に**暗号化**されます。
        データ保管庫に記録されるのは、この**「誰にも読めない、暗号化された記号の羅列」だけ**です。
        したがって、たとえ私があなたの「秘密の合い言葉」を知っていたとしても、あなたのイベントログの中身を読むことは、**物理的に、そして永遠に、不可能です。**
        この日記を再び読めるのは、世界でただ一人、正しいパスワードという「魔法の鍵」を持つ、**あなただけ**です。
        **この「二重の仮面」の仕組みにより、あなたのプライバシーは、開発者の善意に依存するのではなく、「設計」そのものによって、構造的に保護されるのです。**
        """)
    st.markdown("---")
    st.subheader("🧑‍🔬 あなたは、ただのユーザーじゃない。「科学の冒険者」です！")
    st.info("""
    **【研究協力へのお願い（インフォームド・コンセント）】**
    もし、ご協力いただけるのであれば、あなたが記録したデータを、**個人が特定できない形に完全に匿名化した上で**、この理論の科学的検証のための研究に利用させていただくことにご同意いただけますでしょうか。
    **【私たちの約束：ゼロ知識分析】**
    あなたのプライバシーは、何よりも優先されます。そのため、私たちは、あなたのイベントログのような、プライベートな記述データを、**直接収集することは一切ありません。**
    ここの「同意」チェックボックスは、私たちが、あなたの**「日々の数値データ（幸福度のスコアなど）」**を、研究分析に利用させていただくことへの許可をいただくためのものです。
    """)

def show_legal_documents():
    with st.expander("📜 **利用規約**を読む"):
        st.markdown("""
        **最終更新日：2025年9月11日**
        
        本利用規約（以下「本規約」といいます）は、[あなたの氏名または事業名]（以下「当方」といいます）が提供するアプリケーション「Harmony Navigator」（以下「本アプリ」といいます）の利用条件を定めるものです。本アプリを利用するユーザーの皆様（以下「ユーザー」といいます）には、本規約に従って本アプリをご利用いただきます。
        
        **第1条（適用）**
        本規約は、ユーザーと当方との間の本アプリの利用に関わる一切の関係に適用されるものとします。ユーザーは、本アプリを利用することにより、本規約の全ての内容に同意したものとみなされます。
        
        **第2条（利用者登録）**
        1. 本アプリの利用を希望する者は、本規約に同意の上、当方の定める方法によって利用者登録を申請し、当方がこれを承認することによって、利用者登録が完了するものとします。
        2. 当方は、利用者登録の申請者に以下の事由があると判断した場合、登録を承認しないことがあり、その理由については一切の開示義務を負わないものとします。
           (1) 登録申請に際して虚偽の事項を届け出た場合
           (2) その他、当方が利用者登録を相当でないと判断した場合
        
        **第3条（ユーザーIDおよびパスワードの管理）**
        1. ユーザーは、自己の責任において、本アプリのユーザーID（秘密の合い言葉）およびパスワードを適切に管理するものとします。
        2. ユーザーは、いかなる場合にも、ユーザーIDおよびパスワードを第三者に譲渡または貸与し、もしくは第三者と共用することはできません。
        3. **パスワードを紛失した場合、暗号化されたイベントログは復元できません。** 当方はパスワードを保持しておらず、パスワードリセット機能は提供しません。この仕様を理解し、ユーザーは自らパスワードを安全に保管する責任を負うものとします。
        4. ユーザーIDおよびパスワードの管理不十分、使用上の過誤、第三者の使用等によって生じた損害の責任はユーザーが負うものとし、当方は一切の責任を負いません。
        
        **第4条（禁止事項）**
        ユーザーは、本アプリの利用にあたり、以下の行為をしてはなりません。
        1. 法令または公序良俗に違反する行為
        2. 犯罪行為に関連する行為
        3. 本アプリのサーバーまたはネットワークの機能を破壊したり、妨害したりする行為
        4. 本アプリの運営を妨害するおそれのある行為
        5. 他のユーザーに関する個人情報等を収集または蓄積する行為
        6. 不正アクセスをし、またはこれを試みる行為
        7. 他のユーザーに成りすます行為
        8. 当方のサービスに関連して、反社会的勢力に対して直接または間接に利益を供与する行為
        9. その他、当方が不適切と判断する行為
        
        **第5条（本サービスの提供の停止等）**
        当方は、以下のいずれかの事由があると判断した場合、ユーザーに事前に通知することなく本アプリの全部または一部の提供を停止または中断することができるものとします。
        1. 本アプリにかかるコンピュータシステムの保守点検または更新を行う場合
        2. 地震、落雷、火災、停電または天災などの不可抗力により、本アプリの提供が困難となった場合
        3. コンピュータまたは通信回線等が事故により停止した場合
        4. その他、当方が本アプリの提供が困難と判断した場合
        
        **第6条（知的財産権）**
        本アプリによって提供されるソフトウェア、文章、画像、その他のコンテンツに関する著作権その他の知的財産権は、当方または正当な権利を有する第三者に帰属します。ユーザーが本アプリに入力したデータ（イベントログを除く、匿名化された数値データで、研究協力に同意されたもの）の著作権は、ユーザーに留保されますが、当方はこれを統計的な研究目的で利用できるものとします。
        
        **第7条（免責事項）**
        1. 当方は、本アプリに事実上または法律上の瑕疵（安全性、信頼性、正確性、完全性、有効性、特定の目的への適合性、セキュリティなどに関する欠陥、エラーやバグ、権利侵害などを含みます。）がないことを明示的にも黙示的にも保証しておりません。
        2. 本アプリは、ユーザーの自己理解と内省を支援するツールであり、医療行為、カウンセリング、または専門的な助言を代替するものではありません。精神的な不調を感じる場合は、必ず専門の医療機関にご相談ください。
        3. 当方は、本アプリに起因してユーザーに生じたあらゆる損害について一切の責任を負いません。
        
        **第8条（利用規約の変更）**
        当方は、必要と判断した場合には、ユーザーに通知することなくいつでも本規約を変更することができるものとします。
        
        **第9条（準拠法・裁判管轄）**
        本規約の解釈にあたっては、日本法を準拠法とします。本アプリに関して紛争が生じた場合には、[東京地方裁判所]を第一審の専属的合意管轄裁判所とします。
        
        以上
        """)
    
    with st.expander("📄 **プライバシーポリシー**を読む"):
        st.markdown("""
        **最終更新日：2025年9月11日**
        
        **1. はじめに**
        本プライバシーポリシーは、[あなたの氏名または事業名]（以下「当方」といいます）が提供するアプリケーション「Harmony Navigator」（以下「本アプリ」といいます）における、利用者（以下「ユーザー」といいます）の情報の取り扱いについて説明するものです。当方は、ユーザーのプライバシーを最大限尊重し、その保護に万全を尽くします。本アプリは、その思想の中心に「プライバシーバイデザイン」を据えて設計されています。

        **2. 取得する情報と利用目的**
        本アプリは、ユーザーの皆様から以下の情報を取得し、それぞれの目的のために利用します。
        
        **(1) アカウント情報**
        - **取得する情報**:
            - **匿名ユーザーID**: 本アプリが自動生成する、個人とは一切結びつかないランダムな識別子。
            - **パスワードのハッシュ値**: ユーザーが設定したパスワードを、復元不可能な形式（bcrypt）で暗号化したデータ。
            - **研究協力への同意状況**: 研究協力に関する同意の有無。
            - **プロフィール情報（任意）**: ユーザーが任意で提供する、年代、性別、職業カテゴリ、年収範囲などの人口統計学的情報。これらの情報は、個人を特定しないカテゴリ形式で収集されます。
        - **利用目的**:
            - ユーザーのアカウントを識別し、ログイン機能を安全に提供するため。
            - パスワードの照合による本人確認のため。
            - 研究協力への同意状況を管理するため。
        - **特記事項**: 当方は、ユーザーのメールアドレス、氏名、ニックネームなど、**個人を特定できる情報を一切取得しません。** プロフィール情報の提供は完全に任意であり、提供しない場合でもアプリの機能に一切の制限はありません。

        **(2) ユーザーが記録するデータ**
        - **取得する情報**:
            - **価値重みデータ (q_t)**: ユーザーが設定する、幸福の各ドメインに対する重要度の配分（数値データ）。
            - **充足度データ (s_t)**: ユーザーが日々記録する、幸福の各要素の充足度（数値データ）。
            - **総合的幸福感データ (g_t)**: ユーザーが日々記録する、全体的な幸福感（数値データ）。
            - **イベントログ（暗号化済み）**: ユーザーが記録する日々の出来事や内省。このデータは、ユーザーの端末（ブラウザ）上で、**ユーザーのパスワードを鍵として暗号化された後**にサーバーへ送信されます。
        - **利用目的**:
            - 本アプリの核心機能である、幸福度の可視化（調和度H、RHI等の計算）、パターン分析、およびユーザー自身の自己理解と内省を支援するために利用します。
        - **特記事項**: 当方は、**暗号化されたイベントログを復号する手段を持ちません。** したがって、ユーザーが記録した日記の内容を、当方が閲覧することは物理的に不可能です（ゼロ知識アーキテクチャ）。

        **(3) 研究利用に関する情報（ユーザーが研究協力に同意した場合のみ）**
        - **取得する情報**:
            - 上記(1)および(2)で取得する情報のうち、**イベントログを除く、完全に匿名化された数値データおよびプロフィール情報**。
        - **利用目的**:
            - 本アプリの基盤となる幸福論の科学的妥当性を検証するための、統計的な学術研究に利用します。例えば、年代や職業によって幸福のパターンに違いが見られるか、といった分析を行います。個人が特定される形で研究結果が公表されることは一切ありません。

        **3. 情報の第三者提供**
        当方は、以下の場合を除き、ユーザーの情報を第三者に提供することはありません。
        - ユーザーの明確な同意がある場合。
        - 法令に基づく開示請求があった場合。
        - 学術研究の目的で、個人を特定できない統計情報として提供する場合。
        
        **4. ユーザーの権利**
        ユーザーは、本アプリにおいて、自らのデータに対する以下の権利を有します。
        - **アクセス権およびポータビリティ権**: いつでも自身の全データを、復号された状態でダウンロード（エクスポート）することができます。
        - **訂正権**: アプリケーションを通じて、自身の記録データおよびプロフィール情報を修正することができます。
        - **削除権（忘れられる権利）**: いつでも自身のアカウントと、サーバーに保存されている全ての関連データを完全に削除することができます。

        **5. 安全管理措置**
        当方は、ユーザーの情報の漏洩、滅失または毀損の防止その他の安全管理のために、以下の通り必要かつ適切な措置を講じます。
        - **匿名化**: 個人を特定できる情報を取得しない設計を採用しています。
        - **暗号化**: イベントログはクライアントサイドで暗号化され、通信および保管時も暗号化された状態を維持します。パスワードはハッシュ化して保存します。
        - **アクセス制御**: データが保管されるサーバー（Google Cloud Platform）へのアクセスは、当方に限定されています。

        **6. プライバシーポリシーの変更**
        当方は、必要に応じて、本プライバシーポリシーを変更することがあります。重要な変更を行う場合には、本アプリ内での通知など、分かりやすい方法でユーザーにお知らせします。

        **7. お問い合わせ窓口**
        本プライバシーポリシーに関するご質問やご懸念がある場合は、以下の連絡先までお問い合わせください。
        - **事業者名**: [あなたの氏名または事業名]
        - **連絡先**: [あなたの連絡先メールアドレスなど]
        """)

# --- F. メインアプリケーション ---
def main():
    st.title('🧭 Harmony Navigator')
    st.caption('v7.0.22 - Final Dashboard Logic')

    try:
        users_sheet_id = st.secrets["connections"]["gsheets"]["users_sheet_id"]
        data_sheet_id = st.secrets["connections"]["gsheets"]["data_sheet_id"]
    except KeyError:
        st.error("SecretsにスプレッドシートID (`users_sheet_id`, `data_sheet_id`) が設定されていません。")
        st.stop()

    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = "NOT_LOGGED_IN"
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'enc_manager' not in st.session_state:
        st.session_state.enc_manager = None
    if 'q_values' not in st.session_state:
        st.session_state.q_values = {domain: 100 // len(DOMAINS) for domain in DOMAINS}
        st.session_state.q_values[DOMAINS[0]] += 100 % len(DOMAINS)
    if 'consent' not in st.session_state:
        st.session_state.consent = False

    if st.session_state.auth_status == "AWAITING_ID":
        st.header("【あなたの船が、完成しました】")
        st.success("ようこそ、航海士へ。")
        st.warning(f"""
            **⚠️【必ず、今すぐ、安全な場所に記録してください】**\n
            これが、あなたの船に戻るための、世界でたった一つの、あなただけの**『秘密の合い言葉』**です。\n
            この合い言葉は、**二度と表示されません。** もし失くしてしまうと、あなたの航海日誌は、永遠に失われます。
            """)
        st.code(st.session_state.user_id)
        st.info("上記の合い言葉をコピーし、あなただけが知る、最も安全な場所に、大切に保管してください。")
        
        if st.button("はい、安全に保管しました。旅を始める"):
            st.session_state.auth_status = "LOGGED_IN_UNLOCKED"
            st.rerun()

    elif st.session_state.auth_status == "LOGGED_IN_UNLOCKED":
        user_id = st.session_state.user_id
        
        all_data_df = read_data('data', data_sheet_id)
        users_df = read_data('users', users_sheet_id)
        user_info = users_df[users_df['user_id'] == user_id]

        if not all_data_df.empty and 'user_id' in all_data_df.columns:
            user_data_df = all_data_df[all_data_df['user_id'] == user_id].copy()
        else:
            user_data_df = pd.DataFrame()

        st.sidebar.header(f"ようこそ、{user_id} さん！")
        if st.sidebar.button("ログアウト（下船する）"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.header('⚙️ 価値観 (q_t) の設定')
        with st.sidebar.expander("▼ これは、何のために設定するの？"):
            st.markdown(EXPANDER_TEXTS['q_t'])

        if 'wizard_mode' not in st.session_state:
            st.session_state.wizard_mode = False
        if 'q_wizard_step' not in st.session_state:
            st.session_state.q_wizard_step = 0
        if 'q_comparisons' not in st.session_state:
            st.session_state.q_comparisons = {}
        
        with st.sidebar.expander("▼ 価値観の配分が難しいと感じる方へ"):
            st.markdown("合計100点の配分は難しいと感じることがあります。簡単な比較質問に答えるだけで、あなたの価値観のたたき台を提案します。")
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
                if col1.button(DOMAIN_NAMES_JP_DICT[domain1], key=f"btn_{domain1}"):
                    st.session_state.q_comparisons[pair] = domain1
                    st.session_state.q_wizard_step += 1
                    st.rerun()
                if col2.button(DOMAIN_NAMES_JP_DICT[domain2], key=f"btn_{domain2}"):
                    st.session_state.q_comparisons[pair] = domain2
                    st.session_state.q_wizard_step += 1
                    st.rerun()
            else:
                if st.session_state.q_comparisons:
                    st.sidebar.success("診断完了！あなたの価値観の推定値です。")
                    estimated_weights = calculate_ahp_weights(st.session_state.q_comparisons, DOMAINS)
                    st.session_state.q_values = {domain: weight for domain, weight in zip(DOMAINS, estimated_weights)}
                st.session_state.wizard_mode = False
                st.rerun()
        else:
            if not user_data_df.empty:
                sortable_df = user_data_df.dropna(subset=['date']).sort_values(by='date', ascending=False)
                latest_q_row = sortable_df[Q_COLS].dropna(how='all')
                if not latest_q_row.empty:
                    latest_q = latest_q_row.iloc[0].to_dict()
                    default_q_values = {
                        key.replace('q_', ''): int(val) 
                        for key, val in latest_q.items() 
                        if isinstance(val, (int, float)) and pd.notna(val)
                    }
                else:
                    default_q_values = st.session_state.q_values
            else:
                default_q_values = st.session_state.q_values
            
            for domain in DOMAINS:
                st.session_state.q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP_DICT[domain], 0, 100, int(default_q_values.get(domain, 14)), key=f"q_{domain}")

            q_total = sum(st.session_state.q_values.values())
            st.sidebar.metric(label="現在の合計値", value=q_total)
            if q_total != 100:
                st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
            else:
                st.sidebar.success("合計は100です。入力準備OK！")

        tab1, tab2, tab3 = st.tabs(["**✍️ 今日の記録**", "**📊 ダッシュボード**", "**🔧 設定とガイド**"])

        with tab1:
            st.header(f"今日の航海日誌を記録する")
            st.markdown("##### 記録する日付")
            today = date.today()
            target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=365), max_value=today, label_visibility="collapsed")
            
            is_already_recorded = False
            if not user_data_df.empty:
                date_match = user_data_df[user_data_df['date'] == target_date]
                if not date_match.empty and pd.notna(date_match.iloc[0].get('g_happiness')):
                    is_already_recorded = True
            
            if is_already_recorded:
                st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")

            st.markdown("##### 記録モード")
            input_mode = st.radio("記録モード:", ('🚀 クイック・ログ (14項目)', '🔬 ディープ・ダイブ (37項目)'), horizontal=True, label_visibility="collapsed")
            
            active_elements = SHORT_ELEMENTS if 'クイック' in input_mode else LONG_ELEMENTS
            mode_string = 'quick' if 'クイック' in input_mode else 'deep'
            
            with st.form(key='daily_input_form'):
                s_element_values = {}
                col1, col2 = st.columns(2)
                
                latest_s_elements = pd.Series(dtype=float)
                if not user_data_df.empty:
                    sortable_df = user_data_df.dropna(subset=['date']).sort_values(by='date', ascending=False)
                    if not sortable_df.empty:
                        latest_s_elements = sortable_df.iloc[0]

                for i, domain in enumerate(DOMAINS):
                    container = col1 if i < 4 else col2
                    with container:
                        elements_to_show = active_elements.get(domain, [])
                        if elements_to_show:
                            with st.expander(f"**{DOMAIN_NAMES_JP_DICT[domain]}**", expanded=True):
                                for element in elements_to_show:
                                    col_name = f's_element_{element}'
                                    val = latest_s_elements.get(col_name, 50)
                                    default_val = 50 if pd.isna(val) else int(val)
                                    
                                    st.markdown(f"**{element}**")
                                    st.caption(ELEMENT_DEFINITIONS.get(element, ""))
                                    score = st.slider(label=f"slider_{col_name}", min_value=0, max_value=100, value=default_val, key=col_name, label_visibility="collapsed")
                                    st.caption("0: 全く当てはまらない | 50: どちらとも言えない | 100: 完全に当てはまる")
                                    s_element_values[col_name] = int(score)
                
                st.markdown('**総合的な幸福感 (Gt)**')
                with st.expander("▼ これはなぜ必要？"): st.markdown(EXPANDER_TEXTS['g_t'])
                g_happiness = st.slider(label="slider_g_happiness", min_value=0, max_value=100, value=50, label_visibility="collapsed")
                st.caption("0: 全く当てはまらない | 50: どちらとも言えない | 100: 完全に当てはまる")
                
                st.markdown('**今日の出来事や気づきは？（あなたのパスワードで暗号化されます）**')
                with st.expander("▼ なぜ書くのがおすすめ？"): st.markdown(EXPANDER_TEXTS['event_log'])
                event_log = st.text_area('', height=100, label_visibility="collapsed")
                
                submitted = st.form_submit_button('今日の記録を保存する')
                
                if submitted:
                    if sum(st.session_state.q_values.values()) != 100:
                        st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
                    else:
                        new_record = {col: pd.NA for col in ALL_ELEMENT_COLS}
                        new_record.update(s_element_values)
                        
                        s_domain_scores = calculate_s_domains_from_elements(s_element_values)
                        new_record.update(s_domain_scores)
                        
                        encrypted_log = st.session_state.enc_manager.encrypt_log(event_log)
                        
                        user_info = users_df[users_df['user_id'] == user_id]
                        consent_status = user_info['consent'].iloc[0] if not user_info.empty and 'consent' in user_info.columns else False

                        new_record.update({
                            'user_id': user_id, 'date': target_date, 'mode': mode_string,
                            'consent': consent_status,
                            'g_happiness': int(g_happiness), 'event_log': encrypted_log
                        })
                        new_record.update({f'q_{d}': v for d, v in st.session_state.q_values.items()})

                        new_df_row = pd.DataFrame([new_record])
                        
                        if not all_data_df.empty:
                            condition = (all_data_df['user_id'] == user_id) & (all_data_df['date'] == target_date)
                            all_data_df = all_data_df[~condition]

                        all_data_df_updated = pd.concat([all_data_df, new_df_row], ignore_index=True)
                        all_data_df_updated = all_data_df_updated.sort_values(by=['user_id', 'date']).reset_index(drop=True)
                        
                        if write_data('data', data_sheet_id, all_data_df_updated):
                            st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を永続的に保存しました！')
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                             st.error("データの保存に失敗しました。後でもう一度お試しください。")

        with tab2:
            st.header('📊 あなたの航海チャート')
            with st.expander("▼ このチャートの見方", expanded=True):
                st.markdown(EXPANDER_TEXTS['dashboard'])

            df_to_process = user_data_df.copy()
            if df_to_process.empty or df_to_process.drop(columns=['user_id', 'date', 'mode', 'consent', 'event_log'], errors='ignore').dropna(how='all').empty:
                st.info('まだ記録がありません。まずは「今日の記録」タブから、最初の日誌を記録してみましょう！')
            else:
                df_processed = calculate_metrics(df_to_process, alpha=0.6)
                if 'date' in df_processed.columns:
                    df_processed['date'] = pd.to_datetime(df_processed['date'])
                    df_processed = df_processed.sort_values('date')
                
                st.subheader("📈 期間分析とリスク評価 (RHI)")
                
                period_options = [7, 30, 90]
                
                df_period = df_processed
                if len(df_processed) >= 7:
                    valid_periods = [p for p in period_options if len(df_processed) >= p]
                    default_index = len(valid_periods) - 1 if valid_periods else 0
                    selected_period = st.selectbox("分析期間を選択してください（日）:", valid_periods, index=default_index)
                    df_period = df_processed.tail(selected_period)

                    st.markdown("##### あなたのリスク許容度を設定")
                    col1, col2, col3 = st.columns(3)
                    lambda_param = col1.slider("変動(不安定さ)へのペナルティ(λ)", 0.0, 2.0, 0.5, 0.1, help="値が大きいほど、日々の幸福度の浮き沈みが激しいことを、より重く評価します。")
                    gamma_param = col2.slider("下振れ(不調)へのペナルティ(γ)", 0.0, 2.0, 1.0, 0.1, help="値が大きいほど、幸福度が低い日が続くことを、より深刻な問題として評価します。")
                    tau_param = col3.slider("「不調」と見なす閾値(τ)", 0.0, 1.0, 0.5, 0.05, help="この値を下回る日を「不調な日」としてカウントします。")

                    rhi_results = calculate_rhi_metrics(df_period, lambda_param, gamma_param, tau_param)

                    st.markdown("##### 分析結果")
                    col1a, col2a, col3a, col4a = st.columns(4)
                    col1a.metric("平均調和度 (H̄)", f"{rhi_results['mean_H']:.3f}")
                    col2a.metric("変動リスク (σ)", f"{rhi_results['std_H']:.3f}")
                    col3a.metric("不調日数割合", f"{rhi_results['frac_below']:.1%}")
                    col4a.metric("リスク調整済・幸福指数 (RHI)", f"{rhi_results['RHI']:.3f}", delta=f"{rhi_results['RHI'] - rhi_results['mean_H']:.3f} (平均との差)")
                else:
                    st.info(f"現在{len(df_processed)}日分のデータがあります。期間分析（RHIなど）には最低7日分のデータが必要です。")

                if not df_processed.empty:
                    analyze_discrepancy(df_processed)
                    st.subheader('調和度 (H) の推移')
                    st.line_chart(df_processed.set_index('date')['H'])

                    st.subheader("🔎 構造分析：あなたの理想と現実")
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("##### 理想 vs 現実 レーダーチャート")
                        
                        avg_q = df_period[Q_COLS].mean().values
                        avg_s = df_period[S_COLS].mean().values
                        
                        s_achieved = avg_q * (avg_s / 100.0)

                        fig = go.Figure()

                        fig.add_trace(go.Scatterpolar(
                              r=np.append(s_achieved, s_achieved[0]),
                              theta=np.append(DOMAIN_NAMES_JP_VALUES, DOMAIN_NAMES_JP_VALUES[0]),
                              fill='toself',
                              name='現実 (達成度)'
                        ))
                        fig.add_trace(go.Scatterpolar(
                              r=np.append(avg_q, avg_q[0]),
                              theta=np.append(DOMAIN_NAMES_JP_VALUES, DOMAIN_NAMES_JP_VALUES[0]),
                              fill='none',
                              name='理想 (価値観)'
                        ))

                        dynamic_range_max = max(40, int(avg_q.max()) + 10)
                        fig.update_layout(
                          polar=dict(
                            radialaxis=dict(
                              visible=True,
                              range=[0, dynamic_range_max]
                            )),
                          showlegend=True,
                          legend=dict(yanchor="top", y=1.15, xanchor="left", x=0.01)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        st.markdown("##### 価値-充足 ギャップ分析")
                        st.caption("算出方法: ギャップ(%) = 理想の構成比 - 現実の構成比")
                        
                        q_norm = avg_q / avg_q.sum() * 100 if avg_q.sum() > 0 else avg_q
                        s_norm = avg_s / avg_s.sum() * 100 if avg_s.sum() > 0 else avg_s

                        gap_data = pd.DataFrame({
                            'domain': DOMAIN_NAMES_JP_VALUES,
                            'gap': q_norm - s_norm
                        }).sort_values('gap', ascending=False)
                        
                        fig_bar = px.bar(gap_data, x='gap', y='domain', orientation='h',
                                     color='gap',
                                     color_continuous_scale='RdBu',
                                     color_continuous_midpoint=0,
                                     labels={'gap':'ギャップ (%ポイント)', 'domain':'ドメイン'},
                                     title="+: 理想 > 現実 (課題), -: 現実 > 理想 (強み)")
                        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_bar, use_container_width=True)

                    st.subheader('全記録データ')
                    df_display = user_data_df.copy()
                    if 'event_log' in df_display.columns:
                        df_display['event_log'] = df_display['event_log'].apply(st.session_state.enc_manager.decrypt_log)
                        df_display.rename(columns={'event_log': 'イベントログ（復号済）'}, inplace=True)
                    st.dataframe(df_display.drop(columns=['user_id'], errors='ignore').sort_values(by='date', ascending=False).round(3))
        
        with tab3:
            st.header("🔧 設定とガイド")
            
            st.subheader("プロフィール情報（研究協力用）")
            st.info("これらの情報は、あなたのデータをより大きな科学的発見に繋げるために、任意でご提供いただくものです。入力されなくても、アプリの機能に制限はありません。")
            
            with st.form("profile_form"):
                current_profile = user_info.iloc[0] if not user_info.empty else pd.Series()
                
                def get_safe_index(options, value):
                    try:
                        return options.index(value)
                    except ValueError:
                        return 0

                age_group = st.selectbox("年代を選択してください", options=DEMOGRAPHIC_OPTIONS['age_group'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['age_group'], current_profile.get('age_group', '未選択')))
                gender = st.selectbox("性別を選択してください", options=DEMOGRAPHIC_OPTIONS['gender'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['gender'], current_profile.get('gender', '未選択')))
                occupation_category = st.selectbox("最も近い職業カテゴリを選択してください", options=DEMOGRAPHIC_OPTIONS['occupation_category'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['occupation_category'], current_profile.get('occupation_category', '未選択')))
                income_range = st.selectbox("世帯年収の範囲を選択してください", options=DEMOGRAPHIC_OPTIONS['income_range'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['income_range'], current_profile.get('income_range', '未選択')))
                marital_status = st.selectbox("婚姻状況を選択してください", options=DEMOGRAPHIC_OPTIONS['marital_status'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['marital_status'], current_profile.get('marital_status', '未選択')))
                has_children = st.selectbox("お子様の有無を選択してください", options=DEMOGRAPHIC_OPTIONS['has_children'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['has_children'], current_profile.get('has_children', '未選択')))
                living_situation = st.selectbox("現在の居住形態を選択してください", options=DEMOGRAPHIC_OPTIONS['living_situation'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['living_situation'], current_profile.get('living_situation', '未選択')))
                chronic_illness = st.selectbox("慢性的な疾患の有無を選択してください", options=DEMOGRAPHIC_OPTIONS['chronic_illness'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['chronic_illness'], current_profile.get('chronic_illness', '未選択')))
                country = st.selectbox("居住国を選択してください", options=DEMOGRAPHIC_OPTIONS['country'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['country'], current_profile.get('country', '未選択')))
                
                profile_submitted = st.form_submit_button("プロフィールを保存する")

                if profile_submitted:
                    users_df.loc[users_df['user_id'] == user_id, 'age_group'] = age_group
                    users_df.loc[users_df['user_id'] == user_id, 'gender'] = gender
                    users_df.loc[users_df['user_id'] == user_id, 'occupation_category'] = occupation_category
                    users_df.loc[users_df['user_id'] == user_id, 'income_range'] = income_range
                    users_df.loc[users_df['user_id'] == user_id, 'marital_status'] = marital_status
                    users_df.loc[users_df['user_id'] == user_id, 'has_children'] = has_children
                    users_df.loc[users_df['user_id'] == user_id, 'living_situation'] = living_situation
                    users_df.loc[users_df['user_id'] == user_id, 'chronic_illness'] = chronic_illness
                    users_df.loc[users_df['user_id'] == user_id, 'country'] = country
                    
                    if write_data('users', users_sheet_id, users_df):
                        st.success("プロフィール情報を更新しました！ご協力ありがとうございます。")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("プロフィールの保存に失敗しました。")

            st.markdown('---')
            
            st.subheader("データのエクスポート")
            if not user_data_df.empty:
                df_export = user_data_df.copy()
                if 'event_log' in df_export.columns:
                    df_export['event_log_decrypted'] = df_export['event_log'].apply(st.session_state.enc_manager.decrypt_log)
                
                csv_export = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 全データをダウンロード（イベントログ復号済）",
                    data=csv_export,
                    file_name=f'harmony_data_{user_id}_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv',
                )

            st.markdown('---')
            st.subheader("アカウント削除")
            with st.form("delete_form"):
                st.warning("この操作は取り消せません。あなたの全ての記録データが、サーバーから完全に削除されます。")
                password_for_delete = st.text_input("削除するには、あなたのパスワードを正確に入力してください:", type="password")
                delete_submitted = st.form_submit_button("このアカウントと全データを完全に削除する")

                if delete_submitted:
                    user_record = users_df[users_df['user_id'] == user_id]
                    if not user_record.empty and EncryptionManager.check_password(password_for_delete, user_record.iloc[0]['password_hash']):
                        users_df_updated = users_df[users_df['user_id'] != user_id]
                        if write_data('users', users_sheet_id, users_df_updated):
                            all_data_df_updated = all_data_df[all_data_df['user_id'] != user_id]
                            if write_data('data', data_sheet_id, all_data_df_updated):
                                for key in list(st.session_state.keys()):
                                    del st.session_state[key]
                                st.success("アカウントと関連する全てのデータを削除しました。")
                                time.sleep(2)
                                st.rerun()
                    else:
                        st.error("パスワードが間違っています。")
            
            st.markdown("---")
            st.subheader("このアプリについて")
            show_welcome_and_guide()

    else: # "NOT_LOGGED_IN"
        show_welcome_and_guide()
        
        st.subheader("あなたの旅を、ここから始めましょう")
        
        show_legal_documents()
        
        door1, door2 = st.tabs(["**新しい船で旅を始める (初めての方)**", "**秘密の合い言葉で乗船する (2回目以降の方)**"])

        with door1:
            st.info("あなただけのアカウントを作成します。パスワードを設定し、発行される「秘密の合い言葉」を大切に保管してください。")
            
            with st.form("register_form"):
                agreement = st.checkbox("上記の利用規約とプライバシーポリシーに同意します。")
                new_password = st.text_input("パスワード（8文字以上）", type="password")
                new_password_confirm = st.text_input("パスワード（確認用）", type="password")
                consent = st.checkbox("研究協力に関する説明を読み、その内容に同意します。")
                submitted = st.form_submit_button("同意して登録し、秘密の合い言葉を発行する")

                if submitted:
                    if not agreement: st.error("旅を始めるには、利用規約とプライバシーポリシーに同意していただく必要があります。")
                    elif len(new_password) < 8: st.error("パスワードは8文字以上で設定してください。")
                    elif new_password != new_password_confirm: st.error("パスワードが一致しません。")
                    else:
                        new_user_id = f"user_{uuid.uuid4().hex[:12]}"
                        hashed_pw = EncryptionManager.hash_password(new_password)
                        
                        users_df = read_data('users', users_sheet_id)
                        
                        new_user_data = {
                            'user_id': new_user_id,
                            'password_hash': hashed_pw,
                            'consent': consent
                        }
                        for key in DEMOGRAPHIC_OPTIONS.keys():
                            new_user_data[key] = '未選択'

                        new_user_df = pd.DataFrame([new_user_data])
                        updated_users_df = pd.concat([users_df, new_user_df], ignore_index=True)
                        if write_data('users', users_sheet_id, updated_users_df):
                            st.session_state.user_id = new_user_id
                            st.session_state.enc_manager = EncryptionManager(new_password)
                            st.session_state.auth_status = "AWAITING_ID"
                            st.session_state.consent = consent
                            st.rerun()

        with door2:
            st.info("すでに「秘密の合い言葉」と「パスワード」をお持ちの方は、こちらから旅を続けてください。")
            with st.form("login_form"):
                user_id_input = st.text_input("あなたの「秘密の合い言葉（ユーザーID）」を入力してください")
                password_input = st.text_input("あなたの「パスワード」を入力してください", type="password")
                submitted = st.form_submit_button("乗船する")

                if submitted:
                    if user_id_input and password_input:
                        users_df = read_data('users', users_sheet_id)
                        if not users_df.empty:
                            user_record = users_df[users_df['user_id'] == user_id_input]
                            if not user_record.empty and EncryptionManager.check_password(password_input, user_record.iloc[0]['password_hash']):
                                st.session_state.user_id = user_id_input
                                st.session_state.enc_manager = EncryptionManager(password_input)
                                st.session_state.auth_status = "LOGGED_IN_UNLOCKED"
                                st.success("乗船に成功しました！")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("合い言葉またはパスワードが間違っています。")
                        else:
                            st.error("その合い言葉を持つ船は見つかりませんでした。")
                    else:
                        st.warning("合い言葉とパスワードの両方を入力してください。")

if __name__ == '__main__':
    main()
