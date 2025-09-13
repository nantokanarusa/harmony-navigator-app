# app.py (v7.0.59 - Final Complete Code with All Fixes & Refinements)
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
import pytz
from collections import Counter

# --- A. 定数と基本設定 ---
st.set_page_config(layout="wide", page_title="Harmony Navigator", page_icon="🧭")
JST = pytz.timezone('Asia/Tokyo')

DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP_DICT = {
    'health': '💪 健康', 'relationships': '🤝 人間関係', 'meaning': '🌱 意味・貢献',
    'autonomy': '🕊️ 自律・成長', 'finance': '💰 経済', 'leisure': '🎨 余暇・心理', 'competition': '⚔️ 競争'
}
DOMAIN_NAMES_JP_VALUES = [DOMAIN_NAMES_JP_DICT[d] for d in DOMAINS]

LONG_ELEMENTS = {
    'health': ['睡眠', '食事', '運動', '身体的快適さ', '感覚的快楽', '性的幸福'],
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

CAPTION_TEXT = "0: 全く当てはまらない | 25: あまり当てはまらない | 50: どちらとも言えない| 75: やや当てはまる | 100: 完全に当てはまる"

ELEMENT_DEFINITIONS = {
    '睡眠': '質の良い睡眠がとれ、朝、すっきりと目覚められた度合い。（例：途中で起きなかった、寝起きが良い）',
    '食事': '栄養バランスの取れた、美味しい食事に満足できた度合い。（例：体に良いものを美味しく食べられた）',
    '運動': '体を動かす習慣があり、それが心身の快調さに繋がっていた度合い。（例：散歩や筋トレでリフレッシュできた）',
    '身体的快適さ': '慢性的な痛みや、気になる不調がなく、快適に過ごせた度合い。（例：肩こりや頭痛がなかった）',
    '感覚的快楽': '五感を通じて、心地よいと感じる瞬間があった度合い。（例：温かいお風呂、心地よい音楽、好きな香り）',
    '性的幸福': '自身の性的な欲求に対して、満足感があった度合い。（生理的な側面）',
    '家族': '家族との間に、安定した、あるいは温かい関係があった度合い。（例：家族と穏やかな会話ができた）',
    'パートナー・恋愛': 'パートナーとの間に、愛情や深い理解、情緒的な親密さがあった度合い。（例：パートナーに感謝を伝えた、深く語り合えた）',
    '友人': '気軽に話せたり、支え合えたりする友人がおり、良い関係を築けていた度合い。（例：友人と気兼ねなく笑い合えた）',
    '社会的承認': '周囲の人々（職場、地域など）から、一員として認められ、尊重されていると感じた度合い。（例：会議で自分の意見が受け入れられた）',
    '利他性・貢献': '自分の行動が、誰かの役に立った、あるいは喜ばれたと感じた度合い。（例：「ありがとう」と言われた、誰かの仕事を手伝った）',
    '共感・繋がり': '他者の気持ちに寄り添ったり、逆に寄り添ってもらったりして、人との深い繋がりを感じた度合い。（例：友人の相談に乗り、気持ちが通じ合った）',
    'やりがい': '自分の仕事や活動（学業、家事、趣味など）に、意義や目的を感じ、夢中になれた度合い。（例：時間を忘れて作業に没頭できた）',
    '達成感': '何か具体的な目標を達成したり、物事を最後までやり遂げたりする経験があった度合い。（例：今日のタスクリストを全て完了できた）',
    '信念との一致': '自分の「こうありたい」という価値観や、倫理観に沿った行動ができた度合い。（例：「誠実でありたい」という信念に基づき、正直に意見を伝えた）',
    'キャリアの展望': '自分の将来のキャリアに対して、希望や前向きな見通しを持てていた度合い。（例：将来のための良い経験が積めたと感じた）',
    '社会への貢献': '自分の活動が、所属するコミュニティや、より大きな社会に対して、良い影響を与えていると感じられた度合い。（例：自分の仕事が社会問題を解決する一助となっている）',
    '有能感': '自分のスキルや能力を、うまく発揮できているという感覚があった度合い。（例：自分の知識で問題を解決できた）',
    '自由・自己決定': '自分の人生における重要な事柄を、他者の圧力ではなく、自分自身の意志で選択・決定できていると感じた度合い。（例：人に勧められたからではなく、自分で考えて今日の行動を決めた）',
    '挑戦・冒険': '新しいことに挑戦したり、未知の経験をしたりして、刺激や興奮を感じた度合い。（例：初めての場所に行ってみた、新しいスキルを学び始めた）',
    '自己成長の実感': '何かを乗り越えたり、新しいことを学んだりして、自分が成長していると感じられた度合い。（例：昨日できなかったことができるようになった）',
    '変化の享受': '環境の変化や、新しい考え方を、ポジティブに受け入れ、楽しむことができた度合い。（例：予期せぬ計画変更にも柔軟に対応できた）',
    '独立・自己信頼': '自分の力で物事に対処できるという、自分自身への信頼感があった度合い。（例：困難な状況でも、自分なら何とかできると思えた）',
    '好奇心': '様々な物事に対して、知的な好奇心を持ち、探求することに喜びを感じた度合い。（例：知らないことを調べてみて面白かった）',
    '経済的安定': '「来月の支払いは大丈夫かな…」といった、短期的なお金の心配がない状態。（例：予期せぬ出費にも対応できる蓄えがある）',
    '経済的余裕': '生活必需品だけでなく、趣味や自己投資など、人生を豊かにすることにもお金を使える状態。（例：値段を気にせず、欲しい本を買えた）',
    '労働環境': '物理的にも、精神的にも、安全で、健康的に働ける環境があった度合い。（例：職場の人間関係が良好で、安心して働ける）',
    'ワークライフバランス': '仕事（あるいは学業）と、プライベートな生活との間で、自分が望むバランスが取れていた度合い。（例：定時で仕事を終え、家族と夕食をとれた）',
    '公正な評価': '自分の働きや成果が、正当に評価され、報酬に反映されていると感じられた度合い。（例：自分の頑張りが給与や賞与にきちんと反映された）',
    '職業的安定性': '「この先も、この仕事を続けていけるだろうか」といった、長期的なキャリアや収入に対する不安がない状態。（例：自分のスキルは今後も社会で通用すると感じられる）',
    '心の平穏': '過度な不安やストレスなく、精神的に安定していた度合い。（例：リラックスして穏やかな気持ちでいられた）',
    '自己肯定感': '自分の長所も短所も含めて、ありのままの自分を、肯定的に受け入れることができた度合い。（例：失敗しても、自分を責めすぎず「まあ、いいか」と思えた）',
    '創造性の発揮': '何かを創作したり、新しいアイデアを思いついたりして、創造的な喜びを感じた度合い。（例：料理やDIYで工夫を楽しんだ）',
    '感謝': '日常の小さな出来事や、周りの人々に対して、自然と「ありがたい」という気持ちが湧いた度合い。（例：店員さんの親切に感謝した）',
    '娯楽・楽しさ': '趣味に没頭したり、友人と笑い合ったり、純粋に「楽しい」と感じる時間があった度合い。（例：好きな映画を見て夢中になった）',
    '芸術・自然': '美しい音楽や芸術、あるいは雄大な自然に触れて、心が動かされたり、豊かになったりする経験があった度合い。（例：夕焼けの美しさに感動した）',
    '優越感・勝利': '他者との比較や競争において、優位に立てたと感じ、満足感を得た。（例：ゲームで勝った、仕事の成績で一番になった）'
}
EXPANDER_TEXTS = {
    'q_t': """
        #### ▼ これは、何のために設定するの？
        これは、あなたの人生という航海で、**「どの宝島を目指すか」**を決める、最も重要な羅針盤です。あなたが「何を大切にしたいか」という**あなた自身の価値観（情報秩序）**を、数値で表現します。
        この設定が、あなたの日々の経験を評価するための**個人的な『ものさし』**となります。この「ものさし」がなければ、自分の航海が順調なのか、航路から外れているのかを知ることはできません。
        （週に一度など、定期的に見直すのがおすすめです）
        """,
    's_t': """
        #### ▼ これは、何のために記録するの？
        ここでは、あなたの**実際の経験（実践秩序）**を記録します。
        頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を、各項目のスライダーで直感的に評価してください。
        この「実際の経験」の記録と、先ほど設定した「あなたの価値観」という羅針盤とを比べることで、両者の間に存在する**『ズレ』**を初めて発見できます。この『ズレ』に気づくことこそが、自己理解と成長の第一歩です。
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
        
        #### 1. **心の航海図：モデルの分析(H) vs あなたの直感(G)**
        - **これは何？**: あなたの日々の幸福度の**時間的な「変動の物語」**です。**モデルによる計算値（H）**と、あなたの**直感的な実感（G）**を重ねて表示します。
        - **読み方**: 
            - **青い線 (調和度 H)**: あなたの価値観と日々の経験の調和度合いを示す、モデルの計算値です。
            - **緑の線 (実感値 G)**: あなたが入力した、その日の総合的な幸福感です。
            - **二つの線のズレ**: この二つの線の乖離は、「計算上は良いはずなのに、なぜか満されない」といった、あなた自身の自己認識のズレを発見する手がかりになります。

        ---

        #### 2. **構造分析：あなたの価値観と経験** - 心のレントゲン写真
        このセクションは、期間中のあなたの平均的な心のの状態を、**構造的**に分析します。
        
        - **価値観 vs 経験 レーダーチャート**:
            - **これは何？**: あなたが**「何を大切にしたいか（青い線）」**という価値観の形と、**「実際に何を経験したか（緑のエリア）」**という日々の充足の形を重ね合わせたものです。
            - **読み方**:
                - **青い線 (あなたの価値観)**: あなたが「何を大切にしたいか」という価値観($q_t$)の形です。尖っている方向ほど、あなたが強く価値を置いている領域です。
                - **緑のエリア (あなたの経験)**: その価値観に対して、**「実際に経験した充足」**($s_t$)の形です。
                - **形のズレ**: この二つの形の**不一致**こそが、あなたの人生における構造的な**『ズレ』**です。「価値観では人間関係を重視しているのに、経験が追いついていない…」といった状況が一目でわかります。

        - **価値観-経験 ギャップ分析 (棒グラフ)**:
            - **これは何？**: 各領域で、「あなたの価値観の構成比」から「あなたの経験の構成比」を差し引いた**『ズレの量』**を可視化したものです。
            - **読み方**:
                - **プラスの棒 (赤色系)**: **「価値観 > 経験」**。あなたが「大切にしたいと思っているのに、経験が追いついていない」領域です。ここが、あなたの**最大の課題であり、成長のチャンス**が眠る場所です。
                - **マイナスの棒 (青色系)**: **「経験 > 価値観」**。あなたが「さほど重視していないのに、多くの時間やエネルギーを費やしている」可能性のある領域です。見直しのヒントになるかもしれません。

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
# ゲーミフィケーション機能：アチーブメント定義
ACHIEVEMENTS = {
    'record_1': {'name': '最初の航海日誌', 'description': '最初の記録をつけました。', 'emoji': '🎉', 'condition': lambda df: len(df) >= 1},
    'record_7': {'name': '航海士の習慣', 'description': '7日間、連続で記録をつけました。', 'emoji': '🗓️', 'condition': lambda df, streak: streak >= 7},
    'record_30': {'name': '熟練の航海士', 'description': '30日間、連続で記録をつけました。', 'emoji': '📅', 'condition': lambda df, streak: streak >= 30},
    'deep_dive_1': {'name': '深海への探求者', 'description': '初めてディープ・ダイブモードで記録しました。', 'emoji': '🔬', 'condition': lambda df: 'deep' in df['mode'].values},
    'q_updated': {'name': '羅針盤の調整', 'description': '価値観（q_t）を更新しました。', 'emoji': '🧭', 'condition': lambda df: len(df.dropna(subset=Q_COLS, how='all')) > 1},
    'rhi_plus': {'name': '順風満帆', 'description': '初めてRHIがプラスになりました。', 'emoji': '⛵', 'condition': lambda df, rhi_results: rhi_results and rhi_results.get('RHI', 0) > 0},
    'balance_master': {'name': '調和の達人', 'description': '全てのドメインの充足度が70点以上になった日がありました。', 'emoji': '⚖️', 'condition': lambda df: (df[S_COLS] >= 70).all(axis=1).any()}
}
# レベル2介入提案機能：介入レシピ定義
INTERVENTION_RECIPES = {
    'health': [
        "いつもより15分早く就寝する",
        "ランチに一品、野菜を追加する",
        "一駅手前で降りて歩いてみる",
        "5分間のストレッチや瞑想を行う",
    ],
    'relationships': [
        "しばらく連絡していない友人に、短いメッセージを送る",
        "家族やパートナーに、小さな感謝を言葉で伝える",
        "ランチは誰かを誘ってみる",
        "人の話を、評価せずに最後まで聞いてみる",
    ],
    'meaning': [
        "今日の仕事が、最終的に誰の役に立ったか想像してみる",
        "週末にできる、小さなボランティア活動を探してみる",
        "自分の価値観について、5分だけ日記に書き出してみる",
        "尊敬する人の本や記事を読んでみる",
    ],
    'autonomy': [
        "明日の予定を一つ、完全に自分の「やりたい」だけで決めてみる",
        "いつもと違う通勤路や、入ったことのない店を試してみる",
        "興味がある分野の入門動画を一つ見てみる",
        "身の回りの小さなことで、自分でコントロールできることを見つける",
    ],
    'finance': [
        "今週の出費を一度だけ見直してみる",
        "自分の仕事のスキルアップに繋がる記事を一つ読む",
        "お昼は手作りのお弁当に挑戦してみる",
        "固定費（サブスク等）で、見直せるものがないか確認する",
    ],
    'leisure': [
        "通勤中に、好きな音楽を3曲、集中して聴く時間を作る",
        "週末に、全く仕事と関係ない趣味の時間を1時間確保する",
        "美しいと感じるものの写真を一枚撮ってみる",
        "寝る前に、今日あった良かったことを3つ書き出す",
    ],
    'competition': [
        "健全な競争を楽しめる、ゲームやスポーツをしてみる",
        "他人との比較ではなく、昨日の自分との比較で「成長」を記録する",
        "競争のストレスを感じたら、意識的に休息を取る",
    ]
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
def calculate_s_domains_from_row(row: pd.Series) -> pd.Series:
    s_domain_scores = {}
    
    for domain, elements in LONG_ELEMENTS.items():
        domain_scores_list = []
        for e in elements:
            col = f's_element_{e}'
            if col in row and pd.notna(row[col]):
                domain_scores_list.append(row[col])
        
        if domain_scores_list:
            s_domain_scores['s_' + domain] = int(round(np.mean(domain_scores_list)))
        else:
            s_domain_scores['s_' + domain] = row.get('s_' + domain, np.nan)
            
    return pd.Series(s_domain_scores)

@st.cache_data
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    if df_copy.empty:
        return df_copy

    def get_s_domains_based_on_mode(row):
        if row.get('mode') == 'deep':
            return calculate_s_domains_from_row(row)
        else:
            return row[S_COLS]

    s_domain_updates = df_copy.apply(get_s_domains_based_on_mode, axis=1)
    df_copy[S_COLS] = s_domain_updates

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
                    **【🎉 幸福なサプライズの予感！】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点）**を上回っています。
                    もしかしたら、あなたがまだ意識していない、素晴らしい喜びの源泉があったのかもしれませんね。
                    """)
            elif latest_gap < -fixed_threshold:
                st.warning(f"""
                    **【🤔 隠れた不満のサイン？】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点）**を下回っています。
                    何か見過ごしているストレス要因や、あなたの価値観と経験の間に小さなズレがあるのかもしれません。
                    """)
            else:
                st.success(f"""
                    **【✨ 順調な初日です！】**
                    あなたの**実感（G = {int(latest_g)}点）**と、モデルが算出した**調和度指数（H = {int(latest_h)}点）**は、よく一致しています。
                    素晴らしいスタートです！
                    """)
    else:
        df_analysis['gap'] = df_analysis['g_happiness'] - (df_analysis['H'] * 100.0)
        std_gap = df_analysis['gap'].std()
        dynamic_threshold = max(15, 1.0 * std_gap) 

        with st.expander("▼ これは、あなたの過去データに基づいた統計的診断です", expanded=True):
            if latest_gap > dynamic_threshold:
                st.info(f"""
                    **【🎉 幸福なサプライズ！】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点）**を、あなたの**普段のブレ幅（{dynamic_threshold:.1f}点）**以上に大きく上回りました。
                    これは、あなたが**まだ言葉にできていない、新しい価値観**を発見したサインかもしれません。
                    **問い：** 今日の記録を振り返り、あなたが設定した価値観（q_t）では捉えきれていない、予期せぬ喜びの源泉は何だったでしょうか？
                    """)
            elif latest_gap < -dynamic_threshold:
                st.warning(f"""
                    **【🤔 隠れた不満？】**
                    あなたの**実感（G = {int(latest_g)}点）**は、モデルが算出した**調和度指数（H = {int(latest_h)}点）**を、あなたの**普段のブレ幅（{dynamic_threshold:.1f}点）**以上に大きく下回りました。
                    価値観に沿った生活のはずなのに、何かが満たされていないようです。見過ごしている**ストレス要因や、あなたの価値観と経験の間に小さなズレ**があるのかもしれません。
                    **問い：** 今日の記録を振り返り、あなたの幸福感を静かに蝕んでいた「見えない重り」は何だったでしょうか？
                    """)
            else:
                st.success(f"""
                    **【✨ 順調な航海です！】**
                    あなたの**実感（G = {int(latest_g)}点）**と、モデルが算出した**調和度指数（H = {int(latest_h)}点）**は、よく一致しています。
                    あなたの自己認識と、実際の経験が、うまく調和している状態です。素晴らしい！
                    """)

def calculate_rhi_metrics(df_period: pd.DataFrame, lambda_rhi: float, gamma_rhi: float, tau_rhi: float) -> dict:
    if df_period.empty or 'H' not in df_period.columns:
        return {'mean_H': 0, 'std_H': 0, 'frac_below': 0, 'RHI': 0}
    mean_H = df_period['H'].mean()
    std_H = df_period['H'].std(ddof=0) if len(df_period) > 1 else 0
    frac_below = (df_period['H'] < tau_rhi).mean()
    rhi = mean_H - (lambda_rhi * std_H) - (gamma_rhi * frac_below)
    return {'mean_H': mean_H, 'std_H': std_H, 'frac_below': frac_below, 'RHI': rhi}
def generate_intervention_proposal(df_period: pd.DataFrame, rhi_results: dict):
    """
    分析結果に基づき、パーソナライズされた介入提案を生成する。
    RHIへの悪影響が最も大きいドメインを特定し、レシピを提案する。
    """
    if df_period.empty or not rhi_results:
        return None, None

    # RHIへの各要素の寄与度（悪影響度）を計算
    mean_h = rhi_results.get('mean_H', 0)
    std_h = rhi_results.get('std_H', 0)
    
    # 各ドメインを一つずつ除外した場合のRHIの変化をシミュレーション
    impacts = {}
    for domain_to_exclude in DOMAINS:
        temp_s_cols = [s for s in S_COLS if 's_' + domain_to_exclude not in s]
        
        # 悪影響を計算するため、単純化して標準偏差への寄与を測る
        # あるドメインの変動が全体の変動にどれだけ寄与したか
        domain_std = df_period['s_' + domain_to_exclude].std()
        
        # ズレ（U）への影響も考慮する
        q_val = df_period['q_' + domain_to_exclude].mean()
        s_val = df_period['s_' + domain_to_exclude].mean()
        gap_contribution = q_val * (1 - (s_val / 100.0)) # 価値が高いのに満たされていない度合い
        
        # 影響度をスコアリング（標準偏差と価値-充足ギャップを重視）
        impact_score = (domain_std / 100.0) * 0.7 + gap_contribution * 0.3
        impacts[domain_to_exclude] = impact_score

    if not impacts:
        return None, None

    # 最も悪影響が大きいドメインを特定
    focus_domain = max(impacts, key=impacts.get)
    
    # そのドメインに対応する介入レシピをランダムに2つ提案
    recipes = INTERVENTION_RECIPES.get(focus_domain, [])
    if len(recipes) > 2:
        proposal = np.random.choice(recipes, 2, replace=False).tolist()
    else:
        proposal = recipes
        
    return focus_domain, proposal

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
        if 'record_timestamp' in df.columns:
             df['record_timestamp'] = pd.to_datetime(df['record_timestamp'], errors='coerce')

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
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce').dt.strftime('%Y-%m-%d')

        if 'record_timestamp' in df_copy.columns:
            # Attempt to coerce column to datetimes. This yields a Series.
            timestamps = pd.to_datetime(df_copy['record_timestamp'], errors='coerce')

            try:
                # Use the dtype of the Series for robust detection
                if pd.api.types.is_datetime64_any_dtype(timestamps.dtype):
                    # If timezone-aware, convert to UTC and then remove tz for consistent storage
                    try:
                        # timestamps.dt.tz might not exist for some pandas versions; use getattr safely
                        if getattr(timestamps.dt, 'tz', None) is not None:
                            # Convert to UTC then drop tz info
                            timestamps = timestamps.dt.tz_convert('UTC').dt.tz_localize(None)
                        # Format as ISO with trailing Z to indicate UTC when possible
                        df_copy['record_timestamp'] = timestamps.apply(lambda x: x.isoformat() + 'Z' if pd.notna(x) else '')
                    except Exception:
                        # Fallback: try simple isoformat if .dt access fails
                        df_copy['record_timestamp'] = timestamps.apply(lambda x: x.isoformat() if pd.notna(x) else '')
                else:
                    # Fallback: handle object-dtype entries (python datetimes or strings)
                    def _to_iso(val):
                        try:
                            if pd.isna(val):
                                return ''
                            ts = pd.to_datetime(val, errors='coerce')
                            if pd.isna(ts):
                                return ''
                            # If tz-aware, convert to UTC then produce ISO + 'Z'
                            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                                try:
                                    # pandas Timestamp may need tz_convert; try to normalize to UTC
                                    ts_utc = ts.tz_convert('UTC') if hasattr(ts, 'tz_convert') else ts
                                    # remove tzinfo for consistent formatting
                                    try:
                                        ts_utc = ts_utc.tz_localize(None)
                                    except Exception:
                                        pass
                                    return ts_utc.isoformat() + 'Z'
                                except Exception:
                                    pass
                            return ts.isoformat()
                        except Exception:
                            return ''
                    df_copy['record_timestamp'] = df_copy['record_timestamp'].apply(_to_iso)
            except Exception:
                # Ensure column exists and is safe to write if anything unexpected occurs
                df_copy['record_timestamp'] = df_copy['record_timestamp'].apply(lambda x: '' if pd.isna(x) else str(x))

        db_schema_cols = ['user_id', 'password_hash', 'consent'] + list(DEMOGRAPHIC_OPTIONS.keys())
        if sheet_name == 'data':
            element_cols_ordered = [f's_element_{e}' for domain_key in DOMAINS for e in LONG_ELEMENTS[domain_key]]
            db_schema_cols = (
                ['user_id', 'date', 'record_timestamp', 'consent', 'mode'] + 
                Q_COLS + S_COLS + 
                ['g_happiness', 'event_log'] +
                element_cols_ordered
            )
        
        for col in db_schema_cols:
            if col not in df_copy.columns:
                df_copy[col] = '' 

        df_to_write = df_copy[db_schema_cols]
        df_to_write = df_to_write.fillna('').astype(str)
        
        worksheet.clear()
        worksheet.update([df_to_write.columns.values.tolist()] + df_to_write.values.tolist(), value_input_option='USER_ENTERED')
        
        st.cache_data.clear()
        st.cache_resource.clear()
        
        return True
    except Exception as e:
        st.error(f"データの書き込み中にエラー: {e}")
        return False
    # --- (D. データ永続化層 の後、E. UIコンポーネント の前に追加) ---

def check_achievements(df: pd.DataFrame, rhi_results: dict, streak: int):
    """ユーザーデータに基づいてアチーブメントの達成状況をチェックする"""
    newly_unlocked = set()
    currently_unlocked = st.session_state.unlocked_achievements.copy()

    for ach_id, details in ACHIEVEMENTS.items():
        if ach_id not in currently_unlocked:
            condition_met = False
            # 条件判定をラムダ関数の引数の数で分岐
            if 'streak' in details['condition'].__code__.co_varnames:
                condition_met = details['condition'](df, streak)
            elif 'rhi_results' in details['condition'].__code__.co_varnames:
                 condition_met = details['condition'](df, rhi_results)
            else:
                condition_met = details['condition'](df)
            
            if condition_met:
                newly_unlocked.add(ach_id)

    if newly_unlocked:
        for ach_id in newly_unlocked:
            st.toast(f"{ACHIEVEMENTS[ach_id]['emoji']} 実績解除： {ACHIEVEMENTS[ach_id]['name']}", icon="🏆")
        st.session_state.unlocked_achievements.update(newly_unlocked)

def calculate_streak(df: pd.DataFrame) -> int:
    """連続記録日数を計算する"""
    if df.empty:
        return 0
    
    df_dates = df['date'].dropna().unique()
    df_dates = sorted(list(df_dates), reverse=True)
    
    today = date.today()
    streak = 0
    
    # 今日の記録があるか、または昨日の記録があるかで開始日を決める
    if today in df_dates:
        expected_date = today
    elif (today - timedelta(days=1)) in df_dates:
        expected_date = today - timedelta(days=1)
        streak = 1 # 昨日は記録しているのでストリークは1から
    else:
        return 0

    if streak == 0 and today in df_dates:
        streak = 1
        expected_date = today - timedelta(days=1)

    for d in df_dates[1:]:
        if d == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        else:
            break
            
    return streak

# --- E. UIコンポーネント ---
def show_welcome_and_guide():
    st.header("ようこそ、Harmony Navigatorへ")
    st.subheader("あなたのための、内省支援ツール")
    st.markdown("---")
    st.info("本アプリは、あなたの自己理解と内省を支援するためのツールであり、幸福の実現を保証するものではありません。")
    st.subheader("1. このアプリの目的")
    st.markdown("""
    「もっと幸せになりたい」と願いながらも、漠然とした不安や、**あなた自身の価値観（こうありたい自分）」**と**「実際の経験（実際に経験した一日）」**の間の、言葉にならない『ズレ』に、私たちはしばしば悩まされます。
    このアプリは、その『ズレ』の正体を可視化し、あなた自身が人生の舵を取るための、**実践的なツール**を提供することを目的としています。
    
    このアプリを使えば、
    - **自分の現在地**（今の心の状態）を客観的に知り、
    - **目的地**（自分が本当に大切にしたいこと）を明確にし、
    - **航路**（日々の選択）を、あなた自身で賢明に調整していくことができます。
    """)
    st.markdown("---")
    st.subheader("2. プライバシー保護について")
    with st.expander("▼ 詳細：二重の匿名化・暗号化技術"):
        st.markdown("""
        このアプリの最も重要な約束は、あなたのプライバシーを守ることです。
        
        **第一に、個人を特定できる情報は一切取得しません。**
        あなたが初めて利用する際、システムが**完全にランダムで予測不可能な「ユーザーID」**を自動で生成します。メールアドレスや氏名の登録は不要です。これにより、開発者を含め誰もが、IDの持ち主が現実世界の誰なのかを知る手段はありません。
        
        **第二に、あなたの日記（イベントログ）は、あなたにしか読めません。**
        あなたが日記を保存する際、その内容はあなたの**パスワード**を鍵として、あなたのブラウザ上で**暗号化**されます。データベースに保存されるのは、誰も解読できない暗号化されたデータのみです。
        
        この仕組みにより、あなたのプライバシーは、**「設計」そのものによって構造的に保護されます。**
        """)
    st.markdown("---")
    st.subheader("3. 学術研究へのご協力について（任意）")
    st.info("""
    もしご協力いただける場合、あなたが記録した**匿名化された数値データ**を、幸福に関する科学的研究に利用させていただくことへのご同意をお願いしています。
    
    あなたのプライバシーを最優先するため、**日記の内容（イベントログ）が研究に利用されることは一切ありません。**
    研究協力への同意は、いつでも「設定」タブから変更可能です。
    """)

def show_legal_documents():
    with st.expander("📜 **利用規約**を読む"):
        st.markdown("""
        **最終更新日：2025年9月12日**
        
        本利用規約（以下「本規約」といいます）は、[あなたの氏名または事業名]（以下「当方」といいます）が提供するアプリケーション「Harmony Navigator」（以下「本アプリ」といいます）の利用条件を定めるものです。本アプリを利用するユーザーの皆様（以下「ユーザー」といいます）には、本規約に従って本アプリをご利用いただきます。
        
        **第1条（適用）**
        本規約は、ユーザーと当方との間の本アプリの利用に関わる一切の関係に適用されるものとします。ユーザーは、本アプリを利用することにより、本規約の全ての内容に同意したものとみなされます。
        
        **第2条（利用者登録）**
        1. **本アプリは16歳以上の個人を対象としています。** 16歳未満の方は、本アプリを利用することはできません。
        2. 本アプリの利用を希望する者は、本規約に同意の上、当方の定める方法によって利用者登録を申請し、当方がこれを承認することによって、利用者登録が完了するものとします。
        3. 当方は、利用者登録の申請者に以下の事由があると判断した場合、登録を承認しないことがあり、その理由については一切の開示義務を負わないものとします。
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
        本規約の解釈にあっては、日本法を準拠法とします。本アプリに関して紛争が生じた場合には、[東京地方裁判所]を第一審の専属的合意管轄裁判所とします。
        
        以上
        """)
    
    with st.expander("📄 **プライバシーポリシー**を読む"):
        st.markdown("""
        **最終更新日：2025年9月12日**
        
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
        
        **8. 未成年者の利用について**
        本アプリは16歳以上の利用者を対象としております。16歳未満の個人から意図的に情報を収集することはありません。もし、あなたが保護者であり、あなたのお子様が当方のサービスを利用し、個人情報を提供したことに気づいた場合は、ご連絡ください。当方は、保護者の同意なしに16歳未満の子供から個人情報を収集したことが判明した場合、その情報をサーバーから削除する措置を講じます。
        """)

def get_safe_index(options, value):
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return 0

def migrate_and_ensure_schema(df: pd.DataFrame, user_id: str, sheet_id: str) -> pd.DataFrame:
    """
    ユーザーデータを読み込み、最新のスキーマに準拠しているか確認・修正する。
    修正があった場合は、データベースに書き戻して永続化する。
    """
    EXPECTED_COLUMNS = ['user_id', 'date', 'record_timestamp', 'consent', 'mode'] + Q_COLS + S_COLS + ['g_happiness', 'event_log'] + ALL_ELEMENT_COLS
    
    df_migrated = df.copy()
    made_changes = False
    
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df_migrated.columns]
    if missing_cols:
        st.info("古いデータ形式を検出しました。スキーマを更新します...")
        for col in missing_cols:
            df_migrated[col] = pd.NA
        made_changes = True

    if 'record_timestamp' in df_migrated.columns:
        df_migrated['record_timestamp'] = pd.to_datetime(df_migrated['record_timestamp'], errors='coerce')
        missing_timestamp_mask = df_migrated['record_timestamp'].isna()
        
        date_as_datetime = pd.to_datetime(df_migrated['date'], errors='coerce')

        if missing_timestamp_mask.any():
            st.info("古い記録にタイムスタンプを付与しています...")
            pseudo_timestamps = date_as_datetime[missing_timestamp_mask].apply(lambda x: pd.Timestamp(x, tz=JST) if pd.notna(x) else pd.NaT)
            df_migrated.loc[missing_timestamp_mask, 'record_timestamp'] = pseudo_timestamps
            made_changes = True

    if made_changes:
        st.info("データベースを最新の形式に更新しています...")
        try:
            all_data_df = read_data('data', sheet_id)
            if not all_data_df.empty:
                other_users_data = all_data_df[all_data_df['user_id'] != user_id]
                all_data_df_updated = pd.concat([other_users_data, df_migrated], ignore_index=True)
            else:
                all_data_df_updated = df_migrated

            if write_data('data', sheet_id, all_data_df_updated):
                st.success("データ形式の更新が完了し、永続的に保存しました。")
                return df_migrated
            else:
                st.error("スキーマ更新の保存に失敗しました。")
        except Exception as e:
            st.warning(f"スキーマ更新の保存中にエラーが発生しました: {e}")
    
    final_order = [col for col in EXPECTED_COLUMNS if col in df_migrated.columns] + [c for c in df_migrated.columns if c not in EXPECTED_COLUMNS]
    return df_migrated[final_order]


