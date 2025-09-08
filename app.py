import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
import os
from datetime import datetime, date, timedelta
import re
import glob

# --- 0. 定数と基本設定 ---
DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP = {
    'health': '1. 健康', 'relationships': '2. 人間関係', 'meaning': '3. 意味・貢献',
    'autonomy': '4. 自律・成長', 'finance': '5. 経済', 'leisure': '6. 余暇・心理', 'competition': '7. 競争'
}

# --- 【v0.9.3最重要機能】材料ごとの詳細な解説を定義 ---
ELEMENT_DEFINITIONS = {
    # 健康
    '睡眠と休息': '心身ともに、十分な休息が取れたと感じる度合い。例：朝、すっきりと目覚められたか。',
    '身体的な快調さ': '活力を感じ、身体的な不調（痛み、疲れなど）がなかった度合い。',
    '睡眠': '質の良い睡眠がとれ、朝、すっきりと目覚められた度合い。',
    '食事': '栄養バランスの取れた、美味しい食事に満足できた度合い。',
    '運動': '体を動かす習慣があり、それが心身の快調さに繋がっていた度合い。',
    '身体的快適さ': '慢性的な痛みや、気になる不調がなく、快適に過ごせた度合い。',
    '感覚的快楽': '五感を通じて、心地よいと感じる瞬間があった度合い。例：温かいお風呂、心地よい音楽。',
    '性的満足': '自身の性的な欲求や、パートナーとの親密さに対して、満足感があった度合い。',
    # 人間関係
    '親密な関係': '家族やパートナー、親しい友人との、温かい、あるいは安心できる繋がりを感じた度合い。',
    '利他性・貢献': '自分の行動が、誰かの役に立った、あるいは喜ばれたと感じた度合い。例：「ありがとう」と言われた。',
    '家族': '家族との間に、安定した、あるいは温かい関係があった度合い。',
    'パートナー・恋愛': 'パートナーとの間に、愛情や深い理解、信頼があった度合い。',
    '友人': '気軽に話せたり、支え合えたりする友人がおり、良い関係を築けていた度合い。',
    '社会的承認': '周囲の人々（職場、地域など）から、一員として認められ、尊重されていると感じた度合い。',
    '共感・繋がり': '他者の気持ちに寄り添ったり、逆に寄り添ってもらったりして、人との深い繋がりを感じた度合い。',
    # 意味・貢献
    '仕事・学業の充実感': '自分の仕事や学びに、やりがいや達成感を感じた度合い。',
    '価値との一致': '自分の大切にしている価値観や信念に沿って、行動できたと感じられる度合い。',
    'やりがい': '自分の仕事や活動（学業、家事、趣味など）に、意義や目的を感じ、夢中になれた度合い。',
    '達成感': '何か具体的な目標を達成したり、物事を最後までやり遂げたりする経験があった度合い。',
    '信念との一致': '自分の「こうありたい」という価値観や、倫理観に沿った行動ができた度合い。',
    'キャリアの展望': '自分の将来のキャリアに対して、希望や前向きな見通しを持てていた度合い。',
    '社会への貢献': '自分の活動が、所属するコミュニティや、より大きな社会に対して、良い影響を与えていると感じられた度合い。',
    '有能感': '自分のスキルや能力を、うまく発揮できているという感覚があった度合い。',
    # 自律・成長
    '自己決定感': '今日の自分の行動は、自分で決めたと感じられる度合い。',
    '自己成長の実感': '何かを乗り越え、自分が成長した、あるいは新しいことを学んだと感じた度合い。',
    '自由・自己決定': '自分の人生における重要な事柄を、他者の圧力ではなく、自分自身の意志で選択・決定できていると感じた度合い。',
    '挑戦・冒険': '新しいことに挑戦したり、未知の経験をしたりして、刺激や興奮を感じた度合い。',
    '変化の享受': '環境の変化や、新しい考え方を、ポジティブに受け入れ、楽しむことができた度合い。',
    '独立・自己信頼': '自分の力で物事に対処できるという、自分自身への信頼感があった度合い。',
    '好奇心': '様々な物事に対して、知的な好奇心を持ち、探求することに喜びを感じた度合い。',
    # 経済
    '経済的な安心感': '日々の生活や将来のお金について、過度な心配をせず、安心して過ごせた度合い。',
    '職業的な達成感': '仕事や学業において、物事をうまくやり遂げた、あるいは目標に近づいたと感じた度合い。',
    '経済的安定': '「来月の支払いは大丈夫かな…」といった、短期的なお金の心配がない状態。',
    '経済的余裕': '生活必需品だけでなく、趣味や自己投資など、人生を豊かにすることにもお金を使える状態。',
    '労働環境': '物理的にも、精神的にも、安全で、健康的に働ける環境があった度合い。',
    'ワークライフバランス': '仕事（あるいは学業）と、プライベートな生活との間で、自分が望むバランスが取れていた度合い。',
    '公正な評価': '自分の働きや成果が、正当に評価され、報酬に反映されていると感じられた度合い。',
    '職業的安定性': '「この先も、この仕事を続けていけるだろうか」といった、長期的なキャリアや収入に対する不安がない状態。',
    # 余暇・心理
    '心の平穏': '過度な不安やストレスなく、精神的に安定していた度合い。',
    '楽しさ・喜び': '純粋に「楽しい」と感じたり、笑ったりする瞬間があった度合い。',
    '自己肯定感': '自分の長所も短所も含めて、ありのままの自分を、肯定的に受け入れることができた度合い。',
    '創造性の発揮': '何かを創作したり、新しいアイデアを思いついたりして、創造的な喜びを感じた度合い。',
    '感謝': '日常の小さな出来事や、周りの人々に対して、自然と「ありがたい」という気持ちが湧いた度合い。',
    '娯楽・楽しさ': '趣味に没頭したり、友人と笑い合ったり、純粋に「楽しい」と感じる時間があった度合い。',
    '芸術・自然': '美しい音楽や芸術、あるいは雄大な自然に触れて、心が動かされたり、豊かになったりする経験があった度合い。',
    # 競争
    '優越感・勝利': '他者との比較や、スポーツ、仕事、学業などにおける競争において、優位に立てたと感じた度合い。'
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
SLIDER_HELP_TEXT = "0: 全く当てはまらない\n\n25: あまり当てはまらない\n\n50: どちらとも言えない\n\n75: やや当てはまる\n\n100: 完全に当てはまる"

# --- 1. 計算ロジック・インサイトエンジン関数（v0.9.2から変更なし） ---
# ... (v0.9.2のコード) ...
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    s_vectors_normalized = df_copy[S_COLS].values / 100.0
    q_vectors = df_copy[Q_COLS].values
    df_copy['S'] = np.sum(q_vectors * s_vectors_normalized, axis=1)
    def calculate_unity(row):
        q_vec = row[Q_COLS].values
        s_vec_raw = row[S_COLS].values
        s_sum = np.sum(s_vec_raw)
        if s_sum == 0: return 0.0
        s_tilde = s_vec_raw / s_sum
        jsd_sqrt = jensenshannon(q_vec, s_tilde)
        jsd = jsd_sqrt**2
        return 1 - jsd
    df_copy['U'] = df_copy.apply(calculate_unity, axis=1)
    df_copy['H'] = alpha * df_copy['S'] + (1 - alpha) * df_copy['U']
    return df_copy

def analyze_discrepancy(df_processed: pd.DataFrame, threshold: int = 20):
    if df_processed.empty: return
    latest_record = df_processed.iloc[-1]
    latest_h_normalized = latest_record['H']
    latest_g = latest_record['g_happiness']
    latest_h = latest_h_normalized * 100
    gap = latest_g - latest_h
    st.subheader("💡 インサイト・エンジン")
    if gap > threshold: st.info(f"**【幸福なサプライズ！🎉】**...")
    elif gap < -threshold: st.warning(f"**【隠れた不満？🤔】**...")
    else: st.success(f"**【順調な航海です！✨】**...")

def safe_filename(name): return re.sub(r'[^a-zA-Z0-9_-]', '_', name)
def get_existing_users():
    files = glob.glob("harmony_data_*.csv")
    users = [f.replace("harmony_data_", "").replace(".csv", "") for f in files]
    return users

# --- 2. アプリケーションのUIとロジック ---
st.set_page_config(layout="wide", page_title="Harmony Navigator")
st.title(f'🧭 Harmony Navigator (MVP v0.9.3)')
st.caption('あなたの「理想」と「現実」のズレを可視化し、より良い人生の航路を見つけるための道具')

# --- ユーザー認証 ---
# ... (v0.9.2のコード) ...
st.sidebar.header("👤 ユーザー認証")
if 'username' not in st.session_state: st.session_state['username'] = None
auth_mode = st.sidebar.radio("モードを選択してください:", ("ログイン", "新規登録"))
existing_users = get_existing_users()
if auth_mode == "ログイン":
    if not existing_users:
        st.sidebar.warning("登録済みのユーザーがいません。まずは新規登録してください。")
    else:
        selected_user = st.sidebar.selectbox("ユーザーを選択してください:", [""] + existing_users)
        if st.sidebar.button("ログイン", key="login_button"):
            if selected_user:
                st.session_state['username'] = selected_user
                st.rerun() 
            else:
                st.sidebar.error("ユーザーを選択してください。")
elif auth_mode == "新規登録":
    new_username_raw = st.sidebar.text_input("新しいユーザー名を入力してください:", key="new_username_input")
    if st.sidebar.button("登録", key="register_button"):
        new_username_safe = safe_filename(new_username_raw)
        if not new_username_safe: st.sidebar.error("ユーザー名を入力してください。")
        elif new_username_safe in existing_users: st.sidebar.error("その名前はすでに使われています。別の名前を入力するか、ログインしてください。")
        else:
            st.session_state['username'] = new_username_safe
            st.sidebar.success(f"ようこそ、{new_username_safe}さん！新しい航海日誌を作成します。")
            st.rerun()


# --- メインアプリの表示 ---
if st.session_state.get('username'):
    username = st.session_state['username']
    CSV_FILE = CSV_FILE_TEMPLATE.format(username)
    st.header(f"ようこそ、{username} さん！")

    # (データ読み込み、記録状況確認、価値観設定はv0.9.2と同様)
    # ...
    if os.path.exists(CSV_FILE):
        df_data = pd.read_csv(CSV_FILE, parse_dates=['date'])
        df_data['date'] = df_data['date'].dt.date
    else:
        columns = ['date', 'mode'] + Q_COLS + S_COLS + ['g_happiness', 'event_log']
        for _, elements in LONG_ELEMENTS.items():
            for element in elements:
                columns.append(f's_element_{element}')
        df_data = pd.DataFrame(columns=columns)
    today = date.today()
    if not df_data[df_data['date'] == today].empty: st.sidebar.success(f"✅ 今日の記録 ({today.strftime('%Y-%m-%d')}) は完了しています。")
    else: st.sidebar.info(f"ℹ️ 今日の記録 ({today.strftime('%Y-%m-%d')}) はまだありません。")
    st.sidebar.header('⚙️ 価値観 (q_t) の設定')
    with st.sidebar.expander("▼ これは何？どう入力する？"): st.markdown("...")
    if not df_data.empty and all(col in df_data.columns for col in Q_COLS): latest_q = df_data[Q_COLS].iloc[-1].values * 100
    else: latest_q = [15, 15, 15, 15, 15, 15, 10]
    q_values = {}
    for i, domain in enumerate(DOMAINS):
        q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP[domain], 0, 100, int(latest_q[i]), key=f"q_{domain}")
    q_total = sum(q_values.values())
    st.sidebar.metric(label="現在の合計値", value=q_total)
    if q_total != 100: st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
    else: st.sidebar.success("合計は100です。入力準備OK！")

    # --- メイン画面：日々の記録 ---
    st.header('✍️ 今日の航海日誌を記録する')
    with st.expander("▼ これは、何のために記録するの？"): st.markdown("...")
    st.markdown("##### 記録する日付")
    target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
    if not df_data[df_data['date'] == target_date].empty: st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")
    st.markdown("##### 記録モード")
    input_mode = st.radio("記録モード:", ('🚀 **クイック・ログ**', '🔬 **ディープ・ダイブ**'), horizontal=True, label_visibility="collapsed", captions=["日々の継続を重視した、基本的な測定モードです。", "週に一度など、じっくり自分と向き合いたい時に。より深い洞察を得られます。"])
    if 'クイック' in input_mode:
        active_elements = SHORT_ELEMENTS
        mode_string = 'quick'
    else:
        active_elements = LONG_ELEMENTS
        mode_string = 'deep'

    with st.form(key='daily_input_form'):
        st.subheader(f'1. 今日の充足度 (s_t) は？ - {input_mode.split("（")[0]}')
        s_values, s_element_values = {}, {}
        col1, col2 = st.columns(2)
        domain_containers = {'health': col1, 'relationships': col1, 'meaning': col1, 'autonomy': col2, 'finance': col2, 'leisure': col2}
        if not df_data.empty: latest_s_elements = df_data.filter(like='s_element_').iloc[-1]
        else: latest_s_elements = pd.Series(50, index=[f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d])
        
        for domain, container in domain_containers.items():
            with container:
                elements_to_show = active_elements.get(domain, [])
                if elements_to_show:
                    with st.expander(f"**{DOMAIN_NAMES_JP[domain]}** - クリックして詳細入力"):
                        element_scores = []
                        for element in elements_to_show:
                            default_val = int(latest_s_elements.get(f's_element_{element}', 50))
                            # --- 【v0.9.3変更点】help引数に、材料ごとの詳細解説を設定 ---
                            element_help_text = ELEMENT_DEFINITIONS.get(element, "")
                            score = st.slider(element, 0, 100, default_val, key=f"s_element_{element}", help=element_help_text)
                            element_scores.append(score)
                            s_element_values[f's_element_{element}'] = score
                        s_values[domain] = int(np.mean(element_scores))
                        st.metric(label=f"充足度（自動計算）", value=f"{s_values[domain]} 点")
        with col2:
            domain = 'competition'
            elements_to_show = active_elements.get(domain, [])
            if elements_to_show:
                with st.expander(f"**{DOMAIN_NAMES_JP[domain]}** - クリックして詳細入力"):
                    default_val = int(latest_s_elements.get(f's_element_{elements_to_show[0]}', 50))
                    # --- 【v0.9.3変更点】help引数に、材料ごとの詳細解説を設定 ---
                    element_help_text = ELEMENT_DEFINITIONS.get(elements_to_show[0], "")
                    score = st.slider(elements_to_show[0], 0, 100, default_val, key=f"s_element_{elements_to_show[0]}", help=element_help_text)
                    s_values[domain] = score
                    s_element_values[f's_element_{elements_to_show[0]}'] = score
                    st.metric(label=f"充足度", value=f"{s_values[domain]} 点")
        
        st.subheader('2. 総合的な幸福感 (Gt) は？')
        with st.expander("▼ これはなぜ必要？"): st.markdown("...")
        g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
        st.subheader('3. 今日の出来事や気づきは？')
        with st.expander("▼ なぜ書くのがおすすめ？"): st.markdown("...")
        event_log = st.text_area('', height=100, label_visibility="collapsed")
        submitted = st.form_submit_button('今日の記録を保存する')

    # (データ保存、ダッシュボード表示はv0.9.2と同様)
    # ...
    if submitted:
        if q_total != 100: st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
        else:
            q_normalized = {f'q_{d}': v / 100.0 for d, v in q_values.items()}
            s_domain_scores = {f's_{d}': v for d, v in s_values.items()}
            new_record = { 'date': target_date, 'mode': mode_string, **q_normalized, **s_domain_scores, **s_element_values, 'g_happiness': g_happiness, 'event_log': event_log }
            new_df = pd.DataFrame([new_record])
            df_data = df_data[df_data['date'] != target_date]
            df_data = pd.concat([df_data, new_df], ignore_index=True)
            all_element_cols = [f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d]
            all_cols = ['date', 'mode'] + Q_COLS + S_COLS + ['g_happiness', 'event_log'] + all_element_cols
            for col in all_cols:
                if col not in df_data.columns: df_data[col] = np.nan
            df_data = df_data.sort_values(by='date').reset_index(drop=True)
            df_data.to_csv(CSV_FILE, index=False)
            st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を保存（または上書き）しました！')
            st.balloons()
            st.rerun()
    st.header('📊 あなたの航海チャート')
    with st.expander("▼ このチャートの見方"): st.markdown("...")
    if df_data.empty:
        st.info('まだ記録がありません。最初の日誌を記録してみましょう！')
    else:
        df_processed = calculate_metrics(df_data.fillna(0).copy())
        analyze_discrepancy(df_processed)
        st.subheader('調和度 (H) の推移')
        df_processed_chart = df_processed.copy()
        df_processed_chart['date'] = pd.to_datetime(df_processed_chart['date'])
        st.line_chart(df_processed_chart.rename(columns={'H': '調和度 (H)'}), x='date', y='H')
        st.subheader('全記録データ')
        st.dataframe(df_processed.round(2))
        st.caption('このアプリは、あなたの理論「幸福論と言語ゲーム」のMVPです。')

else:
    st.info("👈 サイドバーでログイン、または新規登録をしてください。")
