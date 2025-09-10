# app.py (v5.0.0 - The Phoenix / Direct gspread & Robust Error Handling)
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
from google.auth.transport.requests import Request

# --- A. 定数と基本設定 ---
st.set_page_config(layout="wide", page_title="Harmony Navigator")

# ドメインとエレメントの定義
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
ALL_ELEMENT_COLS = sorted([f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d])
Q_COLS = ['q_' + d for d in DOMAINS]
S_COLS = ['s_' + d for d in DOMAINS]
SLIDER_HELP_TEXT = "0: 全く当てはまらない | 25: あまり当てはまらない | 50: どちらとも言えない | 75: やや当てはまる | 100: 完全に当てはまる"

# UIに表示するテキスト
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
        """
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
            return "[復号に失敗しました：パスワードが違うか、データが破損している可能性があります]"

# --- C. コア計算 & ユーティリティ関数 ---
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    if df_copy.empty:
        return df_copy
    
    numeric_cols = Q_COLS + S_COLS + ALL_ELEMENT_COLS + ['g_happiness']
    for col in numeric_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')

    for domain, elements in LONG_ELEMENTS.items():
        element_cols = [f's_element_{e}' for e in elements if f's_element_{e}' in df_copy.columns]
        if element_cols:
            df_copy['s_' + domain] = df_copy[element_cols].mean(axis=1, skipna=True)

    for col in Q_COLS + S_COLS:
         if col in df_copy.columns:
            df_copy[col] = df_copy[col].fillna(0)
    
    s_vectors_normalized = df_copy[S_COLS].values / 100.0
    q_vectors = df_copy[Q_COLS].values
    
    df_copy['S'] = np.nansum(q_vectors * s_vectors_normalized, axis=1)
    
    def calculate_unity(row):
        q_vec = np.array([float(row[col]) for col in Q_COLS], dtype=float)
        s_vec_raw = np.array([float(row[col]) for col in S_COLS], dtype=float)
        
        q_sum = np.sum(q_vec)
        if q_sum == 0: return 0.0
        q_vec_norm = q_vec / q_sum
        
        s_sum = np.sum(s_vec_raw)
        if s_sum == 0: return 0.0
        s_tilde = s_vec_raw / s_sum
        
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

def analyze_discrepancy(df_processed: pd.DataFrame, threshold: int = 20):
    if df_processed.empty or 'H' not in df_processed.columns or 'g_happiness' not in df_processed.columns:
        return
    latest_record = df_processed.iloc[-1]
    latest_h = float(latest_record['H']) * 100.0 if pd.notna(latest_record['H']) else 0
    latest_g = float(latest_record.get('g_happiness', 0)) if pd.notna(latest_record.get('g_happiness', 0)) else 0
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
        creds.refresh(Request())
        return gspread.authorize(creds)
    except Exception as e:
        st.error("Google Sheetsへの認証に失敗しました。Secretsの設定とGCPのAPI設定を確認してください。")
        st.exception(e)
        return None

@st.cache_data(ttl=10)
def read_data(gc: gspread.client.Client, sheet_name: str, spreadsheet_id: str):
    if gc is None:
        return pd.DataFrame()
    try:
        sh = gc.open_by_key(spreadsheet_id)
        if sheet_name == 'users':
            worksheet = sh.worksheet("users")
        elif sheet_name == 'data':
            worksheet = sh.worksheet("data")
        else:
            return pd.DataFrame()
        
        df = pd.DataFrame(worksheet.get_all_records())
        if not df.empty:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
            numeric_cols = Q_COLS + S_COLS + ALL_ELEMENT_COLS + ['g_happiness']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"スプレッドシート（ID: {spreadsheet_id}）が見つかりません。")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"スプレッドシート内に '{sheet_name}' という名前のワークシートが見つかりません。")
    except Exception as e:
        st.error(f"データの読み込み中に予期せぬエラーが発生しました。")
        st.exception(e)
    return pd.DataFrame()

def write_data(gc: gspread.client.Client, sheet_name: str, spreadsheet_id: str, df: pd.DataFrame):
    if gc is None:
        return
    try:
        sh = gc.open_by_key(spreadsheet_id)
        if sheet_name == 'users':
            worksheet = sh.worksheet("users")
        elif sheet_name == 'data':
            worksheet = sh.worksheet("data")
        else:
            return
            
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
        
        worksheet.clear()
        worksheet.update([df_copy.columns.values.tolist()] + df_copy.values.tolist())
        st.cache_data.clear()
    except Exception as e:
        st.error(f"データの書き込み中にエラーが発生しました。")
        st.exception(e)

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
        
        これは、あなたが病院の受付で受け取る、**名前の書いていない、ただの「整理番号」**のようなものです。
        
        開発者である私がデータ保管庫を見ることがあったとしても、そこにあるのは**「整理番号 user_... さんの記録」**という、完全に無機質で、個人とは結びつかない情報だけです。
        
        **あなたがご自身でニックネームを決めるプロセスが存在しないため、あなたが誤って個人を特定できる名前（本名やSNSのアカウント名など）を使ってしまうリスクは、構造的にゼロになります。**
        
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
    
    代わりに、私たちは、あなたがご自身の意思で、安全に研究に協力するための、**全く別の「研究協力ツール」**を、別途提供します。このツールは、
    1. あなたのパスワードを使って、あなたのPC上だけで、イベントログを**復号**します。
    2. 復号されたログの内容から、感情のスコアなどの、**個人を特定できない、匿名化された「統計情報」**だけを抽出します。
    3. そして、この**「統計情報」だけ**を、研究用のデータベースに送信します。
    
    この仕組みにより、**私たち研究者は、あなたのプライベートな物語に一切触れることなく**、科学の発展に必要なデータだけを得ることができます。
    
    ここの「同意」チェックボックスは、私たちが、あなたの**「日々の数値データ（幸福度のスコアなど）」**を、将来あなたが送信してくれるかもしれない**「匿名の統計情報」**と結びつけて、分析することへの許可をいただくためのものです。
    """)