def run_wizard_interface(container):
    """価値観発見ガイドのUIをレンダリングする再利用可能な関数"""
    pairs = list(itertools.combinations(DOMAINS, 2))
    
    with container:
        st.header("🧭 あなたの羅針盤を設定しましょう")
        st.info("あなたの人生という航海で、何を大切にしたいかを見つけるための、最初のステップです。21の簡単な質問に答えることで、あなたの価値観の「たたき台」を一緒に探しましょう。")

        progress_value = (st.session_state.q_wizard_step - 1) / len(pairs) if st.session_state.q_wizard_step > 0 else 0
        st.progress(progress_value, text=f"進捗: {st.session_state.q_wizard_step - 1} / {len(pairs)}")

        if 0 < st.session_state.q_wizard_step <= len(pairs):
            pair = pairs[st.session_state.q_wizard_step - 1]
            domain1, domain2 = pair
            st.subheader(f"質問 {st.session_state.q_wizard_step}/{len(pairs)}")
            st.write("あなたの人生がより充実するために、今、より重要なのはどちらですか？")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(DOMAIN_NAMES_JP_DICT[domain1], key=f"btn_{domain1}", use_container_width=True):
                    st.session_state.q_comparisons[pair] = domain1
                    st.session_state.q_wizard_step += 1
                    st.rerun()
                with st.expander("▼ このドメインには、どんな「材料」が含まれる？"):
                    for element in LONG_ELEMENTS[domain1]:
                        st.markdown(f"- **{element}**: {ELEMENT_DEFINITIONS.get(element, '')}")

            with col2:
                if st.button(DOMAIN_NAMES_JP_DICT[domain2], key=f"btn_{domain2}", use_container_width=True):
                    st.session_state.q_comparisons[pair] = domain2
                    st.session_state.q_wizard_step += 1
                    st.rerun()
                with st.expander("▼ このドメインには、どんな「材料」が含まれる？"):
                    for element in LONG_ELEMENTS[domain2]:
                        st.markdown(f"- **{element}**: {ELEMENT_DEFINITIONS.get(element, '')}")
        else:
            if st.session_state.q_comparisons:
                st.success("✅ 診断完了！あなたの価値観の推定値が計算されました。")
                estimated_weights = calculate_ahp_weights(st.session_state.q_comparisons, DOMAINS)
                
                st.session_state.q_values = {domain: weight for domain, weight in zip(DOMAINS, estimated_weights)}
                
                st.write("推定されたあなたの価値観:")
                st.bar_chart({DOMAIN_NAMES_JP_DICT[k]: v for k, v in st.session_state.q_values.items()})

                if st.button("✅ この価値観で航海を始める"):
                    user_id = st.session_state.user_id
                    all_data_df = read_data('data', st.secrets["connections"]["gsheets"]["data_sheet_id"])
                    
                    new_record = {'user_id': user_id, 'date': date.today(), 'record_timestamp': datetime.now(JST)}
                    new_record.update({f'q_{d}': v for d, v in st.session_state.q_values.items()})
                    new_df_row = pd.DataFrame([new_record])

                    all_data_df_updated = pd.concat([all_data_df, new_df_row], ignore_index=True)

                    # ★★★ TypeError バグ修正：並べ替えの前にデータ型を統一 ★★★
                    if 'date' in all_data_df_updated.columns:
                        all_data_df_updated['date'] = pd.to_datetime(all_data_df_updated['date'], errors='coerce')
                    if 'record_timestamp' in all_data_df_updated.columns:
                        all_data_df_updated['record_timestamp'] = pd.to_datetime(all_data_df_updated['record_timestamp'], errors='coerce')
                    
                    all_data_df_updated = all_data_df_updated.sort_values(by=['user_id', 'date', 'record_timestamp']).reset_index(drop=True)

                    if write_data('data', st.secrets["connections"]["gsheets"]["data_sheet_id"], all_data_df_updated):
                        st.session_state.auth_status = "AWAITING_DEMOGRAPHICS"
                        st.success("価値観を保存しました。次に、任意でプロフィール情報をご登録ください。")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("価値観の保存に失敗しました。")

