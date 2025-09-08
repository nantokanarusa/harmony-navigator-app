import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
import os
from datetime import datetime, date, timedelta
import re
import glob

# --- 0. 定数と基本設定（変更なし） ---
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
SLIDER_HELP_TEXT = "0: 全く当てはまらない\n\n25: あまり当てはまらない\n\n50: どちらとも言えない\n\n75: やや当てはまる\n\n100: 完全に当てはまる"

# --- 1. 計算ロジック・インサイトエンジン関数（v0.9.1から変更なし） ---
# ... (v0.9.1のコード) ...
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
st.title(f'🧭 Harmony Navigator (MVP v0.9.2)')
st.caption('あなたの「理想」と「現実」のズレを可視化し、より良い人生の航路を見つけるための道具')

# --- ユーザー認証 ---
st.sidebar.header("👤 ユーザー認証")
if 'username' not in st.session_state: st.session_state['username'] = None
auth_mode = st.sidebar.radio("モードを選択してください:", ("ログイン", "新規登録"))
existing_users = get_existing_users()
# (v0.9.1の認証ロジック)
# ...
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

    # (データ読み込み)
    if os.path.exists(CSV_FILE):
        df_data = pd.read_csv(CSV_FILE, parse_dates=['date'])
        df_data['date'] = df_data['date'].dt.date
    else:
        columns = ['date', 'mode'] + Q_COLS + S_COLS + ['g_happiness', 'event_log']
        for _, elements in LONG_ELEMENTS.items():
            for element in elements:
                columns.append(f's_element_{element}')
        df_data = pd.DataFrame(columns=columns)
    
    # (今日の記録状況の確認)
    today = date.today()
    if not df_data[df_data['date'] == today].empty: st.sidebar.success(f"✅ 今日の記録 ({today.strftime('%Y-%m-%d')}) は完了しています。")
    else: st.sidebar.info(f"ℹ️ 今日の記録 ({today.strftime('%Y-%m-%d')}) はまだありません。")

    # --- 価値観 (q_t) の設定 ---
    st.sidebar.header('⚙️ 価値観 (q_t) の設定')
    st.sidebar.caption('あなたの「理想のコンパス」です。')
    # --- 【v0.9.2新機能】解説エキスパンダーを追加 ---
    with st.sidebar.expander("▼ これは何？どう入力する？"):
        st.markdown("""
        ここでは、あなたが人生で**何を大切にしたいか（理想＝情報秩序）**を数値で表現します。
        
        合計100点となるよう、各ドメインに重要度を配分してください。この設定が、あなたの現実を評価するための**個人的な『ものさし』**となります。
        
        週に一度など、定期的に見直すのがおすすめです。
        """)
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
    # --- 【v0.9.2新機能】解説エキスパンダーを追加 ---
    with st.expander("▼ これは、何のために記録するの？"):
        st.markdown("""
        ここでは、あなたの**現実の経験（実践秩序）**を記録します。頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を直感的に評価してください。
        
        この記録と、先ほど設定した価値観との**『ズレ』**を見つけることが、自己理解の第一歩です。
        """)
    
    # (日付選択、モード選択はv0.9.1と同様)
    st.markdown("##### 記録する日付")
    target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
    if not df_data[df_data['date'] == target_date].empty: st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")
    st.markdown("##### 記録モード")
    input_mode = st.radio("記録モード:", ('🚀 **クイック・ログ**（日々の記録に）', '🔬 **ディープ・ダイブ**（週一回の詳細分析に）'), horizontal=True, label_visibility="collapsed", captions=["日々の継続を重視した、基本的な測定モードです。", "週に一度など、じっくり自分と向き合いたい時に。より深い洞察を得られます。"])
    if 'クイック' in input_mode:
        active_elements = SHORT_ELEMENTS
        mode_string = 'quick'
    else:
        active_elements = LONG_ELEMENTS
        mode_string = 'deep'

    with st.form(key='daily_input_form'):
        st.subheader(f'1. 今日の充足度 (s_t) は？ - {input_mode.split("（")[0]}')
        # ... (v0.9.1の入力フォームUI) ...
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
                            score = st.slider(element, 0, 100, default_val, key=f"s_element_{element}", help=SLIDER_HELP_TEXT)
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
                    score = st.slider(elements_to_show[0], 0, 100, default_val, key=f"s_element_{elements_to_show[0]}", help=SLIDER_HELP_TEXT)
                    s_values[domain] = score
                    s_element_values[f's_element_{elements_to_show[0]}'] = score
                    st.metric(label=f"充足度", value=f"{s_values[domain]} 点")

        st.subheader('2. 総合的な幸福感 (Gt) は？')
        # --- 【v0.9.2新機能】解説エキスパンダーを追加 ---
        with st.expander("▼ これはなぜ必要？"):
            st.markdown("この項目は、**あなたの直感的な全体評価**です。他の細かい項目の計算結果（H）と、あなたの直感（G）がどれだけ一致しているか、あるいは**ズレているか**を知るための、非常に重要な手がかりとなります。**『計算上は良いはずなのに、なぜか気分が晴れない』**といった、貴重な自己発見のきっかけになります。")
        g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
        
        st.subheader('3. 今日の出来事や気づきは？')
        # --- 【v0.9.2新機能】解説エキスパンダーを追加 ---
        with st.expander("▼ なぜ書くのがおすすめ？"):
            st.markdown("数値だけでは分からない、**幸福度の浮き沈みの『なぜ？』**を解き明かす鍵です。**『誰と会った』『何をした』『何を感じた』**といった具体的な出来事と、グラフの変動を結びつけることで、あなたの幸福のパターンがより鮮明に見えてきます。")
        event_log = st.text_area('', height=100, label_visibility="collapsed")
        
        submitted = st.form_submit_button('今日の記録を保存する')

    # --- データ保存 ---
    if submitted:
        # ... (v0.9.1のデータ保存ロジック) ...
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

    # --- ダッシュボード ---
    st.header('📊 あなたの航海チャート')
    # --- 【v0.9.2新機能】解説エキスパンダーを追加 ---
    with st.expander("▼ このチャートの見方"):
        st.markdown("""
        ここでは、記録されたデータから、あなたの幸福の**パターンと構造**を可視化します。
        - **インサイト・エンジン:** モデルの計算値(H)とあなたの実感(G)のズレから、自己発見のヒントを提示します。
        - **調和度の推移:** あなたの幸福度の時間的な**『物語』**です。グラフの山や谷が、いつ、なぜ起きたのかを探ってみましょう。
        - **全記録データ:** あなたの航海の**『詳細な航海日誌』**です。
        """)
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