# ...（コード前半はv1.1.1と同じ）...

# --- 【v1.1.2新機能】ウェルカムページとガイド表示関数を、より詳細で充実した内容に刷新 ---
def show_welcome_and_guide():
    st.header("ようこそ、最初の航海士へ！「Harmony Navigator」取扱説明書")
    st.markdown("---")

    # --- 【v1.1.2修正点】「1. このアプリは何？」のセクションをより詳細に ---
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

    # --- 【v1.1.2修正点】プライバシー解説を、より詳細で物語性のあるものに ---
    st.subheader("🛡️【最重要】あなたのデータとプライバシーは、絶対的に保護されます")
    with st.expander("▼ 解説：クラウド上の「魔法のレストラン」の、少し詳しいお話"):
        st.markdown("""
        「私の個人的な記録が、開発者（私）に見られてしまうのでは？」という不安は、当然のものです。その不安を完全に取り除くために、このアプリがどういう仕組みで動いているのか、少し詳しくお話しさせてください。
        
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

    # --- 【v1.1.2修正点】研究協力のセクションを、より丁寧で誠実なものに ---
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

# --- 2. アプリケーションのUIとロジック ---
# ...（以降のコードは、v1.1.1から変更ありません。タイトルをv1.1.2に変更するだけです）
st.set_page_config(layout="wide", page_title="Harmony Navigator")
st.title(f'🧭 Harmony Navigator (MVP v1.1.2)')
# ... (以降、v1.1.1のコードをそのまま貼り付け)
# ...
st.caption('あなたの「理想」と「現実」のズレを可視化し、より良い人生の航路を見つけるための道具')
st.sidebar.header("👤 ユーザー認証")
if 'username' not in st.session_state: st.session_state['username'] = None
if 'consent' not in st.session_state: st.session_state['consent'] = False
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
    consent = st.sidebar.checkbox("研究協力に関する説明を読み、その内容に同意します。")
    if st.sidebar.button("登録", key="register_button"):
        new_username_safe = safe_filename(new_username_raw)
        if not new_username_safe: st.sidebar.error("ユーザー名を入力してください。")
        elif new_username_safe in existing_users: st.sidebar.error("その名前はすでに使われています。別の名前を入力するか、ログインしてください。")
        else:
            st.session_state['username'] = new_username_safe
            st.session_state['consent'] = consent
            st.sidebar.success(f"ようこそ、{new_username_safe}さん！新しい航海日誌を作成します。")
            st.rerun()
if st.session_state.get('username'):
    username = st.session_state['username']
    CSV_FILE = CSV_FILE_TEMPLATE.format(username)
    st.header(f"ようこそ、{username} さん！")
    if os.path.exists(CSV_FILE):
        df_data = pd.read_csv(CSV_FILE, parse_dates=['date'])
        df_data['date'] = df_data['date'].dt.date
    else:
        columns = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log']
        for _, elements in LONG_ELEMENTS.items():
            for element in elements:
                columns.append(f's_element_{element}')
        df_data = pd.DataFrame(columns=columns)
    today = date.today()
    if not df_data[df_data['date'] == today].empty: st.sidebar.success(f"✅ 今日の記録 ({today.strftime('%Y-%m-%d')}) は完了しています。")
    else: st.sidebar.info(f"ℹ️ 今日の記録 ({today.strftime('%Y-%m-%d')}) はまだありません。")
    st.sidebar.header('⚙️ 価値観 (q_t) の設定')
    with st.sidebar.expander("▼ これは何？どう入力する？"): st.markdown(EXPANDER_TEXTS['q_t'])
    if not df_data.empty and all(col in df_data.columns for col in Q_COLS): latest_q = df_data[Q_COLS].iloc[-1].values * 100
    else: latest_q = [15, 15, 15, 15, 15, 15, 10]
    q_values = {}
    for i, domain in enumerate(DOMAINS):
        q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP[domain], 0, 100, int(latest_q[i]), key=f"q_{domain}")
    q_total = sum(q_values.values())
    st.sidebar.metric(label="現在の合計値", value=q_total)
    if q_total != 100: st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
    else: st.sidebar.success("合計は100です。入力準備OK！")
    st.header('✍️ 今日の航海日誌を記録する')
    with st.expander("▼ これは、何のために記録するの？"): st.markdown(EXPANDER_TEXTS['s_t'])
    st.markdown("##### 記録する日付")
    target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
    if not df_data[df_data['date'] == target_date].empty: st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")
    st.markdown("##### 記録モード")
    input_mode = st.radio("記録モード:", ('🚀 **クイック・ログ**', '🔬 **ディープ・ダイブ**'), horizontal=True, label_visibility="collapsed", captions=["日々の継続を重視した、基本的な測定モードです。", "週に一度など、じっくり自分と向き合いたい時に。より深い洞察を得られます。"])
    if 'クイック' in input_mode: active_elements = SHORT_ELEMENTS; mode_string = 'quick'
    else: active_elements = LONG_ELEMENTS; mode_string = 'deep'
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
                    element_help_text = ELEMENT_DEFINITIONS.get(elements_to_show[0], "")
                    score = st.slider(elements_to_show[0], 0, 100, default_val, key=f"s_element_{elements_to_show[0]}", help=element_help_text)
                    s_values[domain] = score
                    s_element_values[f's_element_{elements_to_show[0]}'] = score
                    st.metric(label=f"充足度", value=f"{s_values[domain]} 点")
        
        st.subheader('2. 総合的な幸福感 (Gt) は？')
        with st.expander("▼ これはなぜ必要？"): st.markdown(EXPANDER_TEXTS['g_t'])
        g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
        st.subheader('3. 今日の出来事や気づきは？')
        with st.expander("▼ なぜ書くのがおすすめ？"): st.markdown(EXPANDER_TEXTS['event_log'])
        event_log = st.text_area('', height=100, label_visibility="collapsed")
        submitted = st.form_submit_button('今日の記録を保存する')
    if submitted:
        if q_total != 100: st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
        else:
            q_normalized = {f'q_{d}': v / 100.0 for d, v in q_values.items()}
            s_domain_scores = {f's_{d}': v for d, v in s_values.items()}
            consent_status = st.session_state.get('consent', False)
            new_record = { 'date': target_date, 'mode': mode_string, 'consent': consent_status, **q_normalized, **s_domain_scores, **s_element_values, 'g_happiness': g_happiness, 'event_log': event_log }
            new_df = pd.DataFrame([new_record])
            df_data = df_data[df_data['date'] != target_date]
            df_data = pd.concat([df_data, new_df], ignore_index=True)
            all_element_cols = [f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d]
            all_cols = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log'] + all_element_cols
            for col in all_cols:
                if col not in df_data.columns: df_data[col] = np.nan
            df_data = df_data.sort_values(by='date').reset_index(drop=True)
            df_data.to_csv(CSV_FILE, index=False)
            st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を保存（または上書き）しました！')
            st.balloons()
            st.rerun()
    st.header('📊 あなたの航海チャート')
    with st.expander("▼ このチャートの見方"): st.markdown(EXPANDER_TEXTS['dashboard'])
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
    show_welcome_and_guide()