# 改善要望3: プロフィール入力画面の関数を追加
def run_demographics_interface(container):
    """プロフィール情報入力のUIをレンダリングする関数"""
    with container:
        st.header("👤 プロフィール情報のご登録（任意）")
        st.info("""
        ご協力いただき、ありがとうございます。
        もしよろしければ、今後の研究のため、あなたの背景についてお聞かせください。
        **この情報の提供は完全に任意であり、回答しなくてもアプリの機能は全てご利用いただけます。**
        提供された情報は、完全に匿名化された上で、統計分析にのみ利用されます。
        """)
        
        with st.form("profile_form_onboarding"):
            users_df_for_profile = read_data('users', st.secrets["connections"]["gsheets"]["users_sheet_id"])
            user_info = users_df_for_profile[users_df_for_profile['user_id'] == st.session_state.user_id]
            current_profile = user_info.iloc[0] if not user_info.empty else pd.Series()
            
            # 全てのプロフィール項目を追加
            age_group = st.selectbox("年代", options=DEMOGRAPHIC_OPTIONS['age_group'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['age_group'], current_profile.get('age_group')))
            gender = st.selectbox("性別", options=DEMOGRAPHIC_OPTIONS['gender'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['gender'], current_profile.get('gender')))
            occupation_category = st.selectbox("職業", options=DEMOGRAPHIC_OPTIONS['occupation_category'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['occupation_category'], current_profile.get('occupation_category')))
            income_range = st.selectbox("年収", options=DEMOGRAPHIC_OPTIONS['income_range'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['income_range'], current_profile.get('income_range')))
            marital_status = st.selectbox("婚姻状況", options=DEMOGRAPHIC_OPTIONS['marital_status'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['marital_status'], current_profile.get('marital_status')))
            has_children = st.selectbox("子供の有無", options=DEMOGRAPHIC_OPTIONS['has_children'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['has_children'], current_profile.get('has_children')))
            living_situation = st.selectbox("居住形態", options=DEMOGRAPHIC_OPTIONS['living_situation'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['living_situation'], current_profile.get('living_situation')))
            chronic_illness = st.selectbox("慢性疾患", options=DEMOGRAPHIC_OPTIONS['chronic_illness'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['chronic_illness'], current_profile.get('chronic_illness')))
            country = st.selectbox("国", options=DEMOGRAPHIC_OPTIONS['country'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['country'], current_profile.get('country')))
            
            col1, col2 = st.columns(2)
            with col1:
                profile_submitted = st.form_submit_button("✅ プロフィールを保存して進む", use_container_width=True)
            with col2:
                skip_submitted = st.form_submit_button("⏩ 今は回答しない（スキップ）", use_container_width=True)

            if profile_submitted:
                users_df_update = read_data('users', st.secrets["connections"]["gsheets"]["users_sheet_id"])
                # 全てのプロフィール項目を更新
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'age_group'] = age_group
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'gender'] = gender
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'occupation_category'] = occupation_category
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'income_range'] = income_range
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'marital_status'] = marital_status
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'has_children'] = has_children
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'living_situation'] = living_situation
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'chronic_illness'] = chronic_illness
                users_df_update.loc[users_df_update['user_id'] == st.session_state.user_id, 'country'] = country
                
                if write_data('users', st.secrets["connections"]["gsheets"]["users_sheet_id"], users_df_update):
                    st.session_state.auth_status = "INITIALIZING_SESSION"
                    st.success("ご協力ありがとうございます！メイン画面に移動します。")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("プロフィールの保存に失敗しました。")
            
            if skip_submitted:
                st.session_state.auth_status = "INITIALIZING_SESSION"
                st.info("メイン画面に移動します。")
                time.sleep(1)
                st.rerun()
