from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.tools.openrouter_config import get_chat_completion
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast
import logging

# ロガーを取得
logger = logging.getLogger('debate_room')


@agent_endpoint("debate_room", "ディベートルーム：強気・弱気の両者の意見を分析し、中立的な投資結論を導く")
def debate_room_agent(state: AgentState):
    """強気派と弱気派の研究員によるディベートを通じてバランスの取れた結論を導き出します。"""
    show_workflow_status("ディベートルーム")
    show_reasoning = state["metadata"]["show_reasoning"]
    logger.info("研究員の意見を分析し、ディベートを開始します...")

    # 研究員の情報を収集（将来の拡張性も考慮し、防御的にチェック）
    researcher_messages = {}
    for msg in state["messages"]:
        if msg is None:
            continue
        if not hasattr(msg, 'name') or msg.name is None:
            continue
        if isinstance(msg.name, str) and msg.name.startswith("researcher_") and msg.name.endswith("_agent"):
            researcher_messages[msg.name] = msg
            logger.debug(f"研究員の情報を収集: {msg.name}")

    # 強気派と弱気派が揃っているか確認
    if "researcher_bull_agent" not in researcher_messages or "researcher_bear_agent" not in researcher_messages:
        logger.error("必要な研究員データが不足しています: researcher_bull_agent または researcher_bear_agent")
        raise ValueError("必要な researcher_bull_agent または researcher_bear_agent のメッセージが見つかりません")

    # 各研究員のデータをパース
    researcher_data = {}
    for name, msg in researcher_messages.items():
        if not hasattr(msg, 'content') or msg.content is None:
            logger.warning(f"研究員 {name} のメッセージ内容が空です")
            continue
        try:
            data = json.loads(msg.content)
            logger.debug(f"{name} の JSON 内容を正常に解析")
        except (json.JSONDecodeError, TypeError):
            try:
                data = ast.literal_eval(msg.content)
                logger.debug(f"{name} の内容を ast.literal_eval で解析")
            except (ValueError, SyntaxError, TypeError):
                logger.warning(f"{name} のメッセージ内容を解析できず、スキップします")
                continue
        researcher_data[name] = data

    if "researcher_bull_agent" not in researcher_data or "researcher_bear_agent" not in researcher_data:
        logger.error("必要な研究員データの解析に失敗しました")
        raise ValueError("必要な researcher_bull_agent または researcher_bear_agent のデータが解析できませんでした")

    bull_thesis = researcher_data["researcher_bull_agent"]
    bear_thesis = researcher_data["researcher_bear_agent"]
    bull_confidence = bull_thesis.get('confidence', 0)
    bear_confidence = bear_thesis.get('confidence', 0)
    logger.info(f"強気派の信頼度: {bull_confidence}、弱気派の信頼度: {bear_confidence}")

    # ディベート内容をまとめる
    debate_summary = []
    debate_summary.append("強気派の主張:")
    for point in bull_thesis.get("thesis_points", []):
        debate_summary.append(f"+ {point}")

    debate_summary.append("\n弱気派の主張:")
    for point in bear_thesis.get("thesis_points", []):
        debate_summary.append(f"- {point}")

    # LLMに渡す全研究員の主張を収集
    all_perspectives = {}
    for name, data in researcher_data.items():
        perspective = data.get("perspective", name.replace("researcher_", "").replace("_agent", ""))
        all_perspectives[perspective] = {
            "confidence": data.get("confidence", 0),
            "thesis_points": data.get("thesis_points", [])
        }

    logger.info(f"{len(all_perspectives)} 人の研究員の意見を LLM に送信する準備中")

    # プロンプト構築
    llm_prompt = """
あなたはプロの金融アナリストです。以下の複数の研究員の主張を読み、中立的な分析を英語で提供してください。

"""
    for perspective, data in all_perspectives.items():
        llm_prompt += f"\n{perspective.upper()} の視点 (信頼度: {data['confidence']}):\n"
        for point in data["thesis_points"]:
            llm_prompt += f"- {point}\n"

    llm_prompt += """
以下の JSON 形式で回答してください:
{
    "analysis": "各主張の優劣を評価した詳細な分析内容を英語で記載",
    "score": 0.5,  // あなたの総合スコア。-1.0（極端な弱気）〜1.0（極端な強気）、0 は中立
    "reasoning": "このスコアを与えた理由を簡潔に記載"
}

必ず英語で、かつ上記すべてのフィールドを含む有効な JSON を返してください。
"""

    llm_response = None
    llm_analysis = None
    llm_score = 0
    try:
        logger.info("LLM に分析依頼を送信中...")
        messages = [
            {"role": "system", "content": "You are a professional financial analyst. Please provide your analysis in English only, not in Chinese or any other language."},
            {"role": "user", "content": llm_prompt}
        ]

        llm_response = log_llm_interaction(state)(
            lambda: get_chat_completion(messages)
        )()

        logger.info("LLM の応答を受信しました")

        if llm_response:
            try:
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    llm_analysis = json.loads(json_str)
                    llm_score = float(llm_analysis.get("score", 0))
                    llm_score = max(min(llm_score, 1.0), -1.0)
                    logger.info(f"LLM の解析スコア: {llm_score}")
                    logger.debug(f"LLM の分析内容（先頭100文字）: {llm_analysis.get('analysis', 'なし')[:100]}...")
            except Exception as e:
                logger.error(f"LLM 応答の解析に失敗: {e}")
                llm_analysis = {"analysis": "LLMの応答を解析できませんでした", "score": 0, "reasoning": "解析エラー"}
    except Exception as e:
        logger.error(f"LLM 呼び出しエラー: {e}")
        llm_analysis = {"analysis": "LLM API 呼び出し失敗", "score": 0, "reasoning": "API エラー"}

    confidence_diff = bull_confidence - bear_confidence
    llm_weight = 0.3
    mixed_confidence_diff = (1 - llm_weight) * confidence_diff + llm_weight * llm_score

    logger.info(f"混合スコアを計算: 原始差={confidence_diff:.4f}, LLM={llm_score:.4f}, 結果={mixed_confidence_diff:.4f}")

    if abs(mixed_confidence_diff) < 0.1:
        final_signal = "neutral"
        reasoning = "両者とも説得力があり、意見は拮抗しています"
        confidence = max(bull_confidence, bear_confidence)
    elif mixed_confidence_diff > 0:
        final_signal = "bullish"
        reasoning = "強気派の主張の方がより説得力があります"
        confidence = bull_confidence
    else:
        final_signal = "bearish"
        reasoning = "弱気派の主張の方がより説得力があります"
        confidence = bear_confidence

    logger.info(f"最終的な投資判断: {final_signal}（信頼度: {confidence}）")

    message_content = {
        "signal": final_signal,
        "confidence": confidence,
        "bull_confidence": bull_confidence,
        "bear_confidence": bear_confidence,
        "confidence_diff": confidence_diff,
        "llm_score": llm_score if llm_analysis else None,
        "llm_analysis": llm_analysis["analysis"] if llm_analysis and "analysis" in llm_analysis else None,
        "llm_reasoning": llm_analysis["reasoning"] if llm_analysis and "reasoning" in llm_analysis else None,
        "mixed_confidence_diff": mixed_confidence_diff,
        "debate_summary": debate_summary,
        "reasoning": reasoning
    }

    message = HumanMessage(
        content=json.dumps(message_content, ensure_ascii=False),
        name="debate_room_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "ディベートルーム")
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("ディベートルーム", "完了")
    logger.info("ディベートルームでの分析が完了しました")
    return {
        "messages": state["messages"] + [message],
        "data": {
            **state["data"],
            "debate_analysis": message_content
        },
        "metadata": state["metadata"],
    }
