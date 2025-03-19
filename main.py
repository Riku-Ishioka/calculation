import streamlit as st
import re
import json
import os
import pandas as pd
import periodictable


# SAVE_FILE = "composition_list.json"


# **組成式リストの読み込み**
# def load_compositions():
#     if os.path.exists(SAVE_FILE):
#         with open(SAVE_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return []


# **組成式リストの保存**
# def save_compositions(composition_list):
#     with open(SAVE_FILE, "w", encoding="utf-8") as f:
#         json.dump(composition_list, f, ensure_ascii=False, indent=2)


# **アプリ起動時に組成式リストをロード**
# if "composition_list" not in st.session_state:
#     st.session_state["composition_list"] = load_compositions()


def get_atomic_weight(element):
    """periodictable ライブラリを使用して元素の原子量を取得"""
    try:
        return periodictable.elements.symbol(element).mass
    except AttributeError:
        return None


def parse_formula(formula):
    """
    組成式（例："Fe0.5O1.5", "H2O", "NaCl", "C6H12O6", "Fe(OH)2", "Al2(SO4)3"）から元素とその係数の辞書を返す。
    例：
      - "Fe0.5O1.5"  -> {"Fe": 0.5, "O": 1.5}
      - "H2O"        -> {"H": 2.0, "O": 1.0}
      - "NaCl"       -> {"Na": 1.0, "Cl": 1.0}
      - "C6H12O6"    -> {"C": 6.0, "H": 12.0, "O": 6.0}
      - "Fe(OH)2"    -> {"Fe": 1.0, "O": 2.0, "H": 2.0}
      - "Al2(SO4)3"  -> {"Al": 2.0, "S": 3.0, "O": 12.0}
    """

    # スタックを使って括弧の処理を行う
    stack = [{}]
    matches = re.findall(r"([A-Z][a-z]?|\d*\.?\d+|\(|\))", formula)

    i = 0
    while i < len(matches):
        token = matches[i]

        if token == "(":
            # 新しい括弧のグループを作る
            stack.append({})
        elif token == ")":
            # 閉じ括弧に続く乗数を取得
            i += 1
            multiplier = 1.0
            if i < len(matches) and re.match(r"\d*\.?\d+", matches[i]):
                multiplier = float(matches[i])

            group = stack.pop()
            for elem, cnt in group.items():
                stack[-1][elem] = stack[-1].get(elem, 0) + cnt * multiplier
        elif re.match(r"[A-Z][a-z]?", token):  # 元素記号
            formatted_elem = token  # 元素記号はそのまま（大文字+小文字）
            count = 1.0  # デフォルト係数

            # 次が数字ならそれを取得
            if i + 1 < len(matches) and re.match(r"\d*\.?\d+", matches[i + 1]):
                count = float(matches[i + 1])
                i += 1  # 数字をスキップ

            stack[-1][formatted_elem] = stack[-1].get(formatted_elem, 0) + count
        i += 1

    return stack[0]


def main():
    st.markdown("## 組成式から元素の量を計算")

    # **1. ユーザーが組成式を入力**
    st.markdown("### 1. 組成式を入力")

    # 組成式の選択または新規入力
    formula = st.text_input("組成式（例：Gd2PdSi3 や Eu1.1Ag4Sb2）", value="")

    # Enterボタン
    if st.button("Enter"):
        try:
            # 組成式を解析
            composition = parse_formula(formula)
            st.session_state["composition"] = composition
            st.success("組成式の解析に成功しました。")

        except Exception as e:
            st.error(f"組成式の解析に失敗しました: {e}")
    # 確認用に現在の保存リストを表示
    # st.write("保存された組成式リスト:", st.session_state["composition_list"])

    # **解析結果の表示**
    if "composition" in st.session_state:
        composition = st.session_state["composition"]
        df_comp = pd.DataFrame(
            {
                "元素": list(composition.keys()),
                "係数": list(composition.values()),
                "原子量": [
                    get_atomic_weight(elem) if get_atomic_weight(elem) else "不明"
                    for elem in composition.keys()
                ],
            }
        )
        df_comp = df_comp.set_index("元素")
        st.table(df_comp)

        # **2. 基準元素を選択し、グラム数を入力**
        st.markdown("### 2. 基準元素の重量を入力")

        selected_elem = st.selectbox("元素を選択してください", list(composition.keys()))
        mass = st.number_input(
            f"{selected_elem} の重量(g)を入力してください",
            min_value=0.0,
            value=1.0,
            step=0.0001,
            format="%.4f",
        )

        if st.button("Calculate"):
            if mass <= 0:
                st.error("有効なグラム数を入力してください")
            else:
                base_weight = get_atomic_weight(selected_elem)
                if base_weight is None:
                    st.error(f"{selected_elem} の原子量情報が取得できません。")
                else:
                    base_mass = base_weight * composition[selected_elem]
                    factor = mass / base_mass

                    # st.markdown("### 計算結果")
                    results = {}
                    for elem, coeff in composition.items():
                        atomic_weight = get_atomic_weight(elem)
                        if atomic_weight:
                            required = atomic_weight * coeff * factor
                            results[elem] = f"{required:.5f}"
                        else:
                            results[elem] = "原子量情報なし"

                    df_results = pd.DataFrame(
                        {
                            "元素": list(results.keys()),
                            "重量(g)": list(results.values()),
                        }
                    )
                    df_results = df_results.set_index("元素")
                    st.table(df_results)


if __name__ == "__main__":
    main()