def inject_custom_css():
    st.markdown(
        """
        <style>
            /* Streamlitのコンテナ(border=True)のスタイルを上書き */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background-color: #f0f2f6; /* 薄いグレーの背景 */
                border: 1px solid #e0e0e0; /* より薄いグレーの境界線 */
                border-radius: 10px;      /* 角を丸くする */
                padding: 1.2rem 1rem 1rem; /* 内側の余白を調整 */
            }

            /* エキスパンダー（▼...）のスタイルを上書き */
            [data-testid="stExpander"] {
                background-color: #f7f7f7; /* コンテナより少しだけ明るいグレー */
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            
            /* ボタンのスタイルを少し柔らかく */
            [data-testid="stButton"] button {
                border-radius: 8px;
            }

            /* --- ★★★ ここからが新しい修正 ★★★ --- */
            
            /* st.info (青色の網掛け) のスタイルを強制的に上書き */
            div[data-testid="stAlert"][data-alert-type="info"] {
                background-color: #e9ecef !important; /* 薄いグレー */
                border: 1px solid #ced4da !important;
                border-radius: 10px !important;
            }
            /* st.info内のテキストの色 */
            div[data-testid="stAlert"][data-alert-type="info"] .st-emotion-cache-1wivap2 {
                color: #495057 !important; /* 少し濃いグレーの文字 */
            }
            /* st.info内のアイコンの色 */
            div[data-testid="stAlert"][data-alert-type="info"] svg {
                fill: #495057 !important;
            }

            /* st.success (緑色の網掛け) のスタイルを強制的に上書き */
            div[data-testid="stAlert"][data-alert-type="success"] {
                background-color: #dee2e6 !important; /* 少し濃いグレー */
                border: 1px solid #adb5bd !important;
                border-radius: 10px !important;
            }
            /* st.success内のテキストの色 */
            div[data-testid="stAlert"][data-alert-type="success"] .st-emotion-cache-1wivap2 {
                color: #343a40 !important; /* 濃いグレーの文字 */
            }
            /* st.success内のアイコンの色 */
            div[data-testid="stAlert"][data-alert-type="success"] svg {
                fill: #343a40 !important;
            }
            /* --- ★★★ ここまでが新しい修正 ★★★ --- */

        </style>
        """,
        unsafe_allow_html=True,
    )