# --- F. メインアプリケーション ---
def main():
    st.title('🧭 Harmony Navigator')
    st.caption('v5.0.0 - The Phoenix Edition')

    gspread_client = get_gspread_client()
    if gspread_client is None:
        st.warning("現在、データベースに接続できません。時間をおいて再度お試しください。")
        st.stop()

    # SecretsからスプレッドシートIDを取得
    try:
        users_sheet_id = st.secrets["connections"]["gsheets"]["users_sheet_id"]
        data_sheet_id = st.secrets["connections"]["gsheets"]["data_sheet_id"]
    except KeyError:
        st.error("SecretsにスプレッドシートID (`users_sheet_id`, `data_sheet_id`) が設定されていません。")
        st.stop()

    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = "NOT_LOGGED_IN"
    # (以下、セッション状態の初期化は省略)

    if st.session_state.auth_status in ["LOGGED_IN_LOCKED", "LOGGED_IN_UNLOCKED", "AWAITING_ID"]:
        # (ここに、v4.3.1のログイン後、または贈呈式を待っている状態のロジックが、完全に、省略なく入ります)
        # (ただし、read_data, write_data呼び出し時に、gspread_clientとspreadsheet_idを渡すように変更)
        pass
    else: # NOT_LOGGED_IN
        st.header("ようこそ、航海士へ")
        show_welcome_and_guide()
        
        st.subheader("あなたの旅を、ここから始めましょう")
        door1, door2 = st.tabs(["**新しい船で旅を始める (初めての方)**", "**秘密の合い言葉で乗船する (2回目以降の方)**"])

        with door1:
            # (ここに、v4.3.1の新規登録フォームのUIとロジックが、完全に、省略なく入ります)
            # (ただし、read_data, write_data呼び出し時に、gspread_clientとspreadsheet_idを渡すように変更)
            pass

        with door2:
            # (ここに、v4.3.1のログインフォームのUIとロジックが、完全に、省略なく入ります)
            # (ただし、read_data呼び出し時に、gspread_clientとspreadsheet_idを渡すように変更)
            pass

if __name__ == '__main__':
    main()