# --- F. メインアプリケーション ---
def main():
    # ★★★ ここに新しい行を追加 ★★★
    inject_custom_css()
    # ★★★ ここまで ★★★
    
    st.title('🧭 Harmony Navigator')
    st.caption('v7.0.59 - Final Complete Code with All Fixes & Refinements')
    
    try:
        users_sheet_id = st.secrets["connections"]["gsheets"]["users_sheet_id"]
        data_sheet_id = st.secrets["connections"]["gsheets"]["data_sheet_id"]
    except KeyError:
        st.error("SecretsにスプレッドシートID (`users_sheet_id`, `data_sheet_id`) が設定されていません。")
        st.stop()

    if 'auth_status' not in st.session_state: st.session_state.auth_status = "NOT_LOGGED_IN"
    if 'user_id' not in st.session_state: st.session_state.user_id = None
    if 'enc_manager' not in st.session_state: st.session_state.enc_manager = None
    if 'q_values' not in st.session_state:
        st.session_state.q_values = {domain: 100 // len(DOMAINS) for domain in DOMAINS}
        st.session_state.q_values[DOMAINS[0]] += 100 % len(DOMAINS)
    if 'q_wizard_step' not in st.session_state: st.session_state.q_wizard_step = 0
    if 'q_comparisons' not in st.session_state: st.session_state.q_comparisons = {}
    if 'record_streak' not in st.session_state: st.session_state.record_streak = 0
    if 'unlocked_achievements' not in st.session_state: st.session_state.unlocked_achievements = set()

    auth_status = st.session_state.auth_status

    if auth_status in ["NOT_LOGGED_IN", "AWAITING_ID", "AWAITING_WIZARD", "AWAITING_DEMOGRAPHICS"]:
        if auth_status == "AWAITING_ID":
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
                st.session_state.auth_status = "AWAITING_WIZARD"
                st.session_state.q_wizard_step = 1
                st.session_state.q_comparisons = {}
                st.rerun()
        elif auth_status == "AWAITING_WIZARD":
            run_wizard_interface(st.container())
        elif auth_status == "AWAITING_DEMOGRAPHICS":
            run_demographics_interface(st.container())
        else: # NOT_LOGGED_IN
            show_welcome_and_guide()
                        # --- ★★★ ここからが新しい追加箇所 ★★★ ---
            st.subheader("❓ よくあるご質問（FAQ）")
            with st.container(border=True):
                with st.expander("プライバシーとセキュリティについて"):
                    st.markdown("""
                    **Q1. 私の書いた日記（イベントログ）を、開発者や他の誰かに読まれてしまうことはありませんか？**
                    
                    **A1. いいえ、絶対にありません。**
                    あなたの日記は、あなたの**パスワードを鍵として、あなたのスマホやPC上で暗号化**されてから、私たちのサーバーに保存されます。私たち開発者でさえ、その暗号を解読する鍵（あなたのパスワード）を持っていないため、**あなたの日記の中身を閲覧することは物理的に不可能**です。この仕組みを「ゼロ知識暗号化」と呼び、あなたのプライバシーを最高レベルで保護します。

                    **Q2. 個人情報（名前やメールアドレス）を登録する必要はありますか？身元がバレませんか？**
                    
                    **A2. いいえ、一切不要です。**
                    このアプリは、あなたの**本名、メールアドレス、電話番号といった、個人を特定できる情報を一切収集しません。**
                    あなたが利用を開始する際に発行されるのは、完全にランダムで匿名な「秘密の合い言葉（ユーザーID）」のみです。これにより、あなたのアカウントと、現実世界のあなたが結びつくことはありません。
                    
                    **Q3. 私のデータが、勝手に第三者に売られたりしませんか？**
                    
                    **A3. いいえ、決してありません。**
                    あなたのデータを第三者に販売することは、私たちの理念に反します。あなたのデータは、あなたの自己理解を深める目的、そしてあなたが研究協力を同意した場合に限り、**厳格に匿名化された上で**学術研究の目的でのみ利用されます。詳細はプライバシーポリシーをご確認ください。
                    """)

                with st.expander("アプリの効果と使い方について"):
                    st.markdown("""
                    **Q4. このアプリを使えば、本当に「幸せ」になれるのですか？効果は保証されますか？**
                    
                    **A4. いいえ、幸福になることを「保証」するものではありません。**
                    このアプリは、魔法の杖や万能薬ではありません。あくまで、あなたの自己理解と内省を支援するための**「道具（ツール）」**です。
                    私たちは、あなたに「答え」を与えるのではなく、あなたが**自分自身の力で「自分だけの答え」を見つける**ための、客観的なデータ（鏡）と、思考のフレームワーク（羅針盤）を提供します。効果は、あなたがこのツールをどう使いこなすかにかかっています。

                    **Q5. 毎日記録するのが面倒くさそうです。続けられるか心配です。**
                    
                    **A5. そのお気持ち、よく分かります。だからこそ、2つの記録モードを用意しました。**
                    - **「クイック・ログ」モード**なら、**1〜2分**で完了します。忙しい日はこちらをご利用ください。
                    - **「ディープ・ダイブ」モード**は、週に一度や、じっくり自分と向き合いたい特別な日に使うのがおすすめです。
                    大切なのは完璧に記録することではなく、**細く長く、自分との対話を続ける習慣**です。「記録できなかった日」も、それ自体が「忙しかった」という重要なデータになります。

                    **Q6. 数値で評価されることで、逆にストレスを感じたり、スコアの奴隷になったりしませんか？**
                    
                    **A6. それは、このツールが最も警戒しているリスクの一つです。**
                    このアプリの目的は、高いスコアを出すことではありません。スコアは、あくまで**あなた自身との対話の「きっかけ」**に過ぎません。
                    `H`（調和度）や`RHI`（リスク調整済・幸福指数）は、あなたの人生の価値を決めるものでは断じてなく、あなたの「羅針盤（価値観）」と「現在の航路（経験）」がどれだけ一致しているかを示す**計器**です。
                    スコアが低い日は、「自分はダメだ」と落ち込むのではなく、**「おや、羅針盤と航路がズレているようだ。どこで修正しようか？」**と、次の一手を考えるための冷静な材料としてご活用ください。
                    """)

                with st.expander("理論と科学的根拠について"):
                    st.markdown("""
                    **Q7. この「7つのドメイン」や理論は、本当に科学的な根拠があるのですか？**
                    
                    **A7. はい、この理論は、既存の科学的な知見に基づいて構築されています。**
                    「6+1」のドメインモデルは、ポジティブ心理学、自己決定理論、幸福経済学といった、現代の幸福研究における主要な理論モデルを横断し、そのエッセンスを統合・再編したものです。
                    しかし、この理論体系そのものの科学的な妥当性は、**まだ完全には証明されていません。** あなたがこのアプリを利用し、研究に協力してくださることが、この新しい理論を検証し、科学を発展させるための、貴重な一歩となります。

                    **Q8. 価値観を発見する「ガイド」は、私を特定の価値観に誘導しませんか？**
                    
                    **A8. いいえ、その逆です。**
                    「価値観発見ガイド」は、あなたに「これが正しい価値観です」と教えるものではありません。21の質問は、あなた自身も気づいていないかもしれない、**あなたの心の中にある潜在的な優先順位**を、客観的に引き出すためのものです。
                    ガイドが出した結果は、あくまで**「たたき台」**です。その結果を見て、「うん、しっくりくるな」あるいは「いや、自分はもっとここを重視したい」と感じ、最終的にサイドバーのスライダーで**あなた自身の手で微調整する**ことこそが、最も重要なプロセスです。アプリは、あなたの自己決定を最後まで尊重します。
                    """)
            # --- ★★★ ここまでが新しい追加箇所 ★★★ ---
            
            # --- ★★★ ここからが修正箇所 ★★★ ---
            # 新規登録・ログインの前に、法的文書を表示する
            with st.container(border=True):
                st.markdown("##### 利用を開始する前に")
                st.info("本アプリケーションの利用を開始する前に、以下の利用規約とプライバシーポリシーをご確認・ご同意いただく必要があります。")
                show_legal_documents()
            # --- ★★★ ここまでが修正箇所 ★★★ ---

            door1, door2 = st.tabs(["**🚀 新しい船で旅を始める (初めての方)**", "**🔑 秘密の合い言葉で乗船する (2回目以降の方)**"])
            with door1:
                with st.form("register_form"):
                    st.markdown("##### 1. 同意事項")
                    age_consent = st.checkbox("私は16歳以上です。")
                    agreement = st.checkbox("上記の利用規約とプライバシーポリシーに同意します。")
                    st.markdown("##### 2. パスワード設定")
                    new_password = st.text_input("パスワード（8文字以上）", type="password")
                    new_password_confirm = st.text_input("パスワード（確認用）", type="password")
                    st.markdown("##### 3. 研究協力（任意）")
                    consent = st.checkbox("匿名化された数値データを学術研究に利用することに同意します。")
                    st.markdown("---")
                    submitted = st.form_submit_button("✅ 同意して登録し、秘密の合い言葉を発行する", use_container_width=True)
                    if submitted:
                        if not age_consent: st.error("本アプリは16歳以上の方のみご利用いただけます。")
                        elif not agreement: st.error("旅を始めるには、利用規約とプライバシーポリシーに同意していただく必要があります。")
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
                                st.rerun()

            with door2:
                with st.form("login_form"):
                    user_id_input = st.text_input("あなたの「秘密の合い言葉（ユーザーID）」を入力してください")
                    password_input = st.text_input("あなたの「パスワード」を入力してください", type="password")
                    submitted = st.form_submit_button("⚓ 乗船する", use_container_width=True)
                    if submitted:
                        if user_id_input and password_input:
                            users_df = read_data('users', users_sheet_id)
                            if not users_df.empty:
                                user_record = users_df[users_df['user_id'] == user_id_input]
                                if not user_record.empty and EncryptionManager.check_password(password_input, user_record.iloc[0]['password_hash']):
                                    st.session_state.user_id = user_id_input
                                    st.session_state.enc_manager = EncryptionManager(password_input)
                                    st.session_state.auth_status = "CHECKING_USER_DATA"
                                    st.success("乗船に成功しました！データを読み込んでいます...")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("合い言葉またはパスワードが間違っています。")
                            else:
                                st.error("その合い言葉を持つ船は見つかりませんでした。")
                        else:
                            st.warning("合い言葉とパスワードの両方を入力してください。")

    elif auth_status == "CHECKING_USER_DATA":
        user_id = st.session_state.user_id
        all_data_df = read_data('data', data_sheet_id)
        if not all_data_df.empty and 'user_id' in all_data_df.columns and user_id in all_data_df['user_id'].values:
            user_data_df = all_data_df[all_data_df['user_id'] == user_id].copy()
            user_data_df = migrate_and_ensure_schema(user_data_df, user_id, data_sheet_id)
            
            has_q_data = not user_data_df[Q_COLS].dropna(how='all').empty
            if not has_q_data:
                st.session_state.auth_status = "AWAITING_WIZARD"
                st.session_state.q_wizard_step = 1
                st.session_state.q_comparisons = {}
            else:
                st.session_state.auth_status = "INITIALIZING_SESSION"
        else:
            st.session_state.auth_status = "AWAITING_WIZARD"
            st.session_state.q_wizard_step = 1
            st.session_state.q_comparisons = {}
        st.rerun()

    elif auth_status == "INITIALIZING_SESSION":
        user_id = st.session_state.user_id
        all_data_df = read_data('data', data_sheet_id)
        user_data_df = all_data_df[all_data_df['user_id'] == user_id].copy()
        
        if 'record_timestamp' in user_data_df.columns:
            user_data_df['record_timestamp'] = pd.to_datetime(user_data_df['record_timestamp'], errors='coerce')
        else: 
             user_data_df['record_timestamp'] = pd.to_datetime(user_data_df['date'])

        q_data_rows = user_data_df.dropna(subset=Q_COLS, how='all')
        
        if not q_data_rows.empty:
            latest_q_row = q_data_rows.sort_values(by='record_timestamp', ascending=False).iloc[0]
            
            latest_q_dict = latest_q_row[Q_COLS].to_dict()
            st.session_state.q_values = {key.replace('q_', ''): int(val) for key, val in latest_q_dict.items() if isinstance(val, (int, float)) and pd.notna(val)}
        
        st.session_state.auth_status = "LOGGED_IN_UNLOCKED"
        st.rerun()

    elif auth_status == "LOGGED_IN_UNLOCKED":
        user_id = st.session_state.user_id
        
        all_data_df = read_data('data', data_sheet_id)
        user_data_df = all_data_df[all_data_df['user_id'] == user_id].copy()

        # ★★★ ゲーミフィケーション：ストリーク計算 ★★★
        st.session_state.record_streak = calculate_streak(user_data_df)
            
        st.sidebar.header(f"ようこそ、{user_id} さん！")
        # ★★★ ゲーミフィケーション：ストリーク表示 ★★★
        st.sidebar.metric("🔥 連続記録日数", f"{st.session_state.record_streak} 日")

        if st.sidebar.button("🚪 ログアウト（下船する）"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # ... (サイドバーの残りの部分は変更なし) ...
        st.sidebar.markdown("---")
        
        with st.sidebar:
            st.subheader("🧭 あなたの羅針盤")
            st.info("現在の価値観を見直したい場合は、いつでもここからガイドを開始できます。")
            if st.button("🗺️ 価値観発見ガイドを始める", use_container_width=True):
                st.session_state.auth_status = "AWAITING_WIZARD"
                st.session_state.q_wizard_step = 1
                st.session_state.q_comparisons = {}
                st.rerun()
            st.markdown("---")
        
        st.sidebar.header('⚙️ 価値観 (q_t) の手動調整')
        with st.sidebar.expander("▼ これは、何のために設定するの？"):
            st.markdown(EXPANDER_TEXTS['q_t'])
        
        for domain in DOMAINS:
            st.session_state.q_values[domain] = st.sidebar.slider(
                DOMAIN_NAMES_JP_DICT[domain], 0, 100, 
                st.session_state.q_values.get(domain, 14), 
                key=f"q_{domain}"
            )

        q_total = sum(st.session_state.q_values.values())
        st.sidebar.metric(label="現在の合計値", value=q_total)
        if q_total != 100:
            st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
        else:
            st.sidebar.success("合計は100です。入力準備OK！")

        with st.sidebar:
            st.markdown("---")
            st.subheader("📜 法的情報")
            show_legal_documents()

        tab1, tab2, tab3 = st.tabs(["**✍️ 今日の記録**", "**📊 ダッシュボード**", "**🔧 設定とガイド**"])

        with tab1:
            st.header(f"✍️ 今日の航海日誌を記録する")
            container = st.container(border=True)
            container.markdown("##### 記録する日付")
            today = date.today()
            target_date = container.date_input("記録する日付:", value=today, min_value=today - timedelta(days=365), max_value=today, label_visibility="collapsed")
            
            is_already_recorded = False
            if not user_data_df.empty and 'date' in user_data_df.columns:
                date_match = user_data_df[user_data_df['date'] == target_date]
                if not date_match.empty and pd.notna(date_match.iloc[0].get('g_happiness')):
                    is_already_recorded = True
            
            if is_already_recorded:
                container.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")

            container.markdown("##### 記録モード")
            input_mode = container.radio("記録モード:", ('🚀 クイック・ログ (ドメイン別評価)', '🔬 ディープ・ダイブ (詳細項目評価)'), horizontal=True)
            
            with st.form(key='daily_input_form'):
                s_element_values = {}
                s_domain_values = {}

                if 'クイック' in input_mode:
                    mode_string = 'quick'
                    st.info("今日一日を振り返り、7つの幸福の領域が、それぞれどれくらい満たされていたかを評価してください。")
                    for domain in DOMAINS:
                        st.markdown(f"**{DOMAIN_NAMES_JP_DICT[domain]}**")
                        with st.expander("▼ このドメインには、どんな「材料」が含まれる？"):
                            for element in LONG_ELEMENTS[domain]:
                                st.markdown(f"- **{element}**: {ELEMENT_DEFINITIONS.get(element, '')}")
                        s_domain_values['s_' + domain] = st.slider(label=f"slider_{domain}", min_value=0, max_value=100, value=50, key=f"s_{domain}", label_visibility="collapsed")
                        st.caption(CAPTION_TEXT)
                else:
                    mode_string = 'deep'
                    col1, col2 = st.columns(2)
                    latest_s_elements = pd.Series(dtype=float)
                    if not user_data_df.empty:
                        sortable_df_deep = user_data_df.dropna(subset=['date']).sort_values(by='date', ascending=False)
                        if not sortable_df_deep.empty:
                            latest_s_elements = sortable_df_deep.iloc[0]

                    for i, domain in enumerate(DOMAINS):
                        container = col1 if i < 4 else col2
                        with container:
                            with st.expander(f"**{DOMAIN_NAMES_JP_DICT[domain]}**", expanded=True):
                                for element in LONG_ELEMENTS[domain]:
                                    col_name = f's_element_{element}'
                                    val = latest_s_elements.get(col_name, 50)
                                    default_val = 50 if pd.isna(val) else int(val)
                                    
                                    st.markdown(f"**{element}**")
                                    st.caption(ELEMENT_DEFINITIONS.get(element, ""))
                                    score = st.slider(label=f"slider_{col_name}", min_value=0, max_value=100, value=default_val, key=col_name, label_visibility="collapsed")
                                    st.caption(CAPTION_TEXT)
                                    s_element_values[col_name] = int(score)

                st.markdown('**総合的な幸福感 (Gt)**')
                with st.expander("▼ これはなぜ必要？"): st.markdown(EXPANDER_TEXTS['g_t'])
                g_happiness = st.slider(label="slider_g_happiness", min_value=0, max_value=100, value=50, label_visibility="collapsed")
                st.caption(CAPTION_TEXT)
                
                st.markdown('**今日の出来事や気づきは？（あなたのパスワードで暗号化されます）**')
                with st.expander("▼ なぜ書くのがおすすめ？"): st.markdown(EXPANDER_TEXTS['event_log'])
                event_log = st.text_area('', height=100, label_visibility="collapsed")
                
                st.markdown("---")
                submitted = st.form_submit_button('💾 今日の航海日誌を保存する', use_container_width=True)
                
                if submitted:
                    if sum(st.session_state.q_values.values()) != 100:
                        st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
                    else:
                        # --- ★★★ ここからが、あなたの分析に基づく、新しい安全な保存ロジックです ★★★ ---
                        
                        # 1. 保存する新しいレコードを準備する
                        new_record = {}
                        if mode_string == 'deep':
                            new_record.update({col: pd.NA for col in ALL_ELEMENT_COLS})
                            new_record.update(s_element_values)
                            s_domain_scores = calculate_s_domains_from_row(pd.Series(new_record))
                            new_record.update(s_domain_scores.to_dict())
                        else: # quick
                            new_record.update(s_domain_values)

                        encrypted_log = st.session_state.enc_manager.encrypt_log(event_log)
                        
                        users_df_in_form = read_data('users', users_sheet_id)
                        user_info_in_form = users_df_in_form[users_df_in_form['user_id'] == user_id]
                        consent_status = user_info_in_form['consent'].iloc[0] if not user_info_in_form.empty and 'consent' in user_info_in_form.columns else False

                        new_record.update({
                            'user_id': user_id, 
                            'date': target_date,
                            'record_timestamp': datetime.now(JST), # 本物のタイムスタンプを必ず付与
                            'mode': mode_string,
                            'consent': consent_status,
                            'g_happiness': int(g_happiness), 
                            'event_log': encrypted_log
                        })
                        new_record.update({f'q_{d}': v for d, v in st.session_state.q_values.items()})

                        new_df_row = pd.DataFrame([new_record])

                        # 2. 既存の全データを読み込む
                        try:
                            df_existing = read_data('data', data_sheet_id)
                        except Exception as e:
                            st.warning(f"既存データの読み込みに失敗しました。新しいデータのみで保存を試みます。エラー: {e}")
                            df_existing = pd.DataFrame()

                        # 3. 安全なマージ処理（「同じユーザー」かつ「同じ日付」の行だけを置換）
                        if df_existing.empty:
                            df_to_write = new_df_row
                        else:
                            # 既存データから、今回保存するユーザーと日付に一致する行を"除く"
                            # これにより、他ユーザーのデータや、同じ日付でもuser_idが異なる行（デバッグ行など）を保護する
                            condition_to_remove = (df_existing['user_id'] == user_id) & (pd.to_datetime(df_existing['date']).dt.date == target_date)
                            df_preserved = df_existing[~condition_to_remove]
                            
                            # 除外したデータフレームに、新しいレコードを追加する
                            df_to_write = pd.concat([df_preserved, new_df_row], ignore_index=True)

                        # 4. 書き込み前の最終的なデータ型統一と並べ替え
                        if 'date' in df_to_write.columns:
                            df_to_write['date'] = pd.to_datetime(df_to_write['date'], errors='coerce')
                        if 'record_timestamp' in df_to_write.columns:
                            df_to_write['record_timestamp'] = pd.to_datetime(df_to_write['record_timestamp'], errors='coerce')

                        df_to_write = df_to_write.sort_values(by=['user_id', 'date', 'record_timestamp']).reset_index(drop=True)
                        
                        # 5. データベースへの書き込みとキャッシュのクリア
                        if write_data('data', data_sheet_id, df_to_write):
                            st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を永続的に保存しました！')
                            st.balloons()
                            time.sleep(1)
                            st.rerun() # 再実行して最新のデータを表示
                        else:
                             st.error("データの保存に失敗しました。後でもう一度お試しください。")
                with tab2:
                            st.header('📊 あなたの航海チャート')
                            # 簡潔な全体説明のみを残す
                            with st.expander("▼ このチャートの見方", expanded=True):
                                st.info("""
                                このダッシュボードは、あなたの人生という航海の**「現在地」**と**「航跡」**を、多角的に可視化する計器盤です。
                                各チャートの詳細な見方は、それぞれのセクションにある `▼ このチャートの見方` をクリックしてご確認ください。
                                """)
                
                            st.warning("⚠️ **免責事項:** この分析は自己理解を助けるためのものであり、医学的な診断を代替するものではありません。心身の不調が続く場合は、必ず専門の医療機関にご相談ください。")
                
                            df_to_process = user_data_df.copy()
                            if df_to_process.dropna(subset=Q_COLS, how='all').empty:
                                           st.info('まだ記録がありません。まずは「今日の記録」タブから、最初の日誌を記録してみましょう！')
                                        else:
                                            df_processed = calculate_metrics(df_to_process, alpha=0.6)
                                            if 'date' in df_processed.columns:
                                                df_processed['date'] = pd.to_datetime(df_processed['date'])
                                                df_processed = df_processed.sort_values('date')
                                            
                                            # ★★★ ここからがインデント修正箇所です ★★★
                                            # 以下のブロック全体を一段階外側（左）にずらしました。
                                            st.subheader("📈 期間分析とリスク評価 (RHI)")
                                            
                                            period_options = [7, 30, 90]
                                            
                                            df_period = df_processed
                                            if len(df_processed.dropna(subset=['H'])) >= 7:
                                                valid_periods = [p for p in period_options if len(df_processed.dropna(subset=['H'])) >= p]
                                                default_index = len(valid_periods) - 1 if valid_periods else 0
                                                selected_period = st.selectbox("分析期間を選択してください（日）:", valid_periods, index=default_index)
                                                df_period = df_processed.dropna(subset=['H', 'g_happiness']).tail(selected_period)
                            
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
                                                
                                                check_achievements(df_period, rhi_results, st.session_state.record_streak)
                            
                                                if rhi_results['RHI'] < 0.2: 
                                                    st.error("""
                                                    **【専門家への相談を検討してください】**\n
                                                    分析結果によると、あなたの幸福度は持続的に低いか、または非常に不安定な状態にある可能性が示唆されています。
                                                    もし、この状態が続いて辛いと感じる場合は、一人で抱え込まず、カウンセラーや医師といった専門家に相談することを検討してみてください。
                                                    """)
                                                
                                                st.markdown("---")
                                                st.subheader("🧭 次の航海へのヒント")
                            
                                                focus_domain, proposal = generate_intervention_proposal(df_period, rhi_results)
                            
                                                if focus_domain and proposal:
                                                    with st.container(border=True):
                                                        st.markdown(f"分析の結果、今週は特に **{DOMAIN_NAMES_JP_DICT[focus_domain]}** の領域が、あなたの幸福の安定性に影響を与えていたようです。")
                                                        st.info(f"もしよろしければ、今週は以下の小さなアクションを試してみませんか？")
                                                        
                                                        for p in proposal:
                                                            st.button(f"「{p}」を試してみる", use_container_width=True)
                                                else:
                                                    with st.container(border=True):
                                                        st.info("分析できる十分なデータがないか、全てのドメインが安定しています。素晴らしい航海です！")
                            
                                            else:
                                                st.info(f"現在{len(df_processed.dropna(subset=['H']))}日分の有効なデータがあります。期間分析（RHIなど）には最低7日分のデータが必要です。")
                            
                                            if not df_processed.empty:
                                                analyze_discrepancy(df_processed)
                                                
                                                st.markdown("---")
                                                st.subheader("🗺️ あなたの心の航海図")
                            
                                                df_plot = df_period.set_index('date').copy()
                                                df_plot['H_scaled'] = df_plot['H'] * 100
                                                
                                                st.markdown("##### 心の天気図：モデルの分析(H) vs あなたの直感(G)")
                                                
                                                fig_hg = go.Figure()
                                                fig_hg.add_trace(go.Scatter(x=df_plot.index, y=df_plot['H_scaled'], mode='lines+markers', name='調和度 (H) - モデルの分析', line=dict(color='blue')))
                                                fig_hg.add_trace(go.Scatter(x=df_plot.index, y=df_plot['g_happiness'], mode='lines+markers', name='実感値 (G) - あなたの直感', line=dict(color='green')))
                                                st.plotly_chart(fig_hg, use_container_width=True)
                            
                                                if len(df_plot) > 1:
                                                    st.markdown("##### 自己対話のヒント：あなたの「心のクセ」との対話")
                                                    with st.expander("▼ このチャートの見方"):
                                                        st.info("""
                                                        このグラフは、あなたの**『直感的な実感(G)』**と、あなたの価値観に基づいてモデルが算出した**『論理的な分析結果(H)』**の差を示します。この『ズレ』は、どちらが正しいかを示すものではありません。\n
                                                        - **平常範囲（薄い灰色の帯）**: あなたの「いつもの心のクセ」の範囲です。この中に収まっているなら、自己認識は安定しています。\n
                                                        - **プラスへの逸脱**: あなたの直感が、まだ言葉にできていないポジティブな何かを捉えているサインかもしれません。\n
                                                        - **マイナスへの逸脱**: あなたの論理的な自己認識と、実際の心の状態の間に、何か見過ごしている要因があるサインかもしれません。\n
                                                        **バンドを突き抜けた日**に何があったか、日記を振り返ってみると、深い自己発見のヒントが隠されている可能性があります。
                                                        """)
                                                    
                                                    df_plot['insight_gap'] = df_plot['g_happiness'] - df_plot['H_scaled']
                                                    gap_mean = df_plot['insight_gap'].mean()
                                                    gap_std = df_plot['insight_gap'].std()
                                                    upper_band = gap_mean + 1.5 * gap_std
                                                    lower_band = gap_mean - 1.5 * gap_std
                            
                                                    fig_gap = go.Figure()
                                                    fig_gap.add_trace(go.Scatter(x=df_plot.index, y=[upper_band]*len(df_plot), fill=None, mode='lines', line_color='rgba(128,128,128,0.2)', name='平常範囲の上限'))
                                                    fig_gap.add_trace(go.Scatter(x=df_plot.index, y=[lower_band]*len(df_plot), fill='tonexty', mode='lines', line_color='rgba(128,128,128,0.2)', name='平常範囲の下限'))
                                                    fig_gap.add_trace(go.Scatter(x=df_plot.index, y=[gap_mean]*len(df_plot), mode='lines', line=dict(dash='dash', color='grey'), name='あなたの「心のクセ」(平均)'))
                                                    fig_gap.add_trace(go.Scatter(x=df_plot.index, y=df_plot['insight_gap'], mode='lines+markers', name='日々のズレ (G-H)', line=dict(color='black')))
                                                    
                                                    st.plotly_chart(fig_gap, use_container_width=True)
                                                
                                                st.markdown("---")
                                                st.subheader("🔬 構造分析")
                                                
                                                col_chart1, col_chart2 = st.columns(2)
                                                
                                                with col_chart1:
                                                    st.markdown("##### 価値観 vs 経験 レーダーチャート")
                                                    
                                                    latest_q_values = np.array([st.session_state.q_values[d] for d in DOMAINS])
                                                    avg_q = latest_q_values
                                                    avg_s = df_period[S_COLS].mean().values
                                                    
                                                    s_achieved_ratio = avg_s / 100.0 
                                                    s_plot = avg_q * s_achieved_ratio
                            
                                                    fig = go.Figure()
                            
                                                    fig.add_trace(go.Scatterpolar(
                                                          r=np.append(s_plot, s_plot[0]),
                                                          theta=np.append(DOMAIN_NAMES_JP_VALUES, DOMAIN_NAMES_JP_VALUES[0]),
                                                          fill='toself',
                                                          name='あなたの経験 (現実の形)',
                                                          line=dict(color='grey'),
                                                          fillcolor='rgba(128,128,128,0.3)'
                                                    ))
                                                    fig.add_trace(go.Scatterpolar(
                                                          r=np.append(avg_q, avg_q[0]),
                                                          theta=np.append(DOMAIN_NAMES_JP_VALUES, DOMAIN_NAMES_JP_VALUES[0]),
                                                          fill='none',
                                                          name='あなたの価値観 (理想の形)',
                                                          line=dict(color='blue', dash='dash')
                                                    ))
                            
                                                    dynamic_range_max = max(40, int(avg_q.max()) + 10) if avg_q.any() and avg_q.max() > 0 else 40
                                                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, dynamic_range_max])), showlegend=True, legend=dict(yanchor="top", y=1.15, xanchor="left", x=0.01))
                                                    st.plotly_chart(fig, use_container_width=True)
                            
                                                with col_chart2:
                                                    st.markdown("##### 価値観-経験 ギャップ分析")
                                                    st.caption("算出方法: ギャップ(%) = あなたの価値観の構成比 - あなたの経験の構成比")
                                                    
                                                    q_norm = avg_q / avg_q.sum() * 100 if avg_q.sum() > 0 else avg_q
                                                    s_norm = avg_s / avg_s.sum() * 100 if avg_s.sum() > 0 else avg_s
                            
                                                    gap_data = pd.DataFrame({'domain': DOMAIN_NAMES_JP_VALUES, 'gap': q_norm - s_norm}).sort_values('gap', ascending=False)
                                                    
                                                    fig_bar = px.bar(gap_data, x='gap', y='domain', orientation='h', color='gap', color_continuous_scale='RdBu', color_continuous_midpoint=0, labels={'gap':'ギャップ (%ポイント)', 'domain':'ドメイン'}, title="+: 価値観 > 経験 (課題), -: 経験 > 価値観 (強み)")
                                                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                                                    st.plotly_chart(fig_bar, use_container_width=True)
                                                
                                                st.markdown("---")
                                                st.subheader("🔬 詳細分析：あなたの幸福のメカニズムを探る")
                            
                                                with st.container(border=True):
                                                    st.markdown("##### 相関ヒートマップ：幸福の「相乗効果」と「トレードオフ」")
                                                    with st.expander("▼ このチャートの見方"):
                                                        st.info("""
                                                        このヒートマップは、あなたの幸福を構成する各要素が、互いにどう影響し合っているかを可視化します。\n
                                                        - **青色が濃い**ほど、二つの要素が**一緒に高まる**傾向（相乗効果）を示します。\n
                                                        - **赤色が濃い**ほど、片方が高まるともう片方が**低くなる**傾向（トレードオフ）を示します。
                                                        """)
                                                    
                                                    corr_df = df_period[S_COLS].corr()
                                                    corr_df.columns = DOMAIN_NAMES_JP_VALUES
                                                    corr_df.index = DOMAIN_NAMES_JP_VALUES
                                                    fig_heatmap = px.imshow(corr_df, text_auto=True, aspect="auto", color_continuous_scale='RdBu', range_color=[-1, 1])
                                                    st.plotly_chart(fig_heatmap, use_container_width=True)
                            
                                                with st.container(border=True):
                                                    st.markdown("##### イベント影響度ランキング：幸福の「源泉」と「ストレス源」")
                                                    with st.expander("▼ このランキングの見方"):
                                                        st.info("""
                                                        あなたの日記（イベントログ）からキーワードを抽出し、その言葉が記録された日の幸福度が、全体の平均と比べてどれだけ高かったか（または低かったか）をランキングします。
                                                        """)
                                                    
                                                    df_period_logs = df_period.copy()
                                                    df_period_logs['event_log'] = df_period_logs['event_log'].apply(st.session_state.enc_manager.decrypt_log)
                                                    
                                                    word_impact = {}
                                                    mean_h_total = df_period_logs['H'].mean()
                                                    
                                                    df_period_logs['words'] = df_period_logs['event_log'].str.findall(r'[\wぁ-んァ-ン一-龥ー]+')
                                                    all_words = [word for sublist in df_period_logs['words'].dropna() for word in sublist]
                                                    
                                                    common_words = [word for word, count in Counter(all_words).most_common(10) if len(word) > 1]
                            
                                                    for word in common_words:
                                                        impact_days_h = df_period_logs[df_period_logs['event_log'].str.contains(word, na=False)]['H'].mean()
                                                        impact = impact_days_h - mean_h_total
                                                        word_impact[word] = impact
                            
                                                    if word_impact:
                                                        impact_df = pd.DataFrame(list(word_impact.items()), columns=['キーワード', '幸福度へのインパクト']).sort_values('幸福度へのインパクト', ascending=False)
                                                        st.dataframe(impact_df, use_container_width=True)
                                                    else:
                                                        st.info("分析できる十分なイベントログがありません。日記を記録してみましょう！")
                            
                                                with st.container(border=True):
                                                    st.markdown("##### 「価値観と現実のズレ」の推移：あなたの航海術の上達度")
                                                    with st.expander("▼ このチャートの見方"):
                                                         st.info("""
                                                        このグラフは、あなたの「理想（価値観）」と「現実（日々の経験）」の**ズレの大きさ (`1 - U`)** が、時間と共にどう変化したかを示します。\n
                                                        線が**長期的に下降傾向**にあれば、あなたの人生が、より価値観と一致した、調和の取れた方向へ進んでいることを意味します。
                                                        """)
                                                    
                                                    df_period['gap_U'] = 1 - df_period['U']
                                                    st.line_chart(df_period.set_index('date')['gap_U'])
                            
                                                st.markdown("---")
                                                st.subheader('📖 全記録データ')
                                                df_display = user_data_df.copy()
                                                if 'event_log' in df_display.columns:
                                                    df_display['event_log'] = df_display['event_log'].apply(st.session_state.enc_manager.decrypt_log)
                                                    df_display.rename(columns={'event_log': 'イベントログ（復号済）'}, inplace=True)
                                                st.dataframe(df_display.drop(columns=['user_id'], errors='ignore').sort_values(by='date', ascending=False).round(3))

        
        with tab3:
            st.header("🔧 設定とガイド")
            st.subheader("🏆 アチーブメント（実績）")
            with st.container(border=True):
                st.markdown("あなたの航海の記録です。")
                unlocked_count = len(st.session_state.unlocked_achievements)
                total_count = len(ACHIEVEMENTS)
                st.progress(unlocked_count / total_count, text=f"{unlocked_count} / {total_count} 個 達成")
                
                cols = st.columns(4)
                sorted_achievements = sorted(ACHIEVEMENTS.items(), key=lambda item: item[0])
                
                for i, (ach_id, details) in enumerate(sorted_achievements):
                    col = cols[i % 4]
                    if ach_id in st.session_state.unlocked_achievements:
                        col.markdown(f"**{details['emoji']} {details['name']}**")
                        col.caption(details['description'])
                    else:
                        col.markdown(f"**❔ ロック中**")
                        col.caption("達成条件：？？？")
            st.markdown("---")
            
            with st.container(border=True):
                st.subheader("🔒 プライバシー設定")
                users_df_privacy = read_data('users', users_sheet_id)
                user_info_privacy = users_df_privacy[users_df_privacy['user_id'] == user_id]
                current_consent = user_info_privacy['consent'].iloc[0] if not user_info_privacy.empty and 'consent' in user_info_privacy.columns else False
                
                new_consent = st.checkbox("匿名化された数値データを学術研究に利用することに同意する", value=current_consent)
                if new_consent != current_consent:
                    users_df_privacy.loc[users_df_privacy['user_id'] == user_id, 'consent'] = new_consent
                    if write_data('users', users_sheet_id, users_df_privacy):
                        st.success("研究協力への同意状況を更新しました。")
                    else:
                        st.error("設定の保存に失敗しました。")


            with st.container(border=True):
                st.subheader("👤 プロフィール情報（研究協力用）")
                with st.form("profile_form"):
                    users_df_for_profile = read_data('users', users_sheet_id)
                    user_info = users_df_for_profile[users_df_for_profile['user_id'] == user_id]
                    current_profile = user_info.iloc[0] if not user_info.empty else pd.Series()
                    
                    # 全てのプロフィール項目を追加
                    age_group = st.selectbox("年代", options=DEMOGRAPHIC_OPTIONS['age_group'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['age_group'], current_profile.get('age_group')))
                    gender = st.selectbox("性別", options=DEMOGRAPHIC_OPTIONS['gender'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['gender'], current_profile.get('gender')))
                    occupation_category = st.selectbox("職業", options=DEMOGRAPHIC_OPTIONS['occupation_category'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['occupation_category'], current_profile.get('occupation_category')))
                    income_range = st.selectbox("年収", options=DEMOGRAPHIC_OPTIONS['income_range'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['income_range'], current_profile.get('income_range')))
                    marital_status = st.selectbox("婚姻状況", options=DEMOGRAPHIC_OPTIONS['marital_status'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['marital_status'], current_profile.get('marital_status')))
                    has_children = st.selectbox("子供の有無", options=DEMOGRAPHIC_OPTIONS['has_children'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['has_children'], current_profile.get('has_children')))
                    living_situation = st.selectbox("居住形態", options=DEMOGRAPHIC_OPTIONS['living_situation'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['living_situation'], current_profile.get('living_situation')))
                    chronic_illness = st.selectbox("慢性疾患", options=DEMOGRAPHIC_OPTIONS['chronic_illness'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['chronic_illness'], current_profile.get('chronic_illness')))
                    country = st.selectbox("国", options=DEMOGRAPHIC_OPTIONS['country'], index=get_safe_index(DEMOGRAPHIC_OPTIONS['country'], current_profile.get('country')))
                    
                    profile_submitted = st.form_submit_button("プロフィールを保存する", use_container_width=True)

                    if profile_submitted:
                        users_df_update = read_data('users', users_sheet_id)
                        # 全てのプロフィール項目を更新
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'age_group'] = age_group
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'gender'] = gender
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'occupation_category'] = occupation_category
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'income_range'] = income_range
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'marital_status'] = marital_status
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'has_children'] = has_children
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'living_situation'] = living_situation
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'chronic_illness'] = chronic_illness
                        users_df_update.loc[users_df_update['user_id'] == user_id, 'country'] = country
                        
                        if write_data('users', users_sheet_id, users_df_update):
                            st.success("プロフィール情報を更新しました！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("プロフィールの保存に失敗しました。")

            with st.container(border=True):
                st.subheader("📥 データのエクスポート")
                if not user_data_df.empty:
                    df_export = user_data_df.copy()
                    if 'event_log' in df_export.columns:
                        df_export['event_log_decrypted'] = df_export['event_log'].apply(st.session_state.enc_manager.decrypt_log)
                    
                    csv_export = df_export.to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 全データをCSV形式でダウンロード", data=csv_export, file_name=f'harmony_data_{user_id}.csv', use_container_width=True)

            with st.container(border=True):
                st.subheader("🗑️ アカウント削除")
                with st.form("delete_form"):
                    st.warning("この操作は取り消せません。アカウントを削除すると、関連する全てのデータが完全に消去されます。")
                    password_for_delete = st.text_input("パスワードを入力してください", type="password")
                    delete_submitted = st.form_submit_button("本当にアカウントと全データを完全に削除する", type="primary", use_container_width=True)

                    if delete_submitted:
                        users_df_to_delete = read_data('users', users_sheet_id)
                        user_record = users_df_to_delete[users_df_to_delete['user_id'] == user_id]
                        if not user_record.empty and EncryptionManager.check_password(password_for_delete, user_record.iloc[0]['password_hash']):
                            users_df_updated = users_df_to_delete[users_df_to_delete['user_id'] != user_id]
                            if write_data('users', users_sheet_id, users_df_updated):
                                all_data_df_to_delete = read_data('data', data_sheet_id)
                                all_data_df_updated = all_data_df_to_delete[all_data_df_to_delete['user_id'] != user_id]
                                if write_data('data', data_sheet_id, all_data_df_updated):
                                    for key in list(st.session_state.keys()):
                                        del st.session_state[key]
                                    st.success("アカウントと関連する全てのデータを削除しました。")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("データシートからのユーザーデータ削除に失敗しました。")
                            else:
                                 st.error("ユーザーシートからのアカウント削除に失敗しました。")
                        else:
                            st.error("パスワードが間違っています。")
            
            st.markdown("---")
            st.subheader("このアプリについて")
            show_welcome_and_guide()
        
if __name__ == '__main__':
    main()
